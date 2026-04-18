from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, InlineQuery, Message

from config import ADMIN_IDS
from modles.locations import User


class IsAdmin(BaseFilter):
    """
    Passes if the user's Telegram ID is in ADMIN_IDS (config/.env)
    OR their role is "admin" in the database.
    ADMIN_IDS check is instant (no DB); DB role check is the fallback.
    """

    async def __call__(
        self, event: Union[Message, CallbackQuery, InlineQuery]
    ) -> bool:
        tg_id = event.from_user.id

        # Fast path: ID whitelist
        if tg_id in ADMIN_IDS:
            return True

        # DB role check
        user = await User.filter(tg_id=tg_id).first()
        return user is not None and user.role == "admin"
