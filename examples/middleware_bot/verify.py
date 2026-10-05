"""Offline verification of the middleware pipeline.

Run it without a Telegram token to confirm hook ordering, halting and
error unwinding:

    python examples/middleware_bot/verify.py
"""

import asyncio
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent))

from t8ot import BaseMiddleware, Bot, Context  # noqa: E402

from middlewares.auth import BANNED_USER_IDS, AuthMiddleware  # noqa: E402
from middlewares.logger import LoggerMiddleware  # noqa: E402

DUMMY_TOKEN = "123456:AAHdummyTOKENforOfflineVerification"


def make_ctx(user_id: int) -> Context:
    """Builds a Context around a stubbed Message event."""
    event = type(
        "Msg",
        (),
        {
            "from_user": type("U", (), {"id": user_id, "first_name": "Tester"})(),
            "chat": type("C", (), {"id": user_id})(),
            "text": "/start",
            "contact": None,
            "location": None,
        },
    )()
    bot = Bot(token=DUMMY_TOKEN)
    return Context(bot, event)


class Tracer(BaseMiddleware):
    """Records every hook invocation into a shared list."""

    def __init__(self, name: str, log: List[str], allow: bool = True):
        self.name = name
        self.log = log
        self.allow = allow

    async def pre_process(self, ctx: Context) -> bool:
        self.log.append(f"pre:{self.name}")
        return self.allow

    async def post_process(self, ctx: Context, exception: Exception = None) -> None:
        self.log.append(f"post:{self.name}:{'err' if exception else 'ok'}")


def check_success_order() -> None:
    log: List[str] = []
    bot = Bot(token=DUMMY_TOKEN)
    bot.use(Tracer("outer", log))
    bot.use(Tracer("inner", log))
    ctx = make_ctx(1)

    async def handler(c: Context) -> None:
        log.append("handler")

    asyncio.run(bot._execute_with_middlewares(ctx, handler))
    assert log == ["pre:outer", "pre:inner", "handler", "post:inner:ok", "post:outer:ok"], log
    print("[ok] hooks run pre-first, post in reverse order")


def check_halt_unwinds() -> None:
    log: List[str] = []
    bot = Bot(token=DUMMY_TOKEN)
    bot.use(Tracer("outer", log))
    bot.use(Tracer("guard", log, allow=False))
    bot.use(Tracer("never", log))

    async def handler(c: Context) -> None:
        log.append("handler")

    asyncio.run(bot._execute_with_middlewares(make_ctx(1), handler))
    assert log == ["pre:outer", "pre:guard", "post:guard:ok", "post:outer:ok"], log
    print("[ok] a False return halts the handler and still unwinds post hooks")


def check_exception_propagates() -> None:
    log: List[str] = []
    bot = Bot(token=DUMMY_TOKEN)
    bot.use(Tracer("outer", log))

    async def handler(c: Context) -> None:
        raise RuntimeError("boom")

    try:
        asyncio.run(bot._execute_with_middlewares(make_ctx(1), handler))
    except RuntimeError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("exception did not propagate")
    assert log == ["pre:outer", "post:outer:err"], log
    print("[ok] handler errors reach post hooks and re-raise")


def check_example_middlewares() -> None:
    bot = Bot(token=DUMMY_TOKEN)
    bot.use(AuthMiddleware())
    bot.use(LoggerMiddleware())

    seen: List[dict] = []

    class StartCommand:
        async def execute(self, ctx: Context) -> None:
            seen.append(dict(ctx.extra))

    allowed, blocked = make_ctx(1), make_ctx(BANNED_USER_IDS[0])
    asyncio.run(bot._execute_with_middlewares(allowed, StartCommand().execute))
    asyncio.run(bot._execute_with_middlewares(blocked, StartCommand().execute))

    assert seen == [{"permissions": ["read", "write"], "start_time": seen[0]["start_time"]}], seen
    assert "permissions" not in allowed.extra, "auth cleanup did not revoke permissions"
    assert seen[0]["start_time"] > 0, "logger did not stamp a start time"
    print("[ok] example middlewares inject into ctx.extra and enforce the ban list")


if __name__ == "__main__":
    check_success_order()
    check_halt_unwinds()
    check_exception_propagates()
    check_example_middlewares()
    print("All middleware pipeline checks passed.")
