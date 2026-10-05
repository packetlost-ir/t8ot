# Context API & Responses

Every handler receives a single object: the **context** (`ctx`). It normalizes `Message`,
`CallbackQuery` and `InlineQuery` into one interface, so your code never branches on the raw
update type.

```python
class StartCommand(BaseCommand):
    name = "start"

    async def execute(self, ctx: Context) -> None:
        await ctx.reply(f"Hello {ctx.user.first_name}!")
```

---

## Event data

| Member | Type | Description |
|---|---|---|
| `ctx.user` | `User` | Sender of the event (`first_name`, `id`, `username`, …) |
| `ctx.chat` | `Optional[Chat]` | Chat the event belongs to; `None` for inline queries |
| `ctx.chat_id` | `int` | Target chat for replies (inline queries fall back to the user id) |
| `ctx.message` | `Optional[Message]` | Underlying message, `None` for inline queries |
| `ctx.text` | `Optional[str]` | Message text, `None` when absent |
| `ctx.value` | `Any` | Primary payload: text, `contact.phone_number`, or `location` |
| `ctx.data` | `Optional[str]` | Raw `callback_data` on callback queries |
| `ctx.query` | `str` | Inline query text (`ctx.is_inline` only) |
| `ctx.extra` | `Dict[str, Any]` | Per-update scratchpad shared by middlewares and the handler |
| `ctx.is_callback` | `bool` | The event is a `CallbackQuery` |
| `ctx.is_inline` | `bool` | The event is an `InlineQuery` |
| `ctx.state_data` | `Dict[str, Any]` | Data collected so far in the active flow |
| `ctx.app` | `Bot` | The framework bot object (storage, flows, start/cancel flow) |
| `ctx.bot` | `AsyncTeleBot` | The underlying telebot client, for anything t8ot doesn't wrap |
| `ctx.raw_event` | `Message \| CallbackQuery \| InlineQuery` | The untouched Telegram object |

```python
async def execute(self, ctx: Context) -> None:
    if ctx.chat.type == "private":
        await ctx.reply("This is a direct chat.")
    await ctx.reply(f"value = {ctx.value!r}")
```

### `ctx.extra`

A plain dict created per update. Middlewares write to it, handlers read it — the standard way to
pass data down the pipeline:

```python
async def execute(self, ctx: Context) -> None:
    tenant = ctx.extra.get("tenant")
    await ctx.reply(f"tenant: {tenant}")
```

See [Middleware](middleware.md).

---

## Messaging helpers

### `reply(text, **kwargs)`

Sends a message to the current chat. Any `telebot` keyword argument is forwarded
(`reply_markup`, `parse_mode`, `disable_web_page_preview`, …).

```python
from t8ot import InlineKeyboard

keyboard = InlineKeyboard().button("Open", url="https://example.com").build()
await ctx.reply("Pick one:", reply_markup=keyboard)
```

### `answer(text=None, show_alert=False)`

Acknowledges a callback query (no-op for other event types).

```python
class ConfirmCallback(BaseCallback):
    pattern = "confirm:"

    async def execute(self, ctx: Context) -> None:
        await ctx.answer("Saved!", show_alert=True)
```

### `edit_text(text, **kwargs)`

Edits the current message, whatever the event type is. Raises `RuntimeError` when the event
carries no message (inline queries).

```python
await ctx.edit_text("Done ✅")
```

### `edit(text, **kwargs)`

Callback-only variant: raises `RuntimeError` outside a callback query. Useful when you want the
callback behaviour to be explicit.

### `delete() -> bool`

Deletes the current message. Returns `False` — never raises — when there is nothing to delete or
Telegram refuses (messages older than 48 hours, for example).

```python
if await ctx.delete():
    await ctx.reply("Oops, removed.")
```

---

## Media helpers

Each helper accepts a `file_id`, a URL or an open file object, plus an optional caption and any
telebot keyword arguments. All of them reply into the current chat.

```python
await ctx.reply_photo("https://example.com/cat.jpg", caption="Look at this")
await ctx.reply_document("report.pdf", caption="Your report")
await ctx.reply_video("clip.mp4", caption="Clip", width=480)
```

| Helper | telebot call |
|---|---|
| `reply_photo(photo, caption=None, **kwargs)` | `send_photo` |
| `reply_document(document, caption=None, **kwargs)` | `send_document` |
| `reply_video(video, caption=None, **kwargs)` | `send_video` |

---

## Flow helpers

| Helper | Description |
|---|---|
| `await ctx.app.start_flow(ctx, "survey")` | Start the registered flow `survey` |
| `await ctx.cancel_flow()` | Cancel the user's active flow (also runs `flow.on_cancel`) |
| `ctx.state_data` | Read-only view of the collected step data |

---

## Keyboards

Both builders are fluent: chain `.button(...)`, `.row()` and `.adjust(n)`, then `.build()` to get
the telebot markup object.

### `InlineKeyboard`

```python
from t8ot import InlineKeyboard

keyboard = (
    InlineKeyboard()
    .button("Profile", callback_data="menu:profile")
    .button("Settings", callback_data="menu:settings")
    .button("Docs", url="https://example.com/docs")
    .adjust(2)                 # re-flow into rows of two
    .build()
)

await ctx.reply("Choose:", reply_markup=keyboard)
```

`button(text, callback_data=None, url=None, web_app_url=None, switch_inline_query=None)` —
`callback_data` defaults to the button text when omitted. `adjust(n)` re-flows all buttons into
fixed-size rows; `row()` forces a line break. `InlineKeyboard(row_width=3)` is the constructor
default and is only a hint for `adjust`.

### `ReplyKeyboard`

```python
from t8ot import ReplyKeyboard

keyboard = (
    ReplyKeyboard(placeholder="Pick one...", resize_keyboard=True)
    .button("Share contact", request_contact=True)
    .button("Share location", request_location=True)
    .row()
    .button("Cancel")
    .build()
)

await ctx.reply("What should I do?", reply_markup=keyboard)
```

`button(text, request_contact=False, request_location=False, web_app_url=None)`.

### Removing a keyboard

```python
from t8ot import remove_keyboard

await ctx.reply("Cancelled.", reply_markup=remove_keyboard())
```

---

← [Routing](routing.md) · Next: [FSM & Storage](fsm-and-storage.md)