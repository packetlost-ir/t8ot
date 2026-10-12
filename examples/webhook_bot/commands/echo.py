from t8ot import Context
from t8ot.base import BaseCommand


class EchoCommand(BaseCommand):
    name = "echo"
    description = "Echoes the arguments back: /echo hello world"

    async def execute(self, ctx: Context) -> None:
        # ctx.args drops the command token and splits on whitespace.
        if not ctx.args:
            await ctx.reply("Usage: /echo <text>")
            return
        await ctx.reply(" ".join(ctx.args))
