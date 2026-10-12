import sys
import re
import hmac
import logging
import inspect
import importlib.util
from pathlib import Path
from typing import Optional, Type, Dict, List, Callable, Awaitable
from types import ModuleType
import asyncio

from aiohttp import web
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, CallbackQuery, InlineQuery, Update

from .context import Context
from .base import BaseCommand, BaseCallback, BaseMessage, BaseInline
from .fsm import BaseStorage, MemoryStorage, BaseFlow
from .middleware import BaseMiddleware


logger = logging.getLogger("t8ot")

SECRET_TOKEN_HEADER = "X-Telegram-Bot-Api-Secret-Token"


def _default_flow_name(cls: type) -> str:
    """Derives a fallback flow name from a class name.

    Only a trailing ``flow`` suffix is stripped (case-insensitive), so
    ``FlowchartFlow`` becomes ``flowchart`` rather than ``chart``. Falls
    back to the lower-cased class name when stripping leaves it empty.
    """
    stripped = re.sub(r"(?i)flow$", "", cls.__name__)
    return stripped.lower() or cls.__name__.lower()


def _build_callback_filter(
    pattern: Optional[str],
) -> Callable[[CallbackQuery], bool]:
    """Builds a callback-data predicate from a routing pattern.

    ``None`` matches everything. A trailing ``:`` or ``*`` opts into prefix
    matching (the ``*`` is stripped before the comparison); any other value
    requires an exact match, so ``"user"`` never swallows ``"user_settings"``.
    """
    if pattern is None:
        return lambda call: True
    if pattern.endswith(":"):
        return lambda call: bool(call.data) and call.data.startswith(pattern)
    if pattern.endswith("*"):
        base = pattern[:-1]
        return lambda call: bool(call.data) and call.data.startswith(base)
    return lambda call: call.data == pattern


class Bot:
    def __init__(
        self,
        token: str,
        parse_mode: Optional[str] = "HTML",
        storage: Optional[BaseStorage] = None,
    ):
        self.bot = AsyncTeleBot(token=token, parse_mode=parse_mode)
        self.token = token
        self.storage: BaseStorage = storage or MemoryStorage()
        self.flows: Dict[str, BaseFlow] = {}
        self.middlewares: List[BaseMiddleware] = []

        # Global message interceptor for active multi-step flows
        @self.bot.message_handler(
            func=lambda msg: self.storage.get_state(msg.from_user.id) is not None,
            content_types=['text', 'contact', 'location']
        )
        async def flow_interceptor(message: Message):
            ctx = Context(self, message)
            await self._execute_with_middlewares(ctx, self._handle_flow_step)

    def use(self, middleware: BaseMiddleware) -> None:
        """Registers a global middleware into the execution pipeline."""
        self.middlewares.append(middleware)

    async def _execute_with_middlewares(
        self,
        ctx: Context,
        handler: Callable[[Context], Awaitable[None]]
    ) -> None:
        """Executes pre-hooks, the target handler, and post-hooks."""
        executed_middlewares: List[BaseMiddleware] = []
        halted = False
        exception: Optional[Exception] = None

        try:
            # 1. Run pre_process hooks sequentially
            for mw in self.middlewares:
                allowed = await mw.pre_process(ctx)
                executed_middlewares.append(mw)
                if not allowed:
                    halted = True  # Request halted by middleware
                    break

            # 2. Execute target handler
            if not halted:
                await handler(ctx)

        except Exception as e:
            exception = e

        # 3. Unwind post_process hooks in reverse order (success, halt or error)
        for mw in reversed(executed_middlewares):
            await mw.post_process(ctx, exception=exception)

        if exception is not None:
            raise exception

    def _import_module_from_file(self, file_path: Path, root: Path) -> Optional[ModuleType]:
        """Import a handler file under a name derived from its relative path.

        The relative path keeps same-named files in sibling folders
        (``admin/stats.py`` vs ``user/stats.py``) from clashing in
        ``sys.modules``. Returns ``None`` when the file cannot be imported.
        """
        rel = file_path.relative_to(root).as_posix()
        dotted = rel[:-3].replace("/", ".")
        module_name = f"t8ot_dynamic_{dotted}_{abs(hash(str(file_path.resolve())))}"

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            print(f"[t8ot] Warning: Cannot load '{rel}'.")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            del sys.modules[module_name]  # Never cache a half-imported module
            print(f"[t8ot] Warning: Failed to import '{rel}': {e!r}")
            return None
        return module

    def load_handlers(self, directory: str):
        """Recursively discover and register handler classes under ``directory``."""
        root = Path(directory)
        if not root.is_dir():
            print(f"[t8ot] Warning: '{directory}' is not a directory.")
            return

        for py_file in sorted(root.rglob("*.py")):
            rel = py_file.relative_to(root)
            # Skip private/hidden modules: __init__.py, _helpers.py, .cache/x.py
            if any(part.startswith(("_", ".")) for part in rel.parts):
                continue

            module = self._import_module_from_file(py_file, root)
            if not module:
                continue

            for _, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ != module.__name__:
                    continue

                if issubclass(obj, BaseCommand) and obj is not BaseCommand:
                    self._register_command(obj)

                elif issubclass(obj, BaseCallback) and obj is not BaseCallback:
                    self._register_callback(obj)

                elif issubclass(obj, BaseMessage) and obj is not BaseMessage:
                    self._register_message(obj)

                elif issubclass(obj, BaseInline) and obj is not BaseInline:
                    self._register_inline(obj)

                elif issubclass(obj, BaseFlow) and obj is not BaseFlow:
                    self._register_flow(obj)

    def _register_flow(self, cls: Type[BaseFlow]):
        instance = cls()
        flow_name = instance.name or _default_flow_name(cls)
        self.flows[flow_name] = instance
        print(f"[t8ot] Registered flow: {flow_name}")

    def _register_command(self, cls: Type[BaseCommand]):
        instance = cls()
        cmd_name = instance.name or cls.__name__.lower().replace("command", "")

        @self.bot.message_handler(commands=[cmd_name])
        async def handler(message: Message):
            ctx = Context(self, message)
            await self._execute_with_middlewares(ctx, instance.execute)

        print(f"[t8ot] Registered command: /{cmd_name}")

    def _register_callback(self, cls: Type[BaseCallback]):
        instance = cls()
        pattern = instance.pattern
        filter_fn = _build_callback_filter(pattern)

        @self.bot.callback_query_handler(func=filter_fn)
        async def handler(call: CallbackQuery):
            ctx = Context(self, call)
            await self._execute_with_middlewares(ctx, instance.execute)

        print(f"[t8ot] Registered callback: {cls.__name__} (pattern={pattern})")

    def _register_message(self, cls: Type[BaseMessage]):
        instance = cls()
        filter_fn = (lambda msg: msg.text == instance.text_filter) if instance.text_filter else (lambda msg: True)

        @self.bot.message_handler(func=filter_fn, content_types=instance.content_types)
        async def handler(message: Message):
            # Ignore if user is currently in a flow
            if self.storage.get_state(message.from_user.id) is not None:
                return
            ctx = Context(self, message)
            await self._execute_with_middlewares(ctx, instance.execute)

        print(f"[t8ot] Registered message handler: {cls.__name__}")

    def _register_inline(self, cls: Type[BaseInline]):
        instance = cls()

        @self.bot.inline_handler(func=lambda query: True)
        async def handler(inline_query: InlineQuery):
            ctx = Context(self, inline_query)
            await self._execute_with_middlewares(ctx, instance.execute)

        print(f"[t8ot] Registered inline handler: {cls.__name__}")

    async def start_flow(self, ctx: Context, flow_name: str):
        flow = self.flows.get(flow_name)
        if not flow or not flow.steps:
            raise ValueError(f"Flow '{flow_name}' not found or has no steps.")

        first_step = flow.steps[0]
        self.storage.set_state(ctx.user.id, f"{flow_name}:0")
        await ctx.reply(first_step.prompt)

    async def cancel_user_flow(self, ctx: Context):
        state = self.storage.get_state(ctx.user.id)
        if state:
            flow_name, _ = state.split(":")
            flow = self.flows.get(flow_name)
            self.storage.clear(ctx.user.id)
            if flow:
                await flow.on_cancel(ctx)
            else:
                await ctx.reply("Cancelled.")

    async def _handle_flow_step(self, ctx: Context):
        state = self.storage.get_state(ctx.user.id)
        if not state:
            return

        flow_name, step_idx_str = state.split(":")
        step_idx = int(step_idx_str)
        flow = self.flows.get(flow_name)

        if not flow:
            self.storage.clear(ctx.user.id)
            return

        # Check for cancel keywords
        if ctx.text and ctx.text.strip().lower() in [cmd.lower() for cmd in flow.cancel_commands]:
            await self.cancel_user_flow(ctx)
            return

        current_step = flow.steps[step_idx]

        # Validation
        if current_step.validator:
            is_valid = current_step.validator(ctx)
            if inspect.iscoroutine(is_valid):
                is_valid = await is_valid

            if not is_valid:
                await ctx.reply(current_step.error_message)
                return

        # Save step value
        value = ctx.value
        self.storage.update_data(ctx.user.id, **{current_step.name: value})

        # Move to next step or complete
        next_idx = step_idx + 1
        if next_idx < len(flow.steps):
            self.storage.set_state(ctx.user.id, f"{flow_name}:{next_idx}")
            next_step = flow.steps[next_idx]
            await ctx.reply(next_step.prompt)
        else:
            data = self.storage.get_data(ctx.user.id)
            self.storage.clear(ctx.user.id)
            await flow.on_finish(ctx, data)

    def run(self):
        print("[t8ot] Bot is polling...")
        asyncio.run(self.bot.infinity_polling())

    def _build_webhook_app(
        self,
        webhook_url: str,
        path: str,
        secret_token: Optional[str],
        drop_pending_updates: bool,
    ) -> web.Application:
        """Builds the aiohttp application serving one webhook endpoint.

        Kept separate from :meth:`run_webhook` so tests can drive the
        application through ``aiohttp.test_utils`` without binding a socket.
        """

        async def handle(request: web.Request) -> web.Response:
            if secret_token is not None:
                provided = request.headers.get(SECRET_TOKEN_HEADER)
                if provided is None or not hmac.compare_digest(provided, secret_token):
                    return web.Response(status=403, text="Forbidden")
            try:
                data = await request.json()
            except (ValueError, web.HTTPBadRequest):
                return web.Response(status=400, text="Bad Request")

            try:
                update = Update.de_json(data)
            except (KeyError, TypeError, AttributeError, ValueError):
                update = None
            if update is None:
                return web.Response(status=400, text="Bad Request")

            # A handler failure must not bubble up: Telegram would otherwise
            # retry the same update forever. Acknowledge it regardless.
            try:
                await self.bot.process_new_updates([update])
            except Exception:  # keep the server alive
                logger.exception("Error while processing update")
            return web.Response(text="OK")

        async def on_startup(app: web.Application) -> None:
            await self.bot.set_webhook(
                url=webhook_url,
                secret_token=secret_token,
                drop_pending_updates=drop_pending_updates,
            )
            logger.info("Webhook registered at %s", webhook_url)

        async def on_cleanup(app: web.Application) -> None:
            await self.bot.delete_webhook()
            await self.bot.close_session()
            logger.info("Webhook server stopped")

        app = web.Application()
        app.router.add_post(path, handle)
        app.on_startup.append(on_startup)
        app.on_cleanup.append(on_cleanup)
        return app

    async def run_webhook(
        self,
        webhook_url: str,
        host: str = "0.0.0.0",
        port: int = 8080,
        path: Optional[str] = None,
        secret_token: Optional[str] = None,
        drop_pending_updates: bool = False,
    ) -> None:
        """Serves the bot over an aiohttp webhook endpoint.

        Registers ``webhook_url`` with Telegram on startup, dispatches
        incoming updates to the same handler pipeline as polling, and
        removes the webhook on shutdown. Runs until cancelled.
        """
        if not path:
            path = f"/{self.token}"
        elif not path.startswith("/"):
            path = f"/{path}"

        app = self._build_webhook_app(webhook_url, path, secret_token, drop_pending_updates)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=host, port=port)
        await site.start()
        logger.info("Webhook server listening on %s:%s%s", host, port, path)
        try:
            await asyncio.Event().wait()
        finally:
            await runner.cleanup()