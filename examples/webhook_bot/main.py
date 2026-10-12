import asyncio
import os
from pathlib import Path

from t8ot import Bot

# All settings come from the environment so nothing secret is committed.
# Copy .env.example to .env and fill it in (or export the variables).
BOT_TOKEN = os.getenv("BOT_TOKEN", "123456:YOUR_TOKEN_HERE")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://example.com/webhook")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # None disables the header check
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

bot = Bot(token=BOT_TOKEN)

# Resolve the commands folder relative to this file, so the example runs
# identically from the repo root or from examples/webhook_bot/.
bot.load_handlers(str(Path(__file__).parent / "commands"))

if __name__ == "__main__":
    asyncio.run(
        bot.run_webhook(
            webhook_url=WEBHOOK_URL,
            host=HOST,
            port=PORT,
            path=WEBHOOK_PATH,
            secret_token=WEBHOOK_SECRET,
        )
    )
