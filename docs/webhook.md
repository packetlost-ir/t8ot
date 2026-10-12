# Webhooks in Production

By default `bot.run()` starts **long polling**. In production you usually want **webhooks**: your
process stops asking Telegram for updates and Telegram instead pushes each update to an HTTPS
endpoint you own.

| | Long polling (`run`) | Webhook (`run_webhook`) |
|---|---|---|
| Who initiates | Your process polls Telegram | Telegram POSTs to your server |
| Public HTTPS URL | Not required | **Required** |
| Latency | Poll interval | Immediate |
| Resources | Holds a long-lived poll loop | Passively waits for requests |
| Best for | Local development | VPS, containers, serverless-ish deployments |

Both modes run the **exact same** handler pipeline — file-based routing, middleware, guards, FSM.
Only the transport changes.

---

## `Bot.run_webhook(...)`

```python
async def run_webhook(
    self,
    webhook_url: str,
    host: str = "0.0.0.0",
    port: int = 8080,
    path: Optional[str] = None,
    secret_token: Optional[str] = None,
    drop_pending_updates: bool = False,
) -> None:
```

| Parameter | Default | Meaning |
|---|---|---|
| `webhook_url` | — | **Public** HTTPS URL Telegram should call (must match `path`) |
| `host` | `"0.0.0.0"` | Interface the local aiohttp server binds to |
| `port` | `8080` | Local TCP port |
| `path` | `/{token}` | URL path served by the app. Defaults to the bot token, which is already secret |
| `secret_token` | `None` | When set, Telegram echoes it in `X-Telegram-Bot-Api-Secret-Token`; requests without a match get `403` |
| `drop_pending_updates` | `False` | Discard updates Telegram queued before the webhook was registered |

The method is a coroutine and blocks until cancelled. Run it from an async entry point:

```python
import asyncio
from t8ot import Bot

bot = Bot(token="123456:YOUR_TOKEN")

async def main() -> None:
    await bot.run_webhook("https://bot.example.com/webhook", path="/webhook")

if __name__ == "__main__":
    asyncio.run(main())
```

### Lifecycle

1. **Startup** — registers the webhook with Telegram via `set_webhook(...)`, then starts an
   `aiohttp` `TCPSite`.
2. **Per update** — validates the secret header, parses the JSON body into a `telebot` `Update`,
   and feeds it to `process_new_updates(...)` (the same pipeline as polling).
3. **Shutdown** (on cancellation) — calls `delete_webhook()` and closes the underlying aiohttp
   client session.

Info logs are emitted when the server starts and stops.

> `aiohttp` is already a core dependency, so webhooks add **zero** new packages.

---

## Security model

Webhooks expose a public endpoint, so authenticity matters. Two layers are used:

1. **Secret URL path.** The default path embeds the bot token (`/{token}`), which only you and
   Telegram know. Treat the path as a secret.
2. **Secret token header.** When `secret_token` is supplied, every request must carry a matching
   `X-Telegram-Bot-Api-Secret-Token` header. The comparison is **constant-time**
   (`hmac.compare_digest`), so it cannot be brute-forced by timing. Missing or mismatched headers
   receive `HTTP 403 Forbidden` before any parsing happens.

```python
await bot.run_webhook(
    webhook_url="https://bot.example.com/tg-hook",
    path="/tg-hook",
    secret_token="a-long-random-string",   # Telegram must send this back
)
```

Telegram requires the secret token to be 1–256 characters of `A-Z`, `a-z`, `0-9`, `_` and `-`.

Additional hardening:

- Always terminate TLS at your reverse proxy and expose port `443` only.
- Keep the webhook path unguessable; do not reuse it across deployments.
- Only Telegram's IP ranges (see `https://core.telegram.org/bots/webhooks`) should reach the
  endpoint — restrict at the firewall or proxy if possible.

---

## Configuration via environment variables

Production deployments should not hard-code secrets. Read them with `os.getenv` and ship a
`.env.example` template:

```python
import asyncio
import os

from t8ot import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN", "123456:YOUR_TOKEN_HERE")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://example.com/webhook")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")          # None disables header checks
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

bot = Bot(token=BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(
        bot.run_webhook(
            webhook_url=WEBHOOK_URL,
            host=HOST,
            port=PORT,
            path=WEBHOOK_PATH,
            secret_token=WEBHOOK_SECRET,
        )
    )
```

A complete version lives in [`examples/webhook_bot/`](../examples/webhook_bot/).

---

## Deployment recipes

### Behind Nginx

```nginx
server {
    listen 443 ssl;
    server_name bot.example.com;

    ssl_certificate     /etc/letsencrypt/live/bot.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bot.example.com/privkey.pem;

    location /webhook {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Run the bot bound to localhost so only the proxy can reach it:

```bash
HOST=127.0.0.1 PORT=8080 python main.py
```

### Behind Caddy

Caddy handles TLS automatically:

```caddyfile
bot.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

Then point `WEBHOOK_URL` at `https://bot.example.com/webhook`.

### Cloud platforms

- **Render / Railway / Fly.io** — set the service port to `$PORT`, deploy with
  `python main.py`, and set `WEBHOOK_URL` to the platform's HTTPS hostname plus `/webhook`.
- **Docker** — run `EXPOSE 8080`; pass configuration through environment variables; put the
  container behind your TLS terminator.
- The platform must route `POST` requests to your process; polling is not needed.

### Local development with a tunnel

Telegram needs a public HTTPS URL during development too. Tunnels forward to your local port:

```bash
# ngrok
ngrok http 8080
# then use the printed https URL, e.g.
WEBHOOK_URL=https://<subdomain>.ngrok-free.app/webhook python main.py

# or localtunnel
npx localtunnel --port 8080
```

Remember: `path` and the path inside `webhook_url` must match.

---

## Behavior guarantees

- A malformed or empty JSON body returns `HTTP 400 Bad Request`.
- A JSON body that is not a usable `Update` returns `HTTP 400`.
- If a **handler raises**, the error is logged and the request still returns `HTTP 200 OK`. This
  is deliberate: a non-2xx response makes Telegram retry the same update forever. Handler
  failures should be handled (or logged) inside the handler.

---

← [CLI](cli.md) · Back to [Overview](index.md)
