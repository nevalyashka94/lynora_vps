import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    bot_token: str
    mini_app_url: str
    database_path: str
    subscription_stars: int
    test_telegram_id: int

def get_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    url = os.getenv("MINI_APP_URL", "").strip()
    db = os.getenv("DATABASE_PATH", "./database/lynora.db").strip()
    stars_raw = os.getenv("SUBSCRIPTION_STARS", "0").strip()
    try:
        stars = int(stars_raw)
    except ValueError:
        raise RuntimeError("SUBSCRIPTION_STARS must be an integer.")
    if stars < 0 or stars > 10000:
        raise RuntimeError("SUBSCRIPTION_STARS must be between 0 and 10000.")
    test_id_raw = os.getenv("TEST_TELEGRAM_ID", "0").strip()
    try:
        test_id = int(test_id_raw) if test_id_raw else 0
    except ValueError:
        raise RuntimeError("TEST_TELEGRAM_ID must be an integer.")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set. Copy .env.example to .env and add your BotFather token.")
    if not url.startswith("https://"):
        raise RuntimeError("MINI_APP_URL must be a public HTTPS URL.")
    return Config(token, url.rstrip("/") + "/", db, stars, test_id)
