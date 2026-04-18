from asyncio import run

from aiogram import Bot, Dispatcher
from tortoise import Tortoise

from config import BOT_TOKEN
from handlers import register_all_handlers
from modles import init as init_db

import logging

dp = Dispatcher()


async def main():
    bot = Bot(token=BOT_TOKEN)

    await init_db()

    register_all_handlers(dp)

    try:
        await dp.start_polling(bot)
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run(main())
