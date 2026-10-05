"""Dry-run for nested handler discovery. Run: python examples/nested_routing_bot/verify.py"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from t8ot import Bot

HERE = Path(__file__).resolve().parent


def main() -> None:
    os.chdir(HERE.parents[1])  # match main.py's repo-root-relative paths
    bot = Bot(token="0:TEST")

    before = len(bot.bot.message_handlers)
    bot.load_handlers("examples/nested_routing_bot/commands")
    # The flow interceptor is always registered first, so only our two nested
    # commands may be added by that single call.
    assert len(bot.bot.message_handlers) == before + 2, bot.bot.message_handlers
    print("[ok] one call registered both nested commands")

    bot.load_handlers("examples/nested_routing_bot/callbacks")
    assert len(bot.bot.callback_query_handlers) == 1
    print("[ok] nested callback registered")

    # Skipped: __init__.py, private files, hidden dirs.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "_skipped").mkdir()
        (root / ".hidden").mkdir()
        (root / "__init__.py").write_text("raise RuntimeError('must not be imported')")
        (root / "_skipped" / "boom.py").write_text("raise RuntimeError('nope')")
        (root / ".hidden" / "boom.py").write_text("raise RuntimeError('nope')")
        (root / "ok.py").write_text(
            "from t8ot.base import BaseCommand\n"
            "class OkCommand(BaseCommand):\n"
            "    async def execute(self, ctx):\n"
            "        await ctx.reply('ok')\n"
        )
        bot.load_handlers(str(root))
        assert len(bot.bot.message_handlers) == before + 3

    # Identical filenames in sibling folders must not collide in sys.modules.
    twin = tempfile.mkdtemp()
    twin_root = Path(twin)
    for folder in ("admin", "user"):
        (twin_root / folder).mkdir()
        (twin_root / folder / "stats.py").write_text(
            "from t8ot.base import BaseCommand\n"
            f"class Stats{folder.capitalize()}Command(BaseCommand):\n"
            f"    name = '{folder}_stats'\n"
            "    async def execute(self, ctx):\n"
            "        await ctx.reply('x')\n"
        )
    bot.load_handlers(twin)
    assert len(bot.bot.message_handlers) == before + 5
    print("[ok] sibling folders with identical filenames both registered")

    # A broken handler must warn, not kill the loader.
    broken = tempfile.mkdtemp()
    (Path(broken) / "broken.py").write_text("import nonexistent_module_xyz\n")
    (Path(broken) / "good.py").write_text(
        "from t8ot.base import BaseCommand\n"
        "class GoodCommand(BaseCommand):\n"
        "    async def execute(self, ctx):\n"
        "        await ctx.reply('ok')\n"
    )
    bot.load_handlers(broken)
    assert len(bot.bot.message_handlers) == before + 6
    print("[ok] broken handler skipped, siblings still loaded")

    print("nested routing dry-run OK")


if __name__ == "__main__":
    main()