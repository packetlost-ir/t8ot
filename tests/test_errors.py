"""Self-check for the global error handler. Run: python tests/test_errors.py"""

import asyncio
from typing import List

from telebot.types import Chat, Message, User

from t8ot import Bot, Context


class FakeTeleBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))
        return text


class FakeApp:
    def __init__(self):
        self.bot = FakeTeleBot()


def make_ctx(user_id: int = 1) -> Context:
    return Context(
        FakeApp(),
        Message(
            message_id=42,
            from_user=User(id=user_id, is_bot=False, first_name="Tester"),
            date=0,
            chat=Chat(id=user_id, type="private"),
            content_type="text",
            options={"text": "hi"},
            json_string="{}",
        ),
    )


def check_on_error_receives_exception() -> None:
    bot = Bot(token="123456:TEST")
    seen: List[Exception] = []

    @bot.on_error
    async def handle_error(exc: Exception, ctx: Context) -> None:
        seen.append(exc)

    async def boom(ctx: Context) -> None:
        raise ValueError("kaboom")

    ctx = make_ctx()
    # _dispatch must swallow the error, not propagate it.
    asyncio.run(bot._dispatch(ctx, boom))
    assert len(seen) == 1, seen
    assert isinstance(seen[0], ValueError), seen
    assert str(seen[0]) == "kaboom"
    print("[ok] on_error is notified and the exception is absorbed")


def check_default_is_safe() -> None:
    bot = Bot(token="123456:TEST")

    async def boom(ctx: Context) -> None:
        raise RuntimeError("unhandled and no handler registered")

    # Without a registered handler the error is still absorbed.
    asyncio.run(bot._dispatch(make_ctx(), boom))
    assert bot.error_handler is None
    print("[ok] errors are absorbed even with no on_error handler")


def check_error_handler_failure_is_contained() -> None:
    bot = Bot(token="123456:TEST")

    @bot.on_error
    async def bad_error_handler(exc: Exception, ctx: Context) -> None:
        raise RuntimeError("the error handler is broken too")

    async def boom(ctx: Context) -> None:
        raise ValueError("original")

    asyncio.run(bot._dispatch(make_ctx(), boom))
    print("[ok] a failing on_error handler does not escape _dispatch")


def main() -> None:
    check_on_error_receives_exception()
    check_default_is_safe()
    check_error_handler_failure_is_contained()
    print("errors self-check OK")


if __name__ == "__main__":
    main()
