from t8ot import Context
from t8ot.fsm import BaseFlow, Step


class SurveyFlow(BaseFlow):
    """Two-step survey: name, then a favourite colour."""

    name = "survey"

    def define_steps(self):
        return [
            Step(
                name="name",
                prompt="📝 What is your name?",
                validator=lambda ctx: len(ctx.text or "") >= 2,
                error_message="⚠️ Name must be at least 2 characters. Try again:",
            ),
            Step(
                name="color",
                prompt="🎨 Favourite colour?",
            ),
        ]

    async def on_finish(self, ctx: Context, data: dict):
        await ctx.reply(
            "🎉 <b>Survey complete!</b>\n\n"
            f"<b>Name:</b> {data.get('name')}\n"
            f"<b>Colour:</b> {data.get('color')}\n\n"
            "Send /start again to restart (answers persist in SQLite)."
        )