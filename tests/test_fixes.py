"""Self-check for flow naming, callback routing and ctx.args. Run: python tests/test_fixes.py"""

from types import SimpleNamespace
from typing import Optional

from telebot.types import Chat, Message, User

from t8ot import Context
from t8ot.app import _build_callback_filter, _default_flow_name


class FakeTeleBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))
        return text


class FakeBot:
    def __init__(self):
        self.bot = FakeTeleBot()


def make_ctx(user_id: int = 1, text: Optional[str] = "hi") -> Context:
    message = Message(
        message_id=42,
        from_user=User(id=user_id, is_bot=False, first_name="Tester"),
        date=0,
        chat=Chat(id=user_id, type="private"),
        content_type="text",
        options={"text": text} if text is not None else {},
        json_string="{}",
    )
    return Context(FakeBot(), message)


def check_flow_fallback_names() -> None:
    class FlowchartFlow:
        pass

    class WorkflowFlow:
        pass

    class OnboardingFlow:
        pass

    class Flow:
        pass

    class flow:
        pass

    assert _default_flow_name(FlowchartFlow) == "flowchart"
    assert _default_flow_name(WorkflowFlow) == "workflow"
    assert _default_flow_name(OnboardingFlow) == "onboarding"
    # Stripping must not leave an empty name behind.
    assert _default_flow_name(Flow) == "flow"
    assert _default_flow_name(flow) == "flow"
    print("[ok] flow fallback names strip only a trailing 'Flow'")


def check_callback_filter() -> None:
    call_user = SimpleNamespace(data="user")
    call_user_settings = SimpleNamespace(data="user_settings")
    call_settings = SimpleNamespace(data="settings:x")
    call_none = SimpleNamespace(data=None)

    exact = _build_callback_filter("user")
    assert exact(call_user) is True
    assert exact(call_user_settings) is False  # no broad prefix cross-talk

    prefix_colon = _build_callback_filter("settings:")
    assert prefix_colon(call_settings) is True
    assert prefix_colon(call_user) is False

    wildcard = _build_callback_filter("u*")
    assert wildcard(call_user) is True
    assert wildcard(call_user_settings) is True
    assert wildcard(call_settings) is False

    catch_all = _build_callback_filter(None)
    assert catch_all(call_none) is True

    # A None payload never raises under any pattern.
    assert exact(call_none) is False
    assert prefix_colon(call_none) is False
    print("[ok] callback patterns route exact vs prefix without cross-talk")


def check_ctx_args() -> None:
    ctx = make_ctx(text="/ban 12345 spam")
    assert ctx.args == ["12345", "spam"], ctx.args

    bare = make_ctx(text="/start")
    assert bare.args == [], bare.args

    spaced = make_ctx(text="/add   a   b  ")
    assert spaced.args == ["a", "b"], spaced.args

    empty = make_ctx(text="")
    assert empty.args == [], empty.args

    whitespace = make_ctx(text="   ")
    assert whitespace.args == [], whitespace.args

    no_message = make_ctx(text=None)
    assert no_message.args == [], no_message.args
    print("[ok] ctx.args parses command payloads cleanly")


def main() -> None:
    check_flow_fallback_names()
    check_callback_filter()
    check_ctx_args()
    print("fixes self-check OK")


if __name__ == "__main__":
    main()
