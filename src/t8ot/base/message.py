from abc import ABC, abstractmethod
from typing import Optional, List
from ..context import Context


class BaseMessage(ABC):
    """Base class for standard text or media message handlers."""

    content_types: List[str] = ["text"]
    text_filter: Optional[str] = None

    @abstractmethod
    async def execute(self, ctx: Context) -> None:
        pass