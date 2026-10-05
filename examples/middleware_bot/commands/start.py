from t8ot import BaseCommand, Context


class StartCommand(BaseCommand):
    name = "start"

    async def execute(self, ctx: Context) -> None:
        # Everything below was placed in ctx.extra by the middlewares.
        permissions = ctx.extra.get("permissions", [])
        granted = ", ".join(permissions) if permissions else "none"

        await ctx.reply(
            f"Hello {ctx.user.first_name}!\n"
            f"<b>Permissions:</b> {granted}\n"
            f"<b>Injected keys:</b> {', '.join(sorted(ctx.extra))}"
        )
