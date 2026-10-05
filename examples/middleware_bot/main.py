import os

from t8ot import Bot

from middlewares.auth import AuthMiddleware
from middlewares.logger import LoggerMiddleware

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

bot = Bot(token=BOT_TOKEN)

# Order matters: auth may halt the pipeline before logger ever runs a handler.
bot.use(AuthMiddleware())
bot.use(LoggerMiddleware())

# Auto-discover handlers across project directories
bot.load_handlers("examples/middleware_bot/commands")

if __name__ == "__main__":
    bot.run()
