import asyncio
from datetime import datetime, timedelta, timezone
import uvicorn
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, MenuButtonWebApp, PreCheckoutQuery

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

@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    payload = query.invoice_payload
    valid = (
        config.subscription_stars > 0
        and query.currency == "XTR"
        and query.total_amount == config.subscription_stars
        and payload == f"vpn30:{query.from_user.id}"
    )
    await query.answer(ok=valid, error_message=None if valid else "Платёж недействителен. Откройте оплату заново.")

@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment
    user_id = message.from_user.id
    if payment.currency != "XTR" or payment.total_amount != config.subscription_stars:
        await message.answer("Платёж получен, но его параметры не совпали с тарифом. Обратитесь в поддержку.")
        return
    if db.has_payment(payment.telegram_payment_charge_id):
        await message.answer("Этот платёж уже обработан.")
        return
    payload = payment.invoice_payload
    if payload != f"vpn30:{user_id}":
        await message.answer("Платёж не удалось привязать к вашему аккаунту. Обратитесь в поддержку.")
        return

    now = datetime.now(timezone.utc)
    current = db.get_user(user_id) or {}
    old = current.get("subscription_expires_at")
    try:
        old_dt = datetime.fromisoformat(old) if old else None
        if old_dt and old_dt.tzinfo is None:
            old_dt = old_dt.replace(tzinfo=timezone.utc)
    except ValueError:
        old_dt = None
    base = old_dt if old_dt and old_dt > now else now
    expires = base + timedelta(days=30)
    db.add_payment(user_id, payment.telegram_payment_charge_id, payment.total_amount, payload)
    db.activate_subscription(user_id, expires.isoformat())
    await message.answer(
        f"✅ Оплата получена!\n\nПодписка LynoraVPN активна до {expires.strftime('%d.%m.%Y %H:%M UTC')}."
    )

@router.message(Command("paysupport"))
async def pay_support(message: Message):
    await message.answer("По вопросам оплаты напишите в поддержку через раздел «Поддержка» в LynoraVPN.")

@router.message(Command("terms"))
async def terms(message: Message):
    await message.answer("Условия использования и правила возврата будут опубликованы перед запуском платных подписок.")

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
