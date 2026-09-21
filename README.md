# LynoraVPN Telegram Bot + Mini App

Минимальный production-ready каркас для Telegram Mini App:
- aiogram 3
- FastAPI
- SQLite
- Telegram WebApp initData validation
- кнопка "Открыть LynoraVPN"
- профиль пользователя сохраняется в БД

## 1. Установка

Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

Скопируйте `.env.example` в `.env` и заполните:

```env
BOT_TOKEN=...
MINI_APP_URL=https://ваш-домен/app/
DATABASE_PATH=./database/lynora.db
```

Токен BotFather хранится только в `.env` и не попадает в HTML.

## 2. Запуск

В одном процессе запускаются FastAPI и Telegram polling:

```bash
python -m bot.main
```

По умолчанию API слушает `0.0.0.0:8000`.

Для локальной разработки Mini App нужен HTTPS URL. Можно использовать Cloudflare Tunnel/ngrok или публичный VPS.

## 3. Важно для Telegram

Mini App URL должен быть публичным HTTPS URL. В `.env` укажите его, например:

`https://example.com/app/`

При старте бот устанавливает кнопку меню `LynoraVPN`.

## 4. Что уже работает

- /start
- кнопка открытия Mini App
- регистрация Telegram пользователя
- серверная проверка Telegram WebApp initData
- профиль
- баланс
- подписка-заглушка
- реферальная ссылка
- тикеты
- демо-промокоды
- SQLite

## 5. Что подключать следующим этапом

- реальная оплата
- настоящие тарифы и даты окончания
- серверная логика промокодов
- реферальные начисления
- VPN backend / WireGuard
- админ-панель
- история платежей


## Telegram Stars payments
The project now contains a server-side 30-day subscription payment flow using Telegram Stars (XTR). Set `SUBSCRIPTION_STARS` in Render to a positive integer to enable the Pay button. Keep it at `0` while configuring the project.

A successful payment is verified by currency, amount, payload and Telegram charge ID before 30 days are added to the user's subscription. Telegram requires digital goods/services in Telegram apps to use Stars.


## Telegram Stars payments
The project contains a server-side 30-day subscription payment flow using Telegram Stars (XTR). Set `SUBSCRIPTION_STARS` in Render to a positive integer to enable the Pay button. Keep it at `0` while configuring the project.


## Безопасный тест подписки
Для теста без списания Stars задайте в Render `TEST_TELEGRAM_ID` равным вашему Telegram ID. Тогда только этот аккаунт увидит кнопку тестовой активации на 30 дней. Перед запуском для пользователей удалите/обнулите `TEST_TELEGRAM_ID`.
