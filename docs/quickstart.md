# Quickstart

Get a bot running in under five minutes.

---

## Requirements

- **Python 3.10 or newer**
- A bot token from [@BotFather](https://t.me/BotFather)

Dependencies (`pyTelegramBotAPI`, `aiohttp`) are installed automatically.

---

## Installation

```bash
pip install t8ot
```

Redis support is an optional extra — install it only if you plan to use `RedisStorage`:

```bash
pip install "t8ot[redis]"
```

Working from source:

```bash
git clone https://github.com/packetlost-ir/t8ot.git
cd t8ot
pip install -e .
```

---

## Bootstrap a project

The CLI scaffolds a runnable bot:

```bash
t8ot init my_bot
cd my_bot
```

```text
my_bot/
├── main.py              # entry point: builds the Bot and loads handlers
├── .env.example         # BOT_TOKEN=your_token_here
├── .gitignore
├── commands/
│   └── start.py         # /start with an inline keyboard
├── callbacks/
└── flows/
```

Nothing is ever overwritten — re-running `t8ot init` reports existing files and skips them.

### Generated entry point (`main.py`)

```python
import os

from t8ot import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN", "123456:YOUR_TOKEN_HERE")

bot = Bot(token=BOT_TOKEN)

# Auto-discovery walks each tree recursively, so you can nest handlers freely.
bot.load_handlers("commands")
bot.load_handlers("callbacks")
bot.load_handlers("flows")

if __name__ == "__main__":
    bot.run()
```

### Generated handler (`commands/start.py`)

```python
from t8ot import Context, InlineKeyboard
from t8ot.base import BaseCommand


class StartCommand(BaseCommand):
    name = "start"
    description = "Welcome message"

    async def execute(self, ctx: Context) -> None:
        keyboard = (
            InlineKeyboard()
            .button("Website", url="https://telegram.org")
            .button("Settings", callback_data="settings:open")
            .build()
        )
        await ctx.reply("Welcome to your t8ot bot!", reply_markup=keyboard)
```

---

## Configure the token

```bash
cp .env.example .env
```

```dotenv
BOT_TOKEN=123456:AAExampleTokenGoesHere
```

```bash
export BOT_TOKEN=123456:AAExampleTokenGoesHere
```

> The token is read by **your** `main.py` via `os.getenv`. t8ot never reads environment
> variables on its own, so you stay in control of configuration.

---

## Run the bot

```bash
python main.py
```

```text
[t8ot] Registered command: /start
[t8ot] Bot is polling...
```

`bot.run()` starts long polling through `AsyncTeleBot`. For webhooks, use the underlying client
directly (`bot.bot`) and skip `run()`.

---

## Add your own handlers

Create a file, subclass a base class, done. The loader finds it recursively:

```bash
t8ot make:command profile      # -> commands/profile.py
t8ot make:callback settings    # -> callbacks/settings.py
t8ot make:flow checkout        # -> flows/checkout.py
```

See the [CLI reference](cli.md) for all generators and their options, and
[Routing](routing.md) for the handler contracts.

---

## Next steps

- [Routing & Handler Discovery](routing.md) — the four handler types and folder conventions
- [Context API](context.md) — everything `ctx` can do
- [FSM & Storage](fsm-and-storage.md) — multi-step flows with persistent state
- [Middleware](middleware.md) / [Guards](guards.md) — cross-cutting behaviour and access control

---

← [Overview](index.md)