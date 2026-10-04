import os
from t8ot import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

bot = Bot(token=BOT_TOKEN)

# Auto-load both commands and multi-step flows
bot.load_handlers("examples/flow_bot/commands")
bot.load_handlers("examples/flow_bot/flows")

if __name__ == "__main__":
    bot.run()