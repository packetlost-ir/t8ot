from abc import ABC, abstractmethod
from typing import Optional
from ..context import Context


class BaseCommand(ABC):
    """Base class for slash command handlers (e.g., /start)."""

    name: str = ""
    description: Optional[str] = None

    @abstractmethod
    async def execute(self, ctx: Context) -> None:
        pass