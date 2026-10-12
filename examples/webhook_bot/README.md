# Webhook Bot Example

A minimal, production-shaped bot that runs over Telegram's webhook API instead of polling.

```text
webhook_bot/
├── main.py               # reads env vars, boots the aiohttp webhook server
├── commands/
│   ├── start.py          # /start
│   └── echo.py           # /echo hello world  -> uses ctx.args
├── .env.example          # copy to .env and fill in
└── README.md
```

## Configuration

Copy the template and edit it:

```bash
cp .env.example .env
```

| Variable | Required | Example | Notes |
|---|---|---|---|
| `BOT_TOKEN` | yes | `123456:ABC...` | From [@BotFather](https://t.me/BotFather) |
| `WEBHOOK_URL` | yes | `https://bot.example.com/webhook` | Public HTTPS URL; must match `WEBHOOK_PATH` |
| `WEBHOOK_PATH` | no | `/webhook` | Local path served by the app (default `/webhook`) |
| `WEBHOOK_SECRET` | recommended | `a-long-random-string` | Sent by Telegram as `X-Telegram-Bot-Api-Secret-Token`; unset disables the check |
| `HOST` | no | `0.0.0.0` | Bind address (use `127.0.0.1` behind a proxy) |
| `PORT` | no | `8080` | Local port |

Load the variables into your shell, for example:

```bash
set -a && . ./.env && set +a
```

## Run locally (tunnel)

Telegram needs a public HTTPS URL. Forward one to your local port:

```bash
# ngrok
ngrok http 8080
# use the printed https host:
export WEBHOOK_URL=https://<subdomain>.ngrok-free.app/webhook
export WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
python main.py
```

```bash
# or localtunnel
npx localtunnel --port 8080
```

Then message the bot in Telegram: `/start`, `/echo hello world`.

## Run on a VPS

1. Put an HTTPS reverse proxy (Nginx/Caddy) in front and forward to `127.0.0.1:8080`.
2. Set `HOST=127.0.0.1`, `WEBHOOK_URL=https://your-domain/webhook`, and a strong `WEBHOOK_SECRET`.
3. Run under a process manager, e.g. systemd:

```ini
[Unit]
Description=t8ot webhook bot
After=network.target

[Service]
WorkingDirectory=/opt/webhook_bot
EnvironmentFile=/opt/webhook_bot/.env
ExecStart=/opt/webhook_bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Full deployment recipes (Nginx, Caddy, cloud platforms) are in
[`docs/webhook.md`](../../docs/webhook.md).

## Notes

- The secret comparison is constant-time; keep the webhook path unguessable too.
- Handler exceptions are logged and still acknowledged with `200` so Telegram does not retry
  them forever.
