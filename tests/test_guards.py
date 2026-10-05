"""Self-check for guard decorators and media helpers. Run: python tests/test_guards.py"""

import asyncio

from telebot.types import Chat, Message, User
from telebot.asyncio_helper import ApiException

from t8ot import Context, admin_only, group_only, private_only


class FakeTeleBot:
    """Records outbound calls instead of hitting Telegram."""

    def __init__(self):
        self.sent = []
        self.deleted = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))
        return text

    async def send_photo(self, chat_id, photo, caption=None, **kwargs):
        self.sent.append((chat_id, "photo", caption))
        return photo

    async def send_document(self, chat_id, document, caption=None, **kwargs):
        self.sent.append((chat_id, "document", caption))
        return document

    async def send_video(self, chat_id, video, caption=None, **kwargs):
        self.sent.append((chat_id, "video", caption))
        return video

    async def delete_message(self, chat_id, message_id):
        self.deleted.append((chat_id, message_id))
        return True

    async def edit_message_text(self, text=None, chat_id=None, message_id=None, **kwargs):
        self.sent.append((chat_id, "edit", text))
        return text


class FakeBot:
    def __init__(self):
        self.bot = FakeTeleBot()


def make_ctx(user_id: int, chat_type: str = "private") -> Context:
    return Context(
        FakeBot(),
        Message(
            message_id=42,
            from_user=User(id=user_id, is_bot=False, first_name="Tester"),
            date=0,
            chat=Chat(id=user_id, type=chat_type),
            content_type="text",
            options={"text": "hi"},
            json_string="{}",
        ),
    )


def check_admin_only() -> None:
    calls = []

    @admin_only([1, 2], on_denied="nope")
    async def handler(ctx: Context) -> None:
        calls.append(ctx.user.id)

    admin_ctx = make_ctx(1)
    guest_ctx = make_ctx(99)
    asyncio.run(handler(admin_ctx))
    asyncio.run(handler(guest_ctx))

    assert calls == [1], calls
    assert admin_ctx.bot.sent == [], admin_ctx.bot.sent
    assert guest_ctx.bot.sent == [(99, "nope")], guest_ctx.bot.sent

    # on_denied=None must silence the reply without letting the handler run.
    @admin_only({1})
    async def silent(ctx: Context) -> None:
        calls.append("should not run")

    muted_ctx = make_ctx(99)
    asyncio.run(silent(muted_ctx))
    assert calls == [1], calls
    assert muted_ctx.bot.sent == [(99, "⛔ Access denied.")], muted_ctx.bot.sent

    # A set of IDs works the same way.
    @admin_only({7}, on_denied=None)
    async def allowed(ctx: Context) -> None:
        calls.append(ctx.user.id)

    asyncio.run(allowed(make_ctx(7)))
    asyncio.run(allowed(make_ctx(8)))  # denied silently
    assert calls == [1, 7], calls
    print("[ok] admin_only allows admins, halts everyone else")


def check_chat_guards() -> None:
    calls = []

    @private_only(on_denied="dm only")
    async def dm(ctx: Context) -> None:
        calls.append(("private", ctx.chat.type))

    @group_only()
    async def group(ctx: Context) -> None:
        calls.append(("group", ctx.chat.type))

    private_ctx = make_ctx(1, "private")
    group_ctx = make_ctx(2, "supergroup")
    plain_group_ctx = make_ctx(3, "group")

    asyncio.run(dm(private_ctx))
    asyncio.run(dm(group_ctx))
    asyncio.run(group(group_ctx))
    asyncio.run(group(private_ctx))
    asyncio.run(group(plain_group_ctx))

    assert calls == [
        ("private", "private"),
        ("group", "supergroup"),
        ("group", "group"),
    ], calls
    assert group_ctx.bot.sent == [(2, "dm only")], group_ctx.bot.sent
    assert private_ctx.bot.sent == [], private_ctx.bot.sent
    print("[ok] private_only / group_only check chat types")


def check_media_helpers() -> None:
    ctx = make_ctx(5)
    asyncio.run(ctx.reply_photo("file_id", caption="pic"))
    asyncio.run(ctx.reply_document("doc.pdf", caption="file"))
    asyncio.run(ctx.reply_video("vid.mp4"))

    assert ctx.bot.sent == [
        (5, "photo", "pic"),
        (5, "document", "file"),
        (5, "video", None),
    ], ctx.bot.sent

    assert asyncio.run(ctx.delete()) is True
    assert ctx.bot.deleted == [(5, 42)], ctx.bot.deleted
    print("[ok] media helpers and delete")


def check_delete_error_is_swallowed() -> None:
    ctx = make_ctx(6)

    async def refuse(chat_id, message_id):
        raise ApiException("message can't be deleted", "delete_message", {"error_code": 400})

    ctx.bot.delete_message = refuse
    assert asyncio.run(ctx.delete()) is False
    print("[ok] telegram delete errors are ignored")


def check_guard_on_handler_method() -> None:
    """Guards must also work on a bound execute(self, ctx) method."""
    from t8ot.base import BaseCommand

    seen = []

    class PanelCommand(BaseCommand):
        name = "panel"

        @admin_only([1], on_denied=None)
        @group_only()
        async def execute(self, ctx: Context) -> None:
            seen.append(ctx.user.id)

    command = PanelCommand()
    asyncio.run(command.execute(make_ctx(1, "supergroup")))  # admin + group: runs
    asyncio.run(command.execute(make_ctx(1, "private")))  # wrong chat type: halted
    asyncio.run(command.execute(make_ctx(2, "supergroup")))  # not an admin: halted
    assert seen == [1], seen
    print("[ok] guards work on handler methods (self binding preserved)")


def main() -> None:
    check_admin_only()
    check_chat_guards()
    check_guard_on_handler_method()
    check_media_helpers()
    check_delete_error_is_swallowed()
    print("guards self-check OK")


if __name__ == "__main__":
    main()