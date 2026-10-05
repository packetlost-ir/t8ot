from t8ot import Context
from t8ot.base import BaseCommand


class StartCommand(BaseCommand):
    name = "start"

    async def execute(self, ctx: Context) -> None:
        state = ctx.app.storage.get_state(ctx.user.id)
        saved = ctx.app.storage.get_data(ctx.user.id)

        # A user can resume exactly where the previous run left off.
        if state:
            await ctx.reply(
                f"⏸ You already have a survey in progress ({state}).\n"
                f"Saved so far: {saved}\n"
                "Answer the question, type /cancel to abort, or /reset to start over."
            )
            return

        if saved:
            await ctx.reply(f"📂 Previous answers: {saved}")
        await ctx.reply("Starting the survey...")
        await ctx.app.start_flow(ctx, "survey")