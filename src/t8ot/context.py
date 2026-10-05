from typing import Optional, Union, Any, Dict, TYPE_CHECKING
from telebot.types import Chat, Message, CallbackQuery, InlineQuery, User

try:  # The exception class was renamed across pyTelegramBotAPI releases.
    from telebot.asyncio_helper import ApiException as TelegramAPIError
except ImportError:  # pyTelegramBotAPI < 4.2x
    from telebot.asyncio_helper import APIError as TelegramAPIError

if TYPE_CHECKING:
    from .app import Bot


class Context:
    """Encapsulates different Telegram events into a unified interface."""

    def __init__(self, bot: "Bot", event: Union[Message, CallbackQuery, InlineQuery]):
        self.app = bot
        self.bot = bot.bot  # AsyncTeleBot client instance
        self.raw_event = event
        # Free-form scratchpad shared between middlewares and the handler.
        self.extra: Dict[str, Any] = {}

        if isinstance(event, CallbackQuery):
            self.message: Optional[Message] = event.message
            self.user: User = event.from_user
            self.chat_id: int = event.message.chat.id if event.message else event.from_user.id
            self.data: Optional[str] = event.data
            self.is_callback: bool = True
            self.is_inline: bool = False
        elif isinstance(event, InlineQuery):
            self.message: Optional[Message] = None
            self.user: User = event.from_user
            self.chat_id: int = event.from_user.id
            self.query: str = event.query
            self.is_callback: bool = False
            self.is_inline: bool = True
        else:
            self.message: Optional[Message] = event
            self.user: User = event.from_user
            self.chat_id: int = event.chat.id
            self.data: Optional[str] = None
            self.is_callback: bool = False
            self.is_inline: bool = False

    @property
    def text(self) -> Optional[str]:
        """Returns the text of the message if available."""
        return self.message.text if self.message else None

    @property
    def value(self) -> Any:
        """Extracts the primary payload (text, phone_number from contact, etc.)."""
        if not self.message:
            return None
        if self.message.contact:
            return self.message.contact.phone_number
        if self.message.location:
            return self.message.location
        return self.message.text

    @property
    def chat(self) -> Optional[Chat]:
        """The chat the event belongs to, or None for inline queries."""
        return self.message.chat if self.message else None

    async def reply(self, text: str, **kwargs) -> Message:
        """Sends a response message to the current chat."""
        return await self.bot.send_message(self.chat_id, text, **kwargs)

    async def reply_photo(
        self, photo: Any, caption: Optional[str] = None, **kwargs
    ) -> Message:
        """Sends a photo (file_id, URL or file object) to the current chat."""
        return await self.bot.send_photo(self.chat_id, photo, caption=caption, **kwargs)

    async def reply_document(
        self, document: Any, caption: Optional[str] = None, **kwargs
    ) -> Message:
        """Sends a document/file to the current chat."""
        return await self.bot.send_document(
            self.chat_id, document, caption=caption, **kwargs
        )

    async def reply_video(
        self, video: Any, caption: Optional[str] = None, **kwargs
    ) -> Message:
        """Sends a video (file_id, URL or file object) to the current chat."""
        return await self.bot.send_video(self.chat_id, video, caption=caption, **kwargs)

    async def delete(self) -> bool:
        """Deletes the current message.

        Returns False when there is nothing to delete or Telegram refuses
        (e.g. messages older than 48 hours are rejected).
        """
        if not self.message:
            return False
        try:
            return bool(
                await self.bot.delete_message(self.chat_id, self.message.message_id)
            )
        except TelegramAPIError:
            return False

    async def answer(self, text: Optional[str] = None, show_alert: bool = False):
        """Acknowledges a callback query notification."""
        if self.is_callback:
            return await self.bot.answer_callback_query(
                callback_query_id=self.raw_event.id,
                text=text,
                show_alert=show_alert,
            )

    async def edit(self, text: str, **kwargs):
        """Edits the existing message in a callback context."""
        if self.is_callback and self.message:
            return await self.bot.edit_message_text(
                text=text,
                chat_id=self.chat_id,
                message_id=self.message.message_id,
                **kwargs,
            )
        raise RuntimeError("Edit only works in callback queries or on editable messages.")

    async def edit_text(self, text: str, **kwargs):
        """Edits the current message, whatever the event type is."""
        if not self.message:
            raise RuntimeError("Nothing to edit: this event carries no message.")
        return await self.bot.edit_message_text(
            text=text,
            chat_id=self.chat_id,
            message_id=self.message.message_id,
            **kwargs,
        )

    @property
    def state_data(self) -> Dict[str, Any]:
        """Returns all collected data for current user in active flow."""
        return self.app.storage.get_data(self.user.id)

    async def cancel_flow(self):
        """Cancels any active interactive flow for this user."""
        await self.app.cancel_user_flow(self)