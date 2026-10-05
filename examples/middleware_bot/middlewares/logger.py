import time
from typing import Optional

from t8ot import BaseMiddleware, Context


class LoggerMiddleware(BaseMiddleware):
    """Measures how long a handler took to execute."""

    async def pre_process(self, ctx: Context) -> bool:
        # Stamp the entry time so post_process can compute the duration.
        ctx.extra["start_time"] = time.perf_counter()
        print(f"[middleware] -> {ctx.user.id} entered the pipeline")
        return True

    async def post_process(self, ctx: Context, exception: Optional[Exception] = None) -> None:
        elapsed = (time.perf_counter() - ctx.extra["start_time"]) * 1000
        if exception is not None:
            print(f"[middleware] <- {ctx.user.id} failed after {elapsed:.2f}ms: {exception!r}")
        else:
            print(f"[middleware] <- {ctx.user.id} finished in {elapsed:.2f}ms")
