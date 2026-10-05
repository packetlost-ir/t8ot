from t8ot import Context
from t8ot.base import BaseCommand


class InfoCommand(BaseCommand):
    """Discovered from commands/user/info.py -> /info."""

    name = "info"

    async def execute(self, ctx: Context) -> None:
        await ctx.reply("👤 User Info")