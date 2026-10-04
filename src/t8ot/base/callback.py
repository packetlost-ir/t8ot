from abc import ABC, abstractmethod
from typing import Optional
from ..context import Context


class BaseCallback(ABC):
    """Base class for inline button callback handlers."""

    pattern: Optional[str] = None

    @abstractmethod
    async def execute(self, ctx: Context) -> None:
        pass