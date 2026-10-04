from t8ot.base import BaseCallback
from t8ot import Context, InlineKeyboard


class ActionCallback(BaseCallback):
    pattern = "action:"

    async def execute(self, ctx: Context) -> None:
        action = ctx.data.replace("action:", "")

        if action == "profile":
            await ctx.answer("Loading profile...")
            back_kb = (
                InlineKeyboard()
                .button("⬅️ Back to Menu", callback_data="action:back")
                .build()
            )
            await ctx.edit(
                f"👤 <b>User Profile</b>\nName: {ctx.user.first_name}\nID: {ctx.user.id}",
                reply_markup=back_kb,
            )

        elif action == "settings":
            await ctx.answer("Opening settings...", show_alert=True)
            await ctx.edit("⚙️ Settings panel is currently under construction.")

        elif action == "stats":
            await ctx.answer()
            await ctx.edit("📊 Bot Stats: Everything is running smooth!")

        elif action == "back":
            await ctx.answer()
            # Restore the main inline menu
            main_kb = (
                InlineKeyboard()
                .button("Profile", callback_data="action:profile")
                .button("Settings", callback_data="action:settings")
                .button("Stats", callback_data="action:stats")
                .button("Website", url="https://github.com")
                .adjust(2)
                .build()
            )
            await ctx.edit("Select an inline option:", reply_markup=main_kb)