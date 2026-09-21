import asyncio
import uvicorn
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, MenuButtonWebApp

from .config import get_config
from .db import Database
from .api import app

config = get_config()
db = Database(config.database_path)
router = Router()

@router.message(CommandStart())
async def start(message: Message):
    u = message.from_user
    db.upsert_user(u.id, u.username, u.first_name or "User")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🚀 Открыть LynoraVPN",
            web_app=WebAppInfo(url=config.mini_app_url)
        )
    ]])
    await message.answer(
        "Добро пожаловать в LynoraVPN!\n\nОткройте приложение, чтобы управлять подпиской.",
        reply_markup=keyboard
    )

async def run():
    bot = Bot(config.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="LynoraVPN", web_app=WebAppInfo(url=config.mini_app_url))
    )

    server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info"))
    await asyncio.gather(
        dp.start_polling(bot),
        server.serve()
    )

if __name__ == "__main__":
    asyncio.run(run())
