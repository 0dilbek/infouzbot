from aiogram import Router

from filters import IsAdmin
from handlers.admins.start import router as start_router
from handlers.admins.add_location import router as add_location_router

# /start is open to everyone; the add-location flow is admin-only.
add_location_router.message.filter(IsAdmin())
add_location_router.callback_query.filter(IsAdmin())
add_location_router.inline_query.filter(IsAdmin())

router = Router()
router.include_router(start_router)
router.include_router(add_location_router)
