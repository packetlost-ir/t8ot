from abc import ABC
from typing import Optional
from ..context import Context


class BaseMiddleware(ABC):
    """Base class for all middleware components."""

    async def pre_process(self, ctx: Context) -> bool:
        """Executed before the handler is called.

        Returning False halts the pipeline and prevents handler execution.
        """
        return True

    async def post_process(self, ctx: Context, exception: Optional[Exception] = None) -> None:
        """Executed after the handler finishes (even if an error occurs)."""
        pass