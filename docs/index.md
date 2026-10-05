# t8ot

**A modern, ergonomic micro-framework for Telegram bots** — built on top of
[pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) (`telebot`) with file-based routing,
a unified context, conversational FSM flows, pluggable storage, middlewares and access guards.

---

## Overview

| | |
|---|---|
| **Philosophy** | Asynchronous first, file-based routing, small surface, zero ceremony |
| **Runtime** | Python 3.10+, `asyncio`, `AsyncTeleBot` |
| **Dependencies** | `pyTelegramBotAPI`, `aiohttp` (plus `redis` only if you use `RedisStorage`) |
| **Entry point** | `Bot.run()` — long polling out of the box |

t8ot is deliberately small. There is no router table to maintain, no dependency-injection
container, and no decorator stack you have to learn before your first handler. You write a
class, drop the file in a folder, and the framework registers it.

---

## Architecture

```text
                    ┌────────────────────────────────────────────┐
   Telegram  ──────►│ Core Engine (Bot)                          │
   update           │  • AsyncTeleBot client                     │
                    │  • handler loader (recursive discovery)    │
                    │  • middleware pipeline                     │
                    └───────────────┬────────────────────────────┘
                                    │ builds
                    ┌───────────────▼────────────────────────────┐
                    │ Context (ctx)                              │
                    │  normalized event data + reply helpers     │
                    └───────┬──────────────────────┬─────────────┘
                            │                      │
             ┌──────────────▼───────────┐  ┌───────▼──────────────┐
             │ Handlers                 │  │ FSM                  │
             │  BaseCommand             │  │  BaseFlow + Step     │
             │  BaseCallback            │  │  storage backend     │
             │  BaseMessage             │  │  (memory/sqlite/redis)│
             │  BaseInline              │  └──────────────────────┘
             │  @admin_only, @group_only│  ┌──────────────────────┐
             └──────────────────────────┘  │ Middleware           │
                                          │  pre_process/post_...│
                                          └──────────────────────┘
```

### The five moving parts

1. **Core Engine — `Bot`**
   Wraps `AsyncTeleBot`, owns the middleware list, the registry of flows, the active storage
   backend, and the recursive handler loader.

2. **Context — `ctx`**
   One object handed to every handler. It normalizes `Message`, `CallbackQuery` and
   `InlineQuery` into a single interface (`ctx.user`, `ctx.text`, `ctx.reply()`, …), so handler
   code never branches on the raw update type.

3. **Routing — file-based discovery**
   `bot.load_handlers("commands")` walks a directory tree, imports every module it finds and
   registers each `Base*` subclass it discovers, at any depth.

4. **FSM — `BaseFlow` + storage**
   Multi-step conversations are declared as data (`Step` objects) and executed by the engine.
   Progress is persisted through a `BaseStorage` backend, so state survives restarts when you
   want it to.

5. **Middleware — `BaseMiddleware`**
   Cross-cutting concerns (auth, logging, rate limiting, metrics) are attached once and wrap
   every handler, with pre-hooks that can halt execution.

---

## Documentation

| Guide | What it covers |
|---|---|
| [Quickstart](quickstart.md) | Requirements, installation, `t8ot init`, first run |
| [Routing & Handler Discovery](routing.md) | File conventions, nested folders, the four handler base classes |
| [Context API & Responses](context.md) | Event data, messaging/media helpers, keyboard builders |
| [FSM & Storage](fsm-and-storage.md) | Multi-step flows, validation, memory/SQLite/Redis backends |
| [Middleware Pipeline](middleware.md) | Pre/post hooks, `ctx.extra` as a per-update scratchpad, halting |
| [Guards](guards.md) | `@admin_only`, `@private_only`, `@group_only` access control |
| [CLI](cli.md) | `t8ot init` and the `make:*` handler generators |

---

## Design rules

- **No hidden magic.** What a file does is decided by which base class it subclasses.
- **Explicit over implicit.** Storage, parse mode and middleware are constructor arguments,
  never environment lookups inside the framework.
- **Boring interfaces.** One `execute(self, ctx)` method, everywhere.
- **No new dependencies.** SQLite uses the standard library; Redis is an optional extra.

---

Next: [Quickstart](quickstart.md)