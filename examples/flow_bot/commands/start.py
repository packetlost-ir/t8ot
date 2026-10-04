from t8ot.base import BaseCommand
from t8ot import Context


class StartCommand(BaseCommand):
    name = "start"

    async def execute(self, ctx: Context) -> None:
        await ctx.reply("Welcome! Starting the registration process...")
        # Start the registered flow by its name
        await ctx.app.start_flow(ctx, "register")