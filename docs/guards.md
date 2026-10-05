# Guards

Guards are decorators that decide whether a handler is allowed to run. They wrap the handler, so
the denied path never reaches your business logic.

```python
from t8ot import Context, admin_only
from t8ot.base import BaseCommand


class StatsCommand(BaseCommand):
    name = "stats"

    @admin_only([123456, 654321])
    async def execute(self, ctx: Context) -> None:
        await ctx.reply("📊 Admin Dashboard")
```

A non-admin sending `/stats` gets `⛔ Access denied.` and the handler body never runs.

---

## `@admin_only(...)`

```python
def admin_only(
    admin_ids: Union[List[int], Set[int]],
    on_denied: Optional[str] = "⛔ Access denied.",
) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
    ...  # returns the decorator
```

| Parameter | Default | Purpose |
|---|---|---|
| `admin_ids` | — | Telegram user IDs allowed through. Lists and sets both work (converted to a set once, at decoration time) |
| `on_denied` | `"⛔ Access denied."` | Reply sent to the user. Pass `None` to fail silently |

Read IDs from the environment so they are not hard-coded:

```python
import os

ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x}

class BroadcastCommand(BaseCommand):
    name = "broadcast"

    @admin_only(ADMIN_IDS, on_denied=None)
    async def execute(self, ctx: Context) -> None:
        await ctx.reply("Broadcast sent.")
```

---

## `@private_only(...)`

```python
def private_only(
    on_denied: Optional[str] = None,
) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
    ...  # returns the decorator
```

Runs only when `ctx.chat.type == "private"`. With the default `on_denied=None` the request is
dropped silently — useful for handlers that should simply not exist in groups.

```python
class DmCommand(BaseCommand):
    name = "notes"

    @private_only()
    async def execute(self, ctx: Context) -> None:
        await ctx.reply("This command only works in direct messages.")
```

Set a message when you want feedback:

```python
class NotesCommand(BaseCommand):
    name = "notes"

    @private_only(on_denied="Please open our direct chat to use this.")
    async def execute(self, ctx: Context) -> None:
        await ctx.reply("Your notes are private.")
```

---

## `@group_only(...)`

```python
def group_only(
    on_denied: Optional[str] = None,
) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
    ...  # returns the decorator
```

Runs only for `group` and `supergroup` chats.

```python
class BanCommand(BaseCommand):
    name = "ban"

    @admin_only([123456]) @group_only()
    async def execute(self, ctx: Context) -> None:
        await ctx.reply(f"Moderating {ctx.chat.title}")
```

---

## Combining guards

Stack decorators — the first one listed is the outermost, so it runs first:

```python
class PanelCommand(BaseCommand):
    name = "panel"

    @admin_only([123456])
    @group_only()
    async def execute(self, ctx: Context) -> None:
        await ctx.reply("Admin panel")
```

- Not an admin → halted by `admin_only`, nothing else is evaluated.
- Admin in a private chat → halted by `group_only`.
- Admin in a group → handler runs.

Works identically on callbacks:

```python
class SettingsCallback(BaseCallback):
    pattern = "settings:"

    @admin_only(ADMIN_IDS)
    async def execute(self, ctx: Context) -> None:
        await ctx.answer("Settings updated.")
```

And on message handlers:

```python
class RawLogMessage(BaseMessage):
    text_filter = "/log"

    @private_only()
    async def execute(self, ctx: Context) -> None:
        await ctx.reply(ctx.text)
```

---

## How it works

Guards wrap the decorated function and short-circuit before delegating:

```python
if ctx.user.id not in allowed:
    if on_denied:
        await ctx.reply(on_denied)
    return          # handler never invoked
await func(*args, **kwargs)
```

Two details worth knowing:

- **Method binding is preserved.** The wrapper forwards every argument it received, so guards work
  on `execute(self, ctx)` methods as well as on plain functions — `functools.wraps` keeps
  `__name__` and the docstring intact.
- **`ctx.chat` may be `None`** (inline queries). Chat-type guards treat that as "not allowed", so
  an inline query can never slip past `@private_only`.

---

## Guards or middleware?

| Use | When |
|---|---|
| **Guards** | One-off rules attached to a single handler |
| **Middleware** | Rules that must apply to every handler — see [Middleware](middleware.md) |

Both run inside the same pipeline, so they compose without extra glue.

---

← [Middleware](middleware.md) · Next: [CLI](cli.md)