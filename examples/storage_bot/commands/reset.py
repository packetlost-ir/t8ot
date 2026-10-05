from t8ot import Context
from t8ot.base import BaseCommand


class ResetCommand(BaseCommand):
    name = "reset"

    async def execute(self, ctx: Context) -> None:
        ctx.app.storage.clear(ctx.user.id)
        await ctx.reply("🧹 Storage cleared. Send /start for a fresh survey.")