from typing import List, Optional, Union
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    WebAppInfo,
)


class InlineKeyboard:
    """Fluent builder for Telegram InlineKeyboardMarkup."""

    def __init__(self, row_width: int = 3):
        self.row_width = row_width
        self._rows: List[List[InlineKeyboardButton]] = [[]]

    def button(
        self,
        text: str,
        callback_data: Optional[str] = None,
        url: Optional[str] = None,
        web_app_url: Optional[str] = None,
        switch_inline_query: Optional[str] = None,
    ) -> "InlineKeyboard":
        """Adds an inline button to the current row."""
        web_app = WebAppInfo(url=web_app_url) if web_app_url else None
        btn = InlineKeyboardButton(
            text=text,
            callback_data=callback_data or text,
            url=url,
            web_app=web_app,
            switch_inline_query=switch_inline_query,
        )
        self._rows[-1].append(btn)
        return self

    def row(self) -> "InlineKeyboard":
        """Breaks and moves to a new row."""
        if self._rows[-1]:
            self._rows.append([])
        return self

    def adjust(self, count: int) -> "InlineKeyboard":
        """Refactors all buttons into rows of fixed size."""
        all_buttons = [btn for row in self._rows for btn in row]
        self._rows = [
            all_buttons[i : i + count] for i in range(0, len(all_buttons), count)
        ]
        if not self._rows:
            self._rows = [[]]
        return self

    def build(self) -> InlineKeyboardMarkup:
        """Compiles buttons into telebot InlineKeyboardMarkup."""
        markup = InlineKeyboardMarkup()
        for row in self._rows:
            if row:
                markup.row(*row)
        return markup


class ReplyKeyboard:
    """Fluent builder for Telegram ReplyKeyboardMarkup."""

    def __init__(
        self,
        resize_keyboard: bool = True,
        one_time_keyboard: bool = False,
        selective: bool = False,
        placeholder: Optional[str] = None,
    ):
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard
        self.selective = selective
        self.placeholder = placeholder
        self._rows: List[List[KeyboardButton]] = [[]]

    def button(
        self,
        text: str,
        request_contact: bool = False,
        request_location: bool = False,
        web_app_url: Optional[str] = None,
    ) -> "ReplyKeyboard":
        """Adds a reply button to the current row."""
        web_app = WebAppInfo(url=web_app_url) if web_app_url else None
        btn = KeyboardButton(
            text=text,
            request_contact=request_contact,
            request_location=request_location,
            web_app=web_app,
        )
        self._rows[-1].append(btn)
        return self

    def row(self) -> "ReplyKeyboard":
        """Breaks and moves to a new row."""
        if self._rows[-1]:
            self._rows.append([])
        return self

    def adjust(self, count: int) -> "ReplyKeyboard":
        """Refactors all buttons into rows of fixed size."""
        all_buttons = [btn for row in self._rows for btn in row]
        self._rows = [
            all_buttons[i : i + count] for i in range(0, len(all_buttons), count)
        ]
        if not self._rows:
            self._rows = [[]]
        return self

    def build(self) -> ReplyKeyboardMarkup:
        """Compiles buttons into telebot ReplyKeyboardMarkup."""
        markup = ReplyKeyboardMarkup(
            resize_keyboard=self.resize_keyboard,
            one_time_keyboard=self.one_time_keyboard,
            selective=self.selective,
            input_field_placeholder=self.placeholder,
        )
        for row in self._rows:
            if row:
                markup.row(*row)
        return markup


def remove_keyboard(selective: bool = False) -> ReplyKeyboardRemove:
    """Helper to remove custom reply keyboards."""
    return ReplyKeyboardRemove(selective=selective)