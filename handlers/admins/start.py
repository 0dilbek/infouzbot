from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.admin_kb import admin_main_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"Salom, <b>{message.from_user.first_name}</b>! Admin panelga xush kelibsiz.",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )
