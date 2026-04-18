from aiogram import Router

from handlers.users.search import router as search_router

router = Router()
router.include_router(search_router)
