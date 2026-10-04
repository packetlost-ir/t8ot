# t8ot

A modern, ergonomic micro-framework built on top of **pyTelegramBotAPI (`telebot`)** designed for building clean, scalable, and modular Telegram bots with file-based routing and built-in FSM.

---

## Key Features

- **File-Based Routing:** Drop handler files into folders (`commands/`, `callbacks/`, `flows/`) and let `t8ot` auto-discover and register them dynamically.
- **Unified Context (`ctx`):** Single, cohesive interface wrapping incoming updates with built-in shortcuts (`ctx.reply`, `ctx.edit`, `ctx.answer`, `ctx.value`).
- **Conversational Flows (FSM):** Multi-step interactive flows with input validation, step-by-step state management, and cancellation support.
- **Fluent Keyboard Builders:** Chainable API for constructing multi-row `InlineKeyboardMarkup` and `ReplyKeyboardMarkup` with layout auto-balancing (`.adjust()`).
- **Asynchronous Architecture:** Native async/await support powered by `AsyncTeleBot`.

---

## Architecture Overview

A typical `t8ot` project follows a clean separation of concerns:

```text
my_bot/
├── main.py                  # Bot entry point & loader configuration
├── commands/                # Slash commands (/start, /help, etc.)
│   └── start.py
├── callbacks/               # Inline keyboard query handlers
│   └── menu_actions.py
└── flows/                   # Multi-step conversational wizards (FSM)
    └── register.py

```

---

## Installation

Install in editable mode during development:

```bash
git clone https://github.com/packetlost-ir/t8ot.git
cd t8ot
pip install -e .

```

Or install dependencies directly:

```bash
pip install -r requirements.txt 
# or
pip install pyTelegramBotAPI aiohttp

```

---

## Quick Start

### 1. Define a Command (`commands/start.py`)

```python
from t8ot.base import BaseCommand
from t8ot import Context

class StartCommand(BaseCommand):
    name = "start"

    async def execute(self, ctx: Context) -> None:
        user_name = ctx.user.first_name if ctx.user else "there"
        await ctx.reply(f"Hello, <b>{user_name}</b>! Welcome to t8ot.")

```

### 2. Define a Multi-Step Flow (`flows/register.py`)

```python
import re
from t8ot.fsm import BaseFlow, Step
from t8ot import Context

def validate_phone(ctx: Context) -> bool:
    return bool(re.match(r"^09\d{9}$", ctx.text or ""))

class RegistrationFlow(BaseFlow):
    name = "register"
    cancel_commands = ["/cancel", "cancel", "exit"]

    def define_steps(self):
        return [
            Step(
                name="name",
                prompt="Please enter your full name:",
                validator=lambda ctx: len(ctx.text or "") >= 3,
                error_message="Name must be at least 3 characters. Try again:",
            ),
            Step(
                name="phone",
                prompt="Please enter your mobile phone number:",
                validator=validate_phone,
                error_message="Invalid phone number. Try again (or /cancel):",
            ),
        ]

    async def on_finish(self, ctx: Context, data: dict):
        await ctx.reply(f"Registration complete!\nName: {data['name']}\nPhone: {data['phone']}")

    async def on_cancel(self, ctx: Context):
        await ctx.reply("Registration cancelled.")

```

### 3. Build Keyboards Fluently

```python
from t8ot import InlineKeyboard, ReplyKeyboard

# Inline Keyboard with auto-grid (2 columns)
inline_kb = (
    InlineKeyboard()
    .button("Profile", callback_data="action:profile")
    .button("Settings", callback_data="action:settings")
    .button("Support", callback_data="action:support")
    .button("Website", url="[https://github.com](https://github.com)")
    .adjust(2)
    .build()
)

# Reply Keyboard requesting metadata
reply_kb = (
    ReplyKeyboard(placeholder="Select an option...")
    .button("Share Contact", request_contact=True)
    .button("Share Location", request_location=True)
    .row()
    .button("Cancel")
    .build()
)

```

### 4. Run the Application (`main.py`)

```python
import os
from t8ot import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

bot = Bot(token=BOT_TOKEN)

# Auto-discover handlers across project directories
bot.load_handlers("commands")
bot.load_handlers("callbacks")
bot.load_handlers("flows")

if __name__ == "__main__":
    bot.run()

```

---

## Modules & Extensibility

* **`t8ot.base`**: Abstract base classes (`BaseCommand`, `BaseCallback`, `BaseMessage`, `BaseInline`) enforcing standard handler contracts.
* **`t8ot.fsm`**: State persistence (`MemoryStorage`) and sequential conversational pipelines (`BaseFlow`, `Step`).
* **`t8ot.types`**: Declarative keyboard utilities (`InlineKeyboard`, `ReplyKeyboard`, `remove_keyboard`).
* **`t8ot.context`**: Normalizes `Message`, `CallbackQuery`, and `InlineQuery` payloads into a predictable interface.

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "feat: add new capability"`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the [MIT License](https://www.google.com/search?q=LICENSE).
