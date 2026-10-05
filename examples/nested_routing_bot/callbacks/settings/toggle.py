from t8ot import Context
from t8ot.base import BaseCallback


class SettingsToggleCallback(BaseCallback):
    """Discovered from callbacks/settings/toggle.py -> data starting with "settings:"."""

    pattern = "settings:"

    async def execute(self, ctx: Context) -> None:
        await ctx.answer(f"Toggled {ctx.data}")