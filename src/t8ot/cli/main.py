import argparse
import re
from pathlib import Path
from typing import Callable, List, Optional

NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")

GITIGNORE = """\
.env
__pycache__/
*.pyc
*.db
"""

ENV_EXAMPLE = """\
BOT_TOKEN=your_token_here
"""

MAIN_PY = '''\
import os

from t8ot import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN", "123456:YOUR_TOKEN_HERE")

bot = Bot(token=BOT_TOKEN)

# Auto-discovery walks each tree recursively, so you can nest handlers freely.
bot.load_handlers("commands")
bot.load_handlers("callbacks")
bot.load_handlers("flows")

if __name__ == "__main__":
    bot.run()
'''

START_COMMAND = '''\
from t8ot import Context, InlineKeyboard
from t8ot.base import BaseCommand


class StartCommand(BaseCommand):
    name = "start"
    description = "Welcome message"

    async def execute(self, ctx: Context) -> None:
        keyboard = (
            InlineKeyboard()
            .button("Website", url="https://telegram.org")
            .button("Settings", callback_data="settings:open")
            .build()
        )
        await ctx.reply("Welcome to your t8ot bot!", reply_markup=keyboard)
'''

COMMAND_TEMPLATE = '''\
from t8ot import Context
from t8ot.base import BaseCommand


class {cls}Command(BaseCommand):
    """Handles /{name}."""

    name = "{name}"
    description = "TODO: describe /{name}"

    async def execute(self, ctx: Context) -> None:
        await ctx.reply("TODO: handle /{name}")
'''

CALLBACK_TEMPLATE = '''\
from t8ot import Context
from t8ot.base import BaseCallback


class {cls}Callback(BaseCallback):
    """Handles callback data starting with "{pattern}"."""

    pattern = "{pattern}"

    async def execute(self, ctx: Context) -> None:
        await ctx.answer("TODO: handle {pattern}")
'''

FLOW_TEMPLATE = '''\
from t8ot import Context
from t8ot.fsm import BaseFlow, Step


def is_number(ctx: Context) -> bool:
    """Example validator: rejects anything that is not a plain number."""
    return bool(ctx.text and ctx.text.strip().lstrip("-").isdigit())


class {cls}Flow(BaseFlow):
    """Two-step {name} flow."""

    name = "{name}"

    def define_steps(self):
        return [
            Step(
                name="amount",
                prompt="How much? (send /cancel to stop)",
                validator=is_number,
                error_message="That is not a number. Try again:",
            ),
            Step(
                name="reason",
                prompt="Why?",
            ),
        ]

    async def on_finish(self, ctx: Context, data: dict):
        await ctx.reply(f"Done! Collected: {data}")
'''


def _class_name(name: str) -> str:
    """Turns ``user-profile`` / ``user_profile`` into ``UserProfile``."""
    return "".join(part.capitalize() for part in re.split(r"[-_]", name))


def _render(template: str, **pairs: str) -> str:
    """Fills ``{token}`` placeholders without touching generated-code braces."""
    for key, value in pairs.items():
        template = template.replace("{" + key + "}", value)
    return template


def _write(path: Path, content: str) -> bool:
    """Writes ``content`` to ``path``, never overwriting an existing file."""
    if path.exists():
        print(f"[t8ot] Skipped (already exists): {path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"[t8ot] Created {path}")
    return True


def cmd_init(args: argparse.Namespace) -> None:
    """Scaffolds a runnable bot project in ``<project_name>/``."""
    root = Path(args.project_name)

    _write(root / ".env.example", ENV_EXAMPLE)
    _write(root / ".gitignore", GITIGNORE)
    _write(root / "main.py", MAIN_PY)
    _write(root / "commands" / "start.py", START_COMMAND)
    for folder in ("commands", "callbacks", "flows"):
        (root / folder).mkdir(parents=True, exist_ok=True)

    print(f"[t8ot] Project ready: {root.resolve()}")
    print("[t8ot] Next: cp .env.example .env  ->  add handlers  ->  python main.py")


def cmd_make_command(args: argparse.Namespace) -> None:
    _write(
        Path(args.dir) / f"{args.name}.py",
        _render(COMMAND_TEMPLATE, name=args.name, cls=_class_name(args.name)),
    )


def cmd_make_callback(args: argparse.Namespace) -> None:
    pattern = args.pattern or f"{args.name}:"
    _write(
        Path(args.dir) / f"{args.name}.py",
        _render(CALLBACK_TEMPLATE, pattern=pattern, cls=_class_name(args.name)),
    )


def cmd_make_flow(args: argparse.Namespace) -> None:
    _write(
        Path(args.dir) / f"{args.name}.py",
        _render(FLOW_TEMPLATE, name=args.name, cls=_class_name(args.name)),
    )


def _add_make(
    subparsers,
    command: str,
    handler: Callable[[argparse.Namespace], None],
    help_text: str,
    default_dir: str,
    with_pattern: bool = False,
) -> None:
    """Registers one ``make:*`` subcommand sharing the name/--dir options."""
    parser = subparsers.add_parser(command, help=help_text)
    parser.add_argument("name", help="Handler name (e.g. user_profile)")
    parser.add_argument("--dir", default=default_dir, help="Target directory")
    if with_pattern:
        parser.add_argument(
            "--pattern", default=None, help="Callback data prefix (default '<name>:')"
        )
    parser.set_defaults(func=handler)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="t8ot", description="t8ot CLI tool for Telegram bot scaffolding"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init", help="Create a new bot project scaffold"
    )
    init_parser.add_argument("project_name", help="Directory to create")
    init_parser.set_defaults(func=cmd_init)

    _add_make(subparsers, "make:command", cmd_make_command, "Generate a command handler", "commands")
    _add_make(
        subparsers, "make:callback", cmd_make_callback, "Generate a callback handler", "callbacks", True
    )
    _add_make(subparsers, "make:flow", cmd_make_flow, "Generate a multi-step flow", "flows")
    return parser


def cli(argv: Optional[List[str]] = None) -> int:
    """Entry point for the ``t8ot`` console script."""
    parser = build_parser()
    args = parser.parse_args(argv)

    name = getattr(args, "name", None)
    if name and not NAME_PATTERN.match(name):
        parser.error(
            f"invalid name '{name}': start with a letter, then use letters, "
            "digits, '-' or '_'"
        )

    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())