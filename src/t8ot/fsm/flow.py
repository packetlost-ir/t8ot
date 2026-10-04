from abc import ABC, abstractmethod
from typing import Callable, Optional, List, Dict, Any
from ..context import Context


class Step:
    def __init__(
        self,
        name: str,
        prompt: str,
        validator: Optional[Callable[[Context], bool]] = None,
        error_message: str = "Invalid input, please try again.",
    ):
        self.name = name
        self.prompt = prompt
        self.validator = validator
        self.error_message = error_message


class BaseFlow(ABC):
    """Base class for multi-step interactive flows."""

    name: str = ""
    cancel_commands: List[str] = ["/cancel", "cancel", "لغو"]

    def __init__(self):
        self.steps: List[Step] = self.define_steps()

    @abstractmethod
    def define_steps(self) -> List[Step]:
        """Define the sequence of steps for this flow."""
        pass

    @abstractmethod
    async def on_finish(self, ctx: Context, data: Dict[str, Any]) -> None:
        """Called when all steps are successfully completed."""
        pass

    async def on_cancel(self, ctx: Context) -> None:
        """Called when user cancels the flow."""
        await ctx.reply("Process cancelled.")