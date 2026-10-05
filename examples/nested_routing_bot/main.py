import os

from t8ot import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

bot = Bot(token=BOT_TOKEN)

# One call walks the whole tree: commands/admin/stats.py, commands/user/info.py
# and callbacks/settings/toggle.py are all discovered recursively.
bot.load_handlers("examples/nested_routing_bot/commands")
bot.load_handlers("examples/nested_routing_bot/callbacks")

if __name__ == "__main__":
    bot.run()