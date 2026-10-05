# Routing & Handler Discovery

t8ot has no router table. You describe your bot as a directory tree and call
`bot.load_handlers()` once per tree.

---

## The discovery call

```python
bot.load_handlers("commands")
bot.load_handlers("callbacks")
bot.load_handlers("flows")
```

Each call walks the given directory **recursively**, imports every module it finds, and registers
each handler class defined in those modules.

| Behaviour | Detail |
|---|---|
| Recursion | `rglob("*.py")` — nesting depth is unlimited |
| Skipped files | anything with a `_` or `.` in its path: `__init__.py`, `_helpers.py`, `.cache/x.py`, `__pycache__/` |
| Ordering | deterministic (sorted by path), so startup logs are stable |
| Import errors | warned and skipped — one broken file never kills the loader |
| Name collisions | impossible: the synthetic module name is built from the file's **relative** path, so `commands/admin/stats.py` and `commands/user/stats.py` both load |

A broken handler prints a warning and the rest still register:

```text
[t8ot] Warning: Failed to import 'commands/broken.py': ModuleNotFoundError(...)
[t8ot] Registered command: /start
```

---

## Folder layout

```text
my_bot/
├── main.py
├── commands/
│   ├── start.py                 -> /start
│   ├── admin/
│   │   ├── ban.py               -> /ban
│   │   └── stats.py             -> /admin_stats
│   └── user/
│       ├── profile.py           -> /profile
│       └── stats.py             -> /user_stats   (same filename, no clash)
├── callbacks/
│   └── settings/
│       └── toggle.py            -> pattern "settings:"
└── flows/
    └── onboarding/
        └── main.py              -> flow "onboarding"
```

Deep trees keep working:

```python
bot.load_handlers("commands")  # picks up commands/admin/ban.py and commands/user/profile.py
```

> Register a *tree* (`commands`), not individual files. A single-file path has no children to
> visit, so nested handlers below it are never discovered.

---

## Handler base classes

Every handler is a class with a single `async def execute(self, ctx)`. The loader inspects each
imported module and registers subclasses of the four base classes below.

### `BaseCommand` — slash commands

```python
from t8ot import Context
from t8ot.base import BaseCommand


class StartCommand(BaseCommand):
    name = "start"                       # registered as /start
    description = "Welcome message"      # optional, for your own reference

    async def execute(self, ctx: Context) -> None:
        await ctx.reply(f"Hello, {ctx.user.first_name}!")
```

| Attribute | Type | Default | Purpose |
|---|---|---|---|
| `name` | `str` | `""` | Command name without the slash. Falls back to the class name (`AdminStatsCommand` → `adminstats`) |
| `description` | `Optional[str]` | `None` | Free-form metadata |

`await ctx.app.start_flow(ctx, "flow_name")` starts a registered flow from inside a command.

### `BaseCallback` — inline button presses

```python
from t8ot import Context
from t8ot.base import BaseCallback


class SettingsToggleCallback(BaseCallback):
    pattern = "settings:"      # matches "settings:open", "settings:theme", ...

    async def execute(self, ctx: Context) -> None:
        await ctx.answer(f"Toggled {ctx.data}")
        await ctx.edit_text("Settings updated.")
```

| Attribute | Type | Default | Purpose |
|---|---|---|---|
| `pattern` | `Optional[str]` | `None` | Fires when `data == pattern` **or** `data.startswith(pattern)`; `None` matches every callback |

### `BaseMessage` — plain messages

```python
from t8ot import Context
from t8ot.base import BaseMessage


class ThanksMessage(BaseMessage):
    text_filter = "thanks"                  # exact text match
    content_types = ["text"]                # any telebot content type

    async def execute(self, ctx: Context) -> None:
        await ctx.reply("You're welcome!")
```

| Attribute | Type | Default | Purpose |
|---|---|---|---|
| `text_filter` | `Optional[str]` | `None` | Exact message text; `None` accepts anything of the listed content types |
| `content_types` | `List[str]` | `["text"]` | e.g. `["text", "contact", "location"]` |

> **Flows win:** `BaseMessage` handlers are skipped while the user has an active flow state, so
> conversational flows always receive the message first.

### `BaseInline` — inline mode (`@bot query`)

```python
from t8ot import Context
from t8ot.base import BaseInline


class SearchInline(BaseInline):
    async def execute(self, ctx: Context) -> None:
        await ctx.reply(f"You searched for: {ctx.query}")
```

Inline queries expose the typed text as `ctx.query`.

> **Note:** `BaseInline` declares a `pattern` attribute for API symmetry, but the loader currently
> registers inline handlers for every query. Filter inside `execute` (e.g.
> `if not ctx.query.startswith("/"): return`) until filtering is wired up.

---

## Imports in handler files

Handlers are imported as standalone files, so use absolute imports:

```python
from t8ot import Context                 # framework
from t8ot.base import BaseCommand
from t8ot.fsm import BaseFlow, Step
```

Relative imports (`from .helpers import ...`) do not resolve inside loaded handler files — put
shared code in a normal package and import it by its importable name.

---

## Registration output

Every registration prints a line, which doubles as a startup audit:

```text
[t8ot] Registered command: /start
[t8ot] Registered callback: SettingsToggleCallback (pattern=settings:)
[t8ot] Registered message handler: ThanksMessage
[t8ot] Registered flow: onboarding
```

---

← [Quickstart](quickstart.md) · Next: [Context API](context.md)