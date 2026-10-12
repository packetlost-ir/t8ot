from t8ot import Context
from t8ot.base import BaseCommand


class StartCommand(BaseCommand):
    name = "start"
    description = "Welcome message"

    async def execute(self, ctx: Context) -> None:
        await ctx.reply(
            f"Hello {ctx.user.first_name}!\n"
            "This bot is running over a webhook.\n"
            "Try /echo hello world."
        )
