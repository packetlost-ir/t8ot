# t8ot

![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Framework](https://img.shields.io/badge/built%20on-pyTelegramBotAPI-blue.svg)
![Docs](https://img.shields.io/badge/docs-in%20docs%2F-informational.svg)

**A modern, ergonomic micro-framework for Telegram bots** — built on top of
[pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) (`telebot`) with file-based
routing, a unified context, conversational FSM flows, pluggable storage, middlewares, access
guards and a project scaffolder.

No router tables. No decorators to learn before your first handler. Write a class, drop the file
in a folder, and the framework registers it.

---

## Key Features

| | |
|---|---|
| 🗂 **File-Based Routing** | Drop handler files into `commands/`, `callbacks/`, `flows/` — discovery is recursive, so `commands/admin/ban.py` is found automatically. Private files (`_x.py`) and `__init__.py` are skipped, and a broken file warns instead of killing the loader. |
| 🧩 **Unified Context (`ctx`)** | `Message`, `CallbackQuery` and `InlineQuery` normalized into one interface: `ctx.user`, `ctx.chat`, `ctx.text`, `ctx.value`, plus `reply`, `edit_text`, `delete`, `reply_photo`, `reply_document`, `reply_video`. |
| 🔁 **Conversational FSM** | Multi-step flows declared as data (`Step` objects) with validation, cancel keywords and per-step storage. |
| 💾 **Pluggable Storage** | `MemoryStorage` (default), `SQLiteStorage` (stdlib, persistent), `RedisStorage` (distributed, optional extra). One line to swap. |
| 🎹 **Fluent Keyboards** | Chainable `InlineKeyboard` / `ReplyKeyboard` builders with `adjust(n)` auto-balancing. |
| 🧱 **Middleware** | `pre_process` / `post_process` hooks around every handler, with `ctx.extra` as a per-update scratchpad and the ability to halt requests. |
| 🔐 **Guards** | `@admin_only([...])`, `@private_only()`, `@group_only()` decorators for access control. |
| 🛠 **CLI** | `t8ot init my_bot` plus `make:command` / `make:callback` / `make:flow` generators. |
| ⚡ **Async Native** | Built on `AsyncTeleBot`; every handler is a plain `async def execute(self, ctx)`. |

---

## Quick Example

```python
from t8ot import Context, InlineKeyboard
from t8ot.base import BaseCommand


class StartCommand(BaseCommand):
    name = "start"

    async def execute(self, ctx: Context) -> None:
        keyboard = (
            InlineKeyboard()
            .button("Website", url="https://example.com")
            .button("Settings", callback_data="settings:open")
            .build()
        )
        await ctx.reply(f"Hello {ctx.user.first_name}!", reply_markup=keyboard)
```

```python
# main.py
import os
from t8ot import Bot

bot = Bot(token=os.getenv("BOT_TOKEN", "123456:YOUR_TOKEN_HERE"))
bot.load_handlers("commands")
bot.load_handlers("callbacks")
bot.load_handlers("flows")

if __name__ == "__main__":
    bot.run()
```

```text
commands/start.py  ->  /start
callbacks/         ->  inline button handlers
flows/             ->  multi-step conversations
```

---

## Project Layout

```text
my_bot/
├── main.py                  # Bot instance + load_handlers() calls
├── commands/                # Slash commands (nested folders welcome)
│   └── start.py
├── callbacks/               # Inline keyboard query handlers
│   └── menu_actions.py
└── flows/                   # Multi-step conversational wizards (FSM)
    └── register.py
```

---

## Installation

```bash
pip install t8ot            # from PyPI
pip install "t8ot[redis]"   # + RedisStorage support

# or from source
git clone https://github.com/packetlost-ir/t8ot.git
cd t8ot && pip install -e .
```

Scaffold a project and run it:

```bash
t8ot init my_bot
cd my_bot && python main.py
```

---

## 📚 Documentation

| Guide | What it covers |
|---|---|
| [Overview & Architecture](docs/index.md) | Philosophy, the five moving parts, design rules |
| [Quickstart](docs/quickstart.md) | Requirements, installation, `t8ot init`, first run |
| [Routing & Handler Discovery](docs/routing.md) | File conventions, nested trees, `BaseCommand` / `BaseCallback` / `BaseMessage` / `BaseInline` |
| [Context API & Responses](docs/context.md) | Event data, messaging & media helpers, keyboard builders |
| [FSM & Storage](docs/fsm-and-storage.md) | `BaseFlow`, `Step`, validation, memory / SQLite / Redis backends |
| [Middleware Pipeline](docs/middleware.md) | Pre/post hooks, halting, `ctx.extra` |
| [Guards](docs/guards.md) | `@admin_only`, `@private_only`, `@group_only` |
| [CLI](docs/cli.md) | `t8ot init` and the `make:*` generators |

---

## Modules

- **`t8ot.base`** — handler contracts: `BaseCommand`, `BaseCallback`, `BaseMessage`, `BaseInline`
- **`t8ot.fsm`** — `BaseFlow`, `Step` and the storage backends
- **`t8ot.middleware`** — `BaseMiddleware` pipeline hooks
- **`t8ot.guards`** — `admin_only`, `private_only`, `group_only`
- **`t8ot.types`** — `InlineKeyboard`, `ReplyKeyboard`, `remove_keyboard`
- **`t8ot.context`** — the `Context` object handed to every handler
- **`t8ot.cli`** — the `t8ot` console script

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "feat: add new capability"`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

Released under the [MIT License](LICENSE).