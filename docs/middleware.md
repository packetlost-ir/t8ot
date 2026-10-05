# Middleware Pipeline

Middleware wraps every handler invocation — the place for cross-cutting behaviour: auth, logging,
rate limiting, metrics, feature flags.

---

## The contract

```python
import time
from typing import Optional
from t8ot import Context
from t8ot.middleware import BaseMiddleware


class TimingMiddleware(BaseMiddleware):
    async def pre_process(self, ctx: Context) -> bool:
        ctx.extra["start_time"] = time.perf_counter()
        return True                                   # True = continue

    async def post_process(self, ctx: Context, exception: Optional[Exception] = None) -> None:
        elapsed = (time.perf_counter() - ctx.extra["start_time"]) * 1000
        print(f"{ctx.user.id} finished in {elapsed:.2f}ms")
```

| Hook | Signature | When it runs |
|---|---|---|
| `pre_process(ctx) -> bool` | before the handler | Return `False` to **halt** the request |
| `post_process(ctx, exception) -> None` | after the handler | Always runs for middlewares whose `pre_process` was entered — on success, on halt, and on failure |

Middleware can also be synchronous (`def` instead of `async def`) if it does no I/O.

---

## Registering

Order matters — hooks run top-down, and unwinding runs bottom-up:

```python
bot.use(TimingMiddleware())
bot.use(AuthMiddleware())
```

```python
async def execute(ctx: Context, handler: Callable[[Context], Awaitable[None]]) -> None:
    executed = []
    exception = None
    try:
        for mw in self.middlewares:
            if not await mw.pre_process(ctx):
                break
            executed.append(mw)
        else:
            await handler(ctx)
    except Exception as exc:
        exception = exc
    finally:
        for mw in reversed(executed):
            await mw.post_process(ctx, exception=exception)
```

Consequences worth knowing:

- If `pre_process` returns `False`, the handler **never runs** and no later middleware's
  `pre_process` is called.
- `post_process` runs in **reverse** registration order — mirroring the call stack.
- Only middlewares that were actually entered receive `post_process`, so you never have to guard
  against partially-initialised state.
- If a handler raises, the exception is re-raised **after** all `post_process` hooks have run, so
  error handlers see a clean state.
- Middleware wraps commands, callbacks, message handlers, inline handlers **and** active flow
  steps: flow input goes through the same pipeline.

---

## Halting execution

Return `False` from `pre_process` to stop the request:

```python
class AuthMiddleware(BaseMiddleware):
    async def pre_process(self, ctx: Context) -> bool:
        ctx.extra["permissions"] = await load_permissions(ctx.user.id)
        if "reports:write" not in ctx.extra["permissions"]:
            await ctx.reply("You cannot do that.")
            return False
        return True
```

Halting is silent to the rest of the pipeline — no handler, no later pre-hooks. Reply first if the
user needs feedback.

---

## Passing data with `ctx.extra`

`ctx.extra` is a fresh dict per update, created by the context. Middlewares write to it in
`pre_process`, and handlers read it afterwards:

```python
class TenantMiddleware(BaseMiddleware):
    async def pre_process(self, ctx: Context) -> bool:
        ctx.extra["tenant"] = await resolve_tenant(ctx.chat_id)
        return True


class ReportsCommand(BaseCommand):
    name = "reports"

    async def execute(self, ctx: Context) -> None:
        tenant = ctx.extra.get("tenant")
        await ctx.reply(f"Reports for {tenant}")
```

This is the idiomatic way to avoid globals: the scratchpad lives and dies with a single update, so
it is safe under concurrency.

---

## Logging example

```python
import time
from typing import Optional
from t8ot import Context
from t8ot.middleware import BaseMiddleware


class LoggerMiddleware(BaseMiddleware):
    async def pre_process(self, ctx: Context) -> bool:
        ctx.extra["start_time"] = time.perf_counter()
        print(f"-> {ctx.user.id} ({ctx.chat.type if ctx.chat else 'inline'})")
        return True

    async def post_process(self, ctx: Context, exception: Optional[Exception] = None) -> None:
        elapsed = (time.perf_counter() - ctx.extra["start_time"]) * 1000
        if exception:
            print(f"<- {ctx.user.id} failed after {elapsed:.2f}ms: {exception!r}")
        else:
            print(f"<- {ctx.user.id} ok ({elapsed:.2f}ms)")
```

---

## Middleware or guards?

| Use | When |
|---|---|
| **Middleware** | Behaviour that applies to *every* handler (logging, metrics, DB session, rate limits) |
| **Guards** | Per-handler access rules (`@admin_only`, `@group_only`) — see [Guards](guards.md) |

The two compose: guards sit inside the middleware pipeline, so a request blocked by middleware
never reaches a guard, and vice versa.

---

← [FSM & Storage](fsm-and-storage.md) · Next: [Guards](guards.md)