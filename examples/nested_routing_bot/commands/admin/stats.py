from t8ot import Context
from t8ot.base import BaseCommand


class AdminStatsCommand(BaseCommand):
    """Discovered from commands/admin/stats.py -> /admin_stats."""

    name = "admin_stats"

    async def execute(self, ctx: Context) -> None:
        await ctx.reply("📊 Admin Dashboard")