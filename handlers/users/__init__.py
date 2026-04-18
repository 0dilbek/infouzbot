from aiogram import Router

from handlers.users.search import router as search_router
from handlers.users.start import router as start_router

router = Router()
router.include_router(search_router)
router.include_router(start_router)
