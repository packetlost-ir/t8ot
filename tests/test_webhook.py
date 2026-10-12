"""Self-check for native aiohttp webhook support. Run: python tests/test_webhook.py"""

import asyncio
from typing import Any, Dict, List

from aiohttp.test_utils import TestClient, TestServer

from t8ot import Bot
from t8ot.app import SECRET_TOKEN_HEADER

VALID_UPDATE: Dict[str, Any] = {
    "update_id": 1,
    "message": {
        "message_id": 5,
        "date": 0,
        "chat": {"id": 9, "type": "private"},
        "from": {"id": 9, "is_bot": False, "first_name": "Tester"},
        "text": "hi",
    },
}

SECRET = "sup3r-s3cret"


def make_bot() -> Bot:
    """Builds a Bot whose Telegram network calls are stubbed out."""
    bot = Bot(token="123456:TEST")
    bot.calls: List[Any] = []  # type: ignore[attr-defined]

    async def set_webhook(**kwargs: Any) -> bool:
        bot.calls.append(("set_webhook", kwargs))
        return True

    async def delete_webhook(**kwargs: Any) -> bool:
        bot.calls.append(("delete_webhook", kwargs))
        return True

    async def close_session() -> None:
        bot.calls.append(("close_session",))

    async def process_new_updates(updates: List[Any]) -> None:
        bot.calls.append(("process_new_updates", updates))

    bot.bot.set_webhook = set_webhook  # type: ignore[assignment]
    bot.bot.delete_webhook = delete_webhook  # type: ignore[assignment]
    bot.bot.close_session = close_session  # type: ignore[assignment]
    bot.bot.process_new_updates = process_new_updates  # type: ignore[assignment]
    return bot


async def check_webhook() -> None:
    bot = make_bot()
    app = bot._build_webhook_app(
        webhook_url="https://example.com/hook",
        path="/hook",
        secret_token=SECRET,
        drop_pending_updates=True,
    )

    async with TestClient(TestServer(app)) as client:
        # Startup hook registered the webhook with the expected arguments.
        set_calls = [c for c in bot.calls if c[0] == "set_webhook"]  # type: ignore[attr-defined]
        assert len(set_calls) == 1, bot.calls
        assert set_calls[0][1] == {
            "url": "https://example.com/hook",
            "secret_token": SECRET,
            "drop_pending_updates": True,
        }, set_calls

        # Valid secret + payload -> 200 and dispatched to process_new_updates.
        resp = await client.post(
            "/hook", json=VALID_UPDATE, headers={SECRET_TOKEN_HEADER: SECRET}
        )
        assert resp.status == 200, resp.status
        assert await resp.text() == "OK"

        dispatched = [c for c in bot.calls if c[0] == "process_new_updates"]  # type: ignore[attr-defined]
        assert len(dispatched) == 1, bot.calls
        assert len(dispatched[0][1]) == 1
        assert dispatched[0][1][0].update_id == 1

        # Wrong secret -> 403 and nothing dispatched.
        resp = await client.post(
            "/hook", json=VALID_UPDATE, headers={SECRET_TOKEN_HEADER: "nope"}
        )
        assert resp.status == 403, resp.status
        assert len([c for c in bot.calls if c[0] == "process_new_updates"]) == 1  # type: ignore[attr-defined]

        # Missing secret header -> 403.
        resp = await client.post("/hook", json=VALID_UPDATE)
        assert resp.status == 403, resp.status

        # Malformed JSON -> 400.
        resp = await client.post(
            "/hook",
            data="{not json",
            headers={SECRET_TOKEN_HEADER: SECRET, "Content-Type": "application/json"},
        )
        assert resp.status == 400, resp.status

        # Valid JSON but not a usable update ({} lacks update_id) -> 400.
        resp = await client.post(
            "/hook", json={}, headers={SECRET_TOKEN_HEADER: SECRET}
        )
        assert resp.status == 400, resp.status

    # Cleanup hook ran on shutdown.
    names = [c[0] for c in bot.calls]  # type: ignore[attr-defined]
    assert "delete_webhook" in names, names
    assert "close_session" in names, names
    print("[ok] webhook routing, auth, dispatch and teardown")


async def check_process_error_is_swallowed() -> None:
    bot = make_bot()

    async def boom(updates: List[Any]) -> None:
        raise RuntimeError("handler exploded")

    bot.bot.process_new_updates = boom  # type: ignore[assignment]
    app = bot._build_webhook_app(
        webhook_url="https://example.com/hook",
        path="/hook",
        secret_token=None,
        drop_pending_updates=False,
    )

    async with TestClient(TestServer(app)) as client:
        resp = await client.post("/hook", json=VALID_UPDATE)
        # A failing handler must still be acknowledged with 200.
        assert resp.status == 200, resp.status
    print("[ok] handler errors do not crash the server")


def main() -> None:
    asyncio.run(check_webhook())
    asyncio.run(check_process_error_is_swallowed())
    print("webhook self-check OK")


if __name__ == "__main__":
    main()
