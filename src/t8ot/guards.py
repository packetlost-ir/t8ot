"""Decorators that restrict when a handler is allowed to run."""

import functools
from typing import Awaitable, Callable, List, Optional, Set, Union

from .context import Context

Handler = Callable[[Context], Awaitable[None]]
Decorator = Callable[[Handler], Handler]

GROUP_CHAT_TYPES = ("group", "supergroup")


def admin_only(
    admin_ids: Union[List[int], Set[int]],
    on_denied: Optional[str] = "⛔ Access denied.",
) -> Decorator:
    """Allows the handler to run only for the listed Telegram user IDs."""

    allowed = set(admin_ids)

    def decorator(func: Handler) -> Handler:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> None:
            # args is (self, ctx) for a bound method and (ctx,) for a function.
            ctx = args[-1] if args else kwargs["ctx"]
            if ctx.user.id not in allowed:
                if on_denied:
                    await ctx.reply(on_denied)
                return
            await func(*args, **kwargs)

        return wrapper

    return decorator


def _chat_type_only(chat_types: Set[str], on_denied: Optional[str]) -> Decorator:
    """Shared implementation for the chat-type guards."""

    def decorator(func: Handler) -> Handler:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> None:
            ctx = args[-1] if args else kwargs["ctx"]
            chat = ctx.chat
            if chat is None or chat.type not in chat_types:
                if on_denied:
                    await ctx.reply(on_denied)
                return
            await func(*args, **kwargs)

        return wrapper

    return decorator


def private_only(on_denied: Optional[str] = None) -> Decorator:
    """Allows the handler to run only in private (one-to-one) chats."""
    return _chat_type_only({"private"}, on_denied)


def group_only(on_denied: Optional[str] = None) -> Decorator:
    """Allows the handler to run only in group or supergroup chats."""
    return _chat_type_only(set(GROUP_CHAT_TYPES), on_denied)