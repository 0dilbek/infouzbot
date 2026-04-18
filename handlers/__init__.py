from aiogram import Dispatcher

from handlers.admins import router as admin_router
from handlers.users import router as user_router


def register_all_handlers(dp: Dispatcher):
    dp.include_router(admin_router)
    dp.include_router(user_router)
