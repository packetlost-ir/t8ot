import re
from t8ot.fsm import BaseFlow, Step
from t8ot import Context


def is_valid_phone(ctx: Context) -> bool:
    if not ctx.text:
        return False
    # Example regex for Iranian phone numbers or standard 11 digits
    return bool(re.match(r"^09\d{9}$", ctx.text.strip()))


def is_valid_age(ctx: Context) -> bool:
    if not ctx.text or not ctx.text.isdigit():
        return False
    return 10 <= int(ctx.text) <= 99


class RegistrationFlow(BaseFlow):
    name = "register"
    cancel_commands = ["/cancel", "cancel", "لغو"]

    def define_steps(self):
        return [
            Step(
                name="name",
                prompt="👋 Please enter your full name:",
                validator=lambda ctx: len(ctx.text or "") >= 3,
                error_message="⚠️ Name must be at least 3 characters. Try again:",
            ),
            Step(
                name="phone",
                prompt="📱 Please enter your mobile number (e.g., 09121234567):",
                validator=is_valid_phone,
                error_message="⚠️ Invalid mobile number format. Try again (or type /cancel):",
            ),
            Step(
                name="age",
                prompt="🎂 Please enter your age:",
                validator=is_valid_age,
                error_message="⚠️ Age must be a number between 10 and 99. Try again:",
            ),
        ]

    async def on_finish(self, ctx: Context, data: dict):
        response_text = (
            "🎉 <b>Registration Complete!</b>\n\n"
            f"<b>Name:</b> {data.get('name')}\n"
            f"<b>Phone:</b> {data.get('phone')}\n"
            f"<b>Age:</b> {data.get('age')}"
        )
        await ctx.reply(response_text)

    async def on_cancel(self, ctx: Context):
        await ctx.reply("❌ Registration process has been cancelled.")