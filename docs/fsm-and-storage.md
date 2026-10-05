# FSM & Storage

The finite state machine turns a list of steps into a conversation: t8ot asks each question,
validates the answer, stores it, and hands the whole result to your flow when the last step
completes.

---

## Defining a flow

```python
from t8ot import Context
from t8ot.fsm import BaseFlow, Step


class RegistrationFlow(BaseFlow):
    name = "register"                                  # key used by start_flow()
    cancel_commands = ["/cancel", "cancel", "exit"]

    def define_steps(self):
        return [
            Step(
                name="name",
                prompt="What is your full name?",
                validator=lambda ctx: len(ctx.text or "") >= 3,
                error_message="At least 3 characters, please.",
            ),
            Step(
                name="phone",
                prompt="Phone number (09121234567):",
                validator=lambda ctx: (ctx.text or "").startswith("09"),
                error_message="That does not look like a phone number.",
            ),
        ]

    async def on_finish(self, ctx: Context, data: dict) -> None:
        await ctx.reply(f"Done! {data}")

    async def on_cancel(self, ctx: Context) -> None:
        await ctx.reply("Registration cancelled.")
```

| Member | Type | Default | Purpose |
|---|---|---|---|
| `name` | `str` | `""` | Flow key; falls back to the class name (`RegistrationFlow` → `registration`) |
| `cancel_commands` | `List[str]` | `["/cancel", "cancel", "لغو"]` | Any message matching one of these aborts the flow (case-insensitive) |
| `define_steps()` | `List[Step]` | — | Required; returns the ordered steps |
| `on_finish(ctx, data)` | — | — | Required; `data` maps step names to collected values |
| `on_cancel(ctx)` | — | default reply | Optional; overrides the default "Process cancelled." |

### `Step`

| Parameter | Type | Default | Purpose |
|---|---|---|---|
| `name` | `str` | — | Key under which the answer is stored in `data` |
| `prompt` | `str` | — | Message sent when the step becomes active |
| `validator` | `Optional[Callable[[Context], bool]]` | `None` | Sync **or** async predicate; returning a falsy value re-asks with `error_message` |
| `error_message` | `str` | `"Invalid input, please try again."` | Shown when validation fails |

```python
Step(name="age", prompt="Your age:", validator=lambda ctx: (ctx.text or "").isdigit())
```

Async validators work too:

```python
async def is_registered(ctx: Context) -> bool:
    return await ctx.app.storage.get_state(ctx.user.id) is not None

Step(name="email", prompt="Email:", validator=is_registered)
```

---

## Running a flow

Start it from any handler:

```python
class StartCommand(BaseCommand):
    name = "start"

    async def execute(self, ctx: Context) -> None:
        await ctx.app.start_flow(ctx, "register")
```

While a flow is active, the engine installs a global interceptor: incoming text, contacts and
locations are routed to the active step instead of your `BaseMessage` handlers. Each answer is
written with `storage.update_data(user_id, **{step.name: value})`, and the state advances from
`register:0` to `register:1`, …

Cancel from anywhere:

```python
await ctx.cancel_flow()     # or let the user type /cancel
```

---

## The storage contract

Progress is persisted through a `BaseStorage` backend. All methods are synchronous:

```python
class BaseStorage(ABC):
    def get_state(self, user_id: int) -> Optional[str]: ...
    def set_state(self, user_id: int, state: str) -> None: ...
    def get_data(self, user_id: int) -> Dict[str, Any]: ...
    def update_data(self, user_id: int, **kwargs) -> None: ...
    def clear(self, user_id: int) -> None: ...
```

Pass one to the `Bot` constructor, or not at all:

```python
from t8ot import Bot, SQLiteStorage

bot = Bot(token=TOKEN)                                  # MemoryStorage by default
bot = Bot(token=TOKEN, storage=SQLiteStorage("bot.db")) # persistent
```

Swapping backends is a one-line change — flow logic never sees the difference.

---

## Backends

### `MemoryStorage` (default)

A plain dictionary. Fastest option, zero setup, and the right choice for tests, local scripts and
single-process bots.

```python
from t8ot import MemoryStorage

bot = Bot(token=TOKEN, storage=MemoryStorage())
```

> **Volatile:** everything is lost when the process restarts, and state is not shared between
> replicas.

### `SQLiteStorage` — local, zero dependencies

Uses Python's bundled `sqlite3`. The table is created on first use:

```sql
CREATE TABLE IF NOT EXISTS fsm_storage (user_id INTEGER PRIMARY KEY, state TEXT, data TEXT)
```

```python
from t8ot import SQLiteStorage

bot = Bot(token=TOKEN, storage=SQLiteStorage("bot.db"))
```

| Property | Value |
|---|---|
| Constructor | `SQLiteStorage(db_path: str = "bot_storage.db")` |
| Storage format | `state` as text, `data` as JSON |
| Thread safety | one connection per operation, committed and closed — safe from the event loop |
| Corrupt payload | falls back to `{}` instead of raising |

Good for single-instance deployments, dev/staging, and bots where losing a few seconds of state
on a crash is unacceptable.

### `RedisStorage` — distributed, multi-instance

Stores state and data under `{prefix}:{user_id}:state` / `{prefix}:{user_id}:data`, with JSON
encoded payloads and optional expiry.

```bash
pip install "t8ot[redis]"
```

```python
from t8ot import RedisStorage

bot = Bot(
    token=TOKEN,
    storage=RedisStorage("redis://localhost:6379/0", prefix="mybot:fsm", ttl=3600),
)
```

| Parameter | Default | Purpose |
|---|---|---|
| `redis_url` | `"redis://localhost:6379/0"` | Any `redis://` URL (TLS, sentinel, cluster URLs included) |
| `prefix` | `"t8ot:fsm"` | Key namespace — set it per bot when sharing one server |
| `ttl` | `None` | Optional expiry in seconds; stale conversations then expire on their own |

`redis` is imported lazily, so only projects that actually instantiate `RedisStorage` need the
package. If it is missing you get an actionable error:

```text
ImportError: RedisStorage requires the 'redis' package. Install it with: pip install redis
```

Use it when you run several replicas behind a load balancer and need shared conversation state.

---

## Writing your own backend

Subclass `BaseStorage` and implement the five methods — useful for Postgres, MongoDB, or tests:

```python
from typing import Any, Dict, Optional
from t8ot import BaseStorage


class NullStorage(BaseStorage):
    """Accepts everything, remembers nothing."""

    def get_state(self, user_id: int) -> Optional[str]:
        return None

    def set_state(self, user_id: int, state: str) -> None:
        pass

    def get_data(self, user_id: int) -> Dict[str, Any]:
        return {}

    def update_data(self, user_id: int, **kwargs) -> None:
        pass

    def clear(self, user_id: int) -> None:
        pass
```

---

← [Context API](context.md) · Next: [Middleware](middleware.md)