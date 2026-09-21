import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    bot_token: str
    mini_app_url: str
    database_path: str

def get_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    url = os.getenv("MINI_APP_URL", "").strip()
    db = os.getenv("DATABASE_PATH", "./database/lynora.db").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is not set. Copy .env.example to .env and add your BotFather token.")
    if not url.startswith("https://"):
        raise RuntimeError("MINI_APP_URL must be a public HTTPS URL.")
    return Config(token, url.rstrip("/") + "/", db)
