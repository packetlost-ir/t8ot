"""Dry-run for nested handler discovery. Run: python examples/nested_routing_bot/verify.py"""

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from t8ot import Bot

HERE = Path(__file__).resolve().parent


def commands(bot: Bot) -> set:
    """Command names telebot currently routes."""
    return {
        name
        for handler in bot.bot.message_handlers
        for name in handler["filters"].get("commands", [])
    }


def callback_filters(bot: Bot) -> set:
    """Callback predicates telebot currently routes."""
    return {h["filters"]["func"] for h in bot.bot.callback_query_handlers}


def accepts(predicate, data: str) -> bool:
    """Calls a t8ot callback filter with a stub carrying ``data``."""
    return bool(predicate(SimpleNamespace(data=data)))


def main() -> None:
    os.chdir(HERE.parents[1])  # match main.py's repo-root-relative paths
    bot = Bot(token="0:TEST")

    # A single call must reach handlers nested one and two levels deep.
    bot.load_handlers("examples/nested_routing_bot/commands")
    assert {"admin_stats", "info"} <= commands(bot), commands(bot)
    print("[ok] one call registered both nested commands")

    bot.load_handlers("examples/nested_routing_bot/callbacks")
    matches = [
        p for p in callback_filters(bot)
        if accepts(p, "settings:toggle") and not accepts(p, "other:x")
    ]
    assert matches, callback_filters(bot)
    print("[ok] nested callback registered and matching its pattern")

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
            "    name = 'probe_ok'\n"
            "    async def execute(self, ctx):\n"
            "        await ctx.reply('ok')\n"
        )
        bot.load_handlers(str(root))
        assert "probe_ok" in commands(bot)
        print("[ok] private, hidden and __init__ modules skipped")

    # Identical filenames in sibling folders must not collide in sys.modules.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for folder in ("admin", "user"):
            (root / folder).mkdir()
            (root / folder / "stats.py").write_text(
                "from t8ot.base import BaseCommand\n"
                f"class Stats{folder.capitalize()}Command(BaseCommand):\n"
                f"    name = 'probe_{folder}_stats'\n"
                "    async def execute(self, ctx):\n"
                "        await ctx.reply('x')\n"
            )
        bot.load_handlers(str(root))
        assert {"probe_admin_stats", "probe_user_stats"} <= commands(bot)
        print("[ok] sibling folders with identical filenames both registered")

    # A broken handler must warn, not kill the loader.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "broken.py").write_text("import nonexistent_module_xyz\n")
        (root / "good.py").write_text(
            "from t8ot.base import BaseCommand\n"
            "class GoodCommand(BaseCommand):\n"
            "    name = 'probe_good'\n"
            "    async def execute(self, ctx):\n"
            "        await ctx.reply('ok')\n"
        )
        bot.load_handlers(str(root))
        assert "probe_good" in commands(bot)
        print("[ok] broken handler skipped, siblings still loaded")

    print("nested routing dry-run OK")


if __name__ == "__main__":
    main()