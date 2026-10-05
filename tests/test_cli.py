"""Self-check for the t8ot CLI scaffolder. Run: python tests/test_cli.py"""

import importlib.util
import os
import tempfile
from pathlib import Path

from t8ot.cli.main import cli


def build_project(root: Path) -> None:
    os.chdir(root)
    cli(["init", "my_bot"])
    os.chdir(root / "my_bot")  # generators are cwd-relative

    for name in (".env.example", ".gitignore", "main.py", "commands/start.py"):
        assert (root / "my_bot" / name).exists(), name
    for folder in ("commands", "callbacks", "flows"):
        assert (root / "my_bot" / folder).is_dir(), folder

    env = (root / "my_bot" / ".env.example").read_text()
    assert "BOT_TOKEN=your_token_here" in env
    gitignore = (root / "my_bot" / ".gitignore").read_text()
    assert ".env" in gitignore and "*.db" in gitignore

    cli(["make:command", "admin_ban"])
    cli(["make:callback", "settings"])  # default pattern: "settings:"
    cli(["make:flow", "onboarding"])
    cli(["make:callback", "theme", "--pattern", "theme:"])

    os.chdir(root / "my_bot")
    generated = sorted(str(p) for p in Path(".").rglob("*.py"))
    assert generated == [
        "callbacks/settings.py",
        "callbacks/theme.py",
        "commands/admin_ban.py",
        "commands/start.py",
        "flows/onboarding.py",
        "main.py",
    ], generated

    for path in Path(".").rglob("*.py"):
        compile(path.read_text(), str(path), "exec")  # syntax check

    assert 'pattern = "settings:"' in Path("callbacks/settings.py").read_text()
    assert 'pattern = "theme:"' in Path("callbacks/theme.py").read_text()

    # Re-running must not clobber edits.
    Path("commands/admin_ban.py").write_text("# edited\n")
    cli(["make:command", "admin_ban"])
    assert Path("commands/admin_ban.py").read_text() == "# edited\n"


def generated_project_boots(root: Path) -> None:
    os.chdir(root / "my_bot")
    spec = importlib.util.spec_from_file_location("generated_main", "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    bot = module.bot
    assert len(bot.bot.message_handlers) == 2  # flow interceptor + /start
    assert len(bot.bot.callback_query_handlers) == 2  # settings + theme
    assert sorted(bot.flows) == ["onboarding"]
    print("[ok] generated project boots and registers its handlers")


def invalid_name_rejected() -> None:
    for bad in ("bad/name", "9lives", "../escape"):
        try:
            cli(["make:command", bad])
        except SystemExit as exc:
            assert exc.code == 2, exc.code
            continue
        raise AssertionError(f"expected rejection for {bad!r}")
    print("[ok] invalid handler names rejected")


def main() -> None:
    cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        build_project(Path(tmp))
        generated_project_boots(Path(tmp))
        invalid_name_rejected()
    os.chdir(cwd)
    print("cli self-check OK")


if __name__ == "__main__":
    main()