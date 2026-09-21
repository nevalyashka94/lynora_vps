import json
from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from aiogram import Bot
from aiogram.types import LabeledPrice

from .config import get_config
from .db import Database
from .telegram_auth import validate_init_data

config = get_config()
db = Database(config.database_path)

app = FastAPI(title="LynoraVPN API")
app.mount("/app", StaticFiles(directory="web", html=True), name="app")

class InitDataBody(BaseModel):
    initData: str

class TicketBody(BaseModel):
    text: str

class PromoBody(BaseModel):
    code: str

class InvoiceBody(BaseModel):
    initData: str


def auth_user(init_data: str):
    try:
        data = validate_init_data(init_data, config.bot_token)
        user = json.loads(data["user"])
        db.upsert_user(user["id"], user.get("username"), user.get("first_name") or "User")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/")
async def root():
    return {"ok": True, "service": "LynoraVPN", "mini_app": config.mini_app_url}

@app.post("/api/auth")
async def auth(body: InitDataBody):
    user = auth_user(body.initData)
    row = db.get_user(user["id"])
    return {"user": row, "subscription_stars": config.subscription_stars, "test_mode": config.test_telegram_id > 0 and user["id"] == config.test_telegram_id}

@app.get("/api/me")
async def me(x_telegram_init_data: str = Header(default="")):
    user = auth_user(x_telegram_init_data)
    return {"user": db.get_user(user["id"]), "subscription_stars": config.subscription_stars, "test_mode": config.test_telegram_id > 0 and user["id"] == config.test_telegram_id}

@app.post("/api/invoice")
async def invoice(body: InvoiceBody):
    user = auth_user(body.initData)
    if config.subscription_stars <= 0:
        raise HTTPException(status_code=503, detail="Оплата пока не настроена: укажите SUBSCRIPTION_STARS в Render.")
    payload = f"vpn30:{user['id']}"
    async with Bot(config.bot_token) as bot:
        link = await bot.create_invoice_link(
            title="LynoraVPN — 30 дней",
            description="Доступ к VPN на 30 дней.",
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label="30 дней", amount=config.subscription_stars)]
        )
    return {"ok": True, "invoice_url": link, "stars": config.subscription_stars}


@app.post("/api/test-subscription")
async def test_subscription(body: InitDataBody):
    user = auth_user(body.initData)
    if not config.test_telegram_id or user["id"] != config.test_telegram_id:
        raise HTTPException(status_code=403, detail="Тестовый режим отключён для этого пользователя.")
    now = datetime.now(timezone.utc)
    current = db.get_user(user["id"]) or {}
    old = current.get("subscription_expires_at")
    try:
        old_dt = datetime.fromisoformat(old) if old else None
        if old_dt and old_dt.tzinfo is None:
            old_dt = old_dt.replace(tzinfo=timezone.utc)
    except ValueError:
        old_dt = None
    base = old_dt if old_dt and old_dt > now else now
    expires = base + timedelta(days=30)
    db.activate_subscription(user["id"], expires.isoformat())
    return {"ok": True, "expires_at": expires.isoformat(), "user": db.get_user(user["id"])}

@app.get("/api/tickets")
async def tickets(x_telegram_init_data: str = Header(default="")):
    user = auth_user(x_telegram_init_data)
    return {"tickets": db.get_tickets(user["id"])}

@app.post("/api/tickets")
async def create_ticket(body: TicketBody, x_telegram_init_data: str = Header(default="")):
    user = auth_user(x_telegram_init_data)
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Ticket text is empty")
    ticket_id = db.add_ticket(user["id"], text)
    return {"ok": True, "id": ticket_id}

@app.post("/api/promo")
async def promo(body: PromoBody, x_telegram_init_data: str = Header(default="")):
    user = auth_user(x_telegram_init_data)
    bonuses = {"PROMO50": 50, "PROMO100": 100, "VIP25": 25, "WELCOME75": 75}
    code = body.code.strip().upper()
    amount = bonuses.get(code)
    if not amount:
        raise HTTPException(status_code=400, detail="Промокод не найден")
    balance = db.add_balance(user["id"], amount)
    return {"ok": True, "amount": amount, "balance": balance}
