import os

from t8ot import Bot, SQLiteStorage

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Swapping backends is a one-line change — flow logic stays untouched:
#   MemoryStorage()                                    # volatile, per-process
#   SQLiteStorage("survey_bot.db")                     # local file, survives restarts
#   RedisStorage("redis://localhost:6379/0", ttl=3600)  # shared across instances
bot = Bot(token=BOT_TOKEN, storage=SQLiteStorage("survey_bot.db"))

bot.load_handlers("examples/storage_bot/commands")
bot.load_handlers("examples/storage_bot/flows")

if __name__ == "__main__":
    bot.run()