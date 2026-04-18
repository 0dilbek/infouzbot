from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(
            text="🔍 Qidirish",
            switch_inline_query_current_chat="",
        )
    )

    await message.answer(
        f"Salom, <b>{message.from_user.first_name}</b>! Botimizga xush kelibsiz.",
        parse_mode="HTML",
        reply_markup=b.as_markup(),
    )
