import os
from t8ot import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

bot = Bot(token=BOT_TOKEN)

bot.load_handlers("examples/test_bot/commands")

if __name__ == "__main__":
    bot.run()