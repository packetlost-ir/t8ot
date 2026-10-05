from typing import List, Optional

from t8ot import BaseMiddleware, Context

# Users blocked from reaching any handler.
BANNED_USER_IDS = [999999]


class AuthMiddleware(BaseMiddleware):
    """Blocks banned users and injects mock permissions into the context."""

    async def pre_process(self, ctx: Context) -> bool:
        if ctx.user.id in BANNED_USER_IDS:
            print(f"[middleware] denied access for user {ctx.user.id}")
            # Returning False halts the pipeline; the handler never runs.
            return False

        # Handlers read permissions from ctx.extra.
        ctx.extra["permissions"] = ["read", "write"]
        print(f"[middleware] granted permissions to user {ctx.user.id}")
        return True

    async def post_process(self, ctx: Context, exception: Optional[Exception] = None) -> None:
        # Cleanup hook: runs on success, halt and failure.
        granted: List[str] = ctx.extra.pop("permissions", [])
        print(f"[middleware] revoked {len(granted)} permissions for user {ctx.user.id}")
