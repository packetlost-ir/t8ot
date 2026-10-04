from abc import ABC, abstractmethod
from typing import Optional
from ..context import Context


class BaseInline(ABC):
    """Base class for inline queries (@bot)."""

    pattern: Optional[str] = None

    @abstractmethod
    async def execute(self, ctx: Context) -> None:
        pass