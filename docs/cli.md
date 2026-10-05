# CLI

`t8ot` ships a command-line scaffolder so you never copy-paste a handler template again.

```bash
t8ot --help
```

```text
usage: t8ot [-h] {init,make:command,make:callback,make:flow} ...

t8ot CLI tool for Telegram bot scaffolding

positional arguments:
  {init,make:command,make:callback,make:flow}
    init                Create a new bot project scaffold
    make:command        Generate a command handler
    make:callback       Generate a callback handler
    make:flow           Generate a multi-step flow

options:
  -h, --help            show this help message and exit
```

The CLI is built on `argparse` and the standard library only — no extra dependencies.

---

## `t8ot init <project_name>`

Creates a runnable project.

```bash
t8ot init my_bot
```

```text
[t8ot] Created my_bot/.env.example
[t8ot] Created my_bot/.gitignore
[t8ot] Created my_bot/main.py
[t8ot] Created my_bot/commands/start.py
[t8ot] Project ready: /home/you/my_bot
[t8ot] Next: cp .env.example .env  ->  add handlers  ->  python main.py
```

What you get:

| Path | Contents |
|---|---|
| `main.py` | `Bot(token=...)` plus `load_handlers()` for `commands`, `callbacks` and `flows` |
| `commands/start.py` | `/start` command with an `InlineKeyboard` |
| `callbacks/`, `flows/` | Empty directories, ready for generated handlers |
| `.env.example` | `BOT_TOKEN=your_token_here` |
| `.gitignore` | Ignores `.env`, `__pycache__/`, `*.pyc`, `*.db` |

**Never overwrites.** Re-running `init` on an existing folder reports and skips what is already
there:

```text
[t8ot] Skipped (already exists): my_bot/main.py
```

---

## `t8ot make:command <name> [--dir DIR]`

```bash
t8ot make:command profile
```

```text
[t8ot] Created commands/profile.py
```

| Option | Default | Purpose |
|---|---|---|
| `--dir DIR` | `commands` | Target directory (created if missing) |

Generates:

```python
from t8ot import Context
from t8ot.base import BaseCommand


class ProfileCommand(BaseCommand):
    """Handles /profile."""

    name = "profile"
    description = "TODO: describe /profile"

    async def execute(self, ctx: Context) -> None:
        await ctx.reply("TODO: handle /profile")
```

The command name is the argument verbatim, so `t8ot make:command admin_ban` registers `/admin_ban`.

---

## `t8ot make:flow <name> [--dir DIR]`

```bash
t8ot make:flow checkout
```

```text
[t8ot] Created flows/checkout.py
```

| Option | Default | Purpose |
|---|---|---|
| `--dir DIR` | `flows` | Target directory |

Generates a flow with two steps and an example validator:

```python
from t8ot import Context
from t8ot.fsm import BaseFlow, Step


def is_number(ctx: Context) -> bool:
    """Example validator: rejects anything that is not a plain number."""
    return bool(ctx.text and ctx.text.strip().lstrip("-").isdigit())


class CheckoutFlow(BaseFlow):
    """Two-step checkout flow."""

    name = "checkout"

    def define_steps(self):
        return [
            Step(
                name="amount",
                prompt="How much? (send /cancel to stop)",
                validator=is_number,
                error_message="That is not a number. Try again:",
            ),
            Step(
                name="reason",
                prompt="Why?",
            ),
        ]

    async def on_finish(self, ctx: Context, data: dict):
        await ctx.reply(f"Done! Collected: {data}")
```

---

## `t8ot make:callback <name> [--pattern PATTERN] [--dir DIR]`

```bash
t8ot make:callback settings
t8ot make:callback theme --pattern "theme:"
```

```text
[t8ot] Created callbacks/settings.py
[t8ot] Created callbacks/theme.py
```

| Option | Default | Purpose |
|---|---|---|
| `--pattern PATTERN` | `<name>:` | Callback data prefix the handler matches |
| `--dir DIR` | `callbacks` | Target directory |

Generates:

```python
from t8ot import Context
from t8ot.base import BaseCallback


class SettingsCallback(BaseCallback):
    """Handles callback data starting with "settings:"."""

    pattern = "settings:"

    async def execute(self, ctx: Context) -> None:
        await ctx.answer("TODO: handle settings:")
```

---

## Naming rules

Handler names become Python identifiers, file names and Telegram command names, so they are
validated. A name must start with a letter and may contain letters, digits, `-` and `_`:

```bash
t8ot make:command 9lives
```

```text
t8ot: error: invalid name '9lives': start with a letter, then use letters, digits, '-' or '_'
```

This also rules out path traversal (`../escape`). Dashes and underscores are normalized into the
class name — `user-profile` produces `UserProfileCommand`, `user_profile` produces
`UserProfileCommand` too.

---

## Typical workflow

```bash
t8ot init my_bot
cd my_bot                 # generators are relative to the current directory

t8ot make:command start
t8ot make:callback settings
t8ot make:flow register

# nested trees work exactly the same way
mkdir -p commands/admin flows/onboarding
t8ot make:command ban --dir commands/admin
t8ot make:flow welcome --dir flows/onboarding

export BOT_TOKEN=123456:AAExampleToken
python main.py
```

---

← [Guards](guards.md) · Back to [Overview](index.md)