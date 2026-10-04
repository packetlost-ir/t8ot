from t8ot.base import BaseCommand
from t8ot import Context


class StartCommand(BaseCommand):
    name = "start"

    async def execute(self, ctx: Context) -> None:
        user_name = ctx.user.first_name if ctx.user else "User"
        await ctx.reply(f"Hello {user_name}! t8ot is working flawlessly.")