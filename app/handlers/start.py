import logging
from aiogram import types, Router, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🎵 Create song")]],
        resize_keyboard=True
    )
    
    await message.answer(
        "👋 Hi! I can create unique songs using AI.\n\n"
        "👇 Press the button below to start:",
        reply_markup=keyboard
    )


def register_start_handlers(dp):
    dp.include_router(router)
