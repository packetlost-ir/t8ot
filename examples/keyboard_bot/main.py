import os
from t8ot import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

bot = Bot(token=BOT_TOKEN)

# Load commands and callback handlers automatically
bot.load_handlers("examples/keyboard_bot/commands")
bot.load_handlers("examples/keyboard_bot/callbacks")

if __name__ == "__main__":
    bot.run()