from t8ot.base import BaseCommand
from t8ot import Context, InlineKeyboard, ReplyKeyboard


class MenuCommand(BaseCommand):
    name = "menu"

    async def execute(self, ctx: Context) -> None:
        # 1. Reply Keyboard Example (phone, location, and simple action)
        reply_kb = (
            ReplyKeyboard(placeholder="Choose an option below...")
            .button("📱 Share Phone", request_contact=True)
            .button("📍 Share Location", request_location=True)
            .row()
            .button("Help")
            .button("About")
            .build()
        )

        await ctx.reply("Here is your standard reply menu:", reply_markup=reply_kb)

        # 2. Inline Keyboard Example with automatic 2-column layout (.adjust)
        inline_kb = (
            InlineKeyboard()
            .button("Profile", callback_data="action:profile")
            .button("Settings", callback_data="action:settings")
            .button("Stats", callback_data="action:stats")
            .button("Website", url="https://github.com")
            .adjust(3)
            .build()
        )

        await ctx.reply("Select an inline option:", reply_markup=inline_kb)