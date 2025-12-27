# app/config.py
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


@dataclass
class Config:
    bot_token: str
    suno_cookie: str
    admin_id: int
    max_prompt_length: int = 400
    google_speech_api_key: str = ""


def load_config() -> Config:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    suno_cookie = os.getenv("SUNO_COOKIE")
    admin_id = int(os.getenv("ADMIN_ID", "0"))
    max_prompt_length = int(os.getenv("MAX_PROMPT_LENGTH", "400"))
    google_speech_api_key = os.getenv("GOOGLE_SPEECH_API_KEY", "")

    if not bot_token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN or BOT_TOKEN not found in .env file!\n"
            "Add: TELEGRAM_BOT_TOKEN=your_token"
        )

    if not suno_cookie:
        raise ValueError(
            "SUNO_COOKIE not found in .env file!\n"
            "Add: SUNO_COOKIE=your_cookie"
        )

    return Config(
        bot_token=bot_token,
        suno_cookie=suno_cookie,
        admin_id=admin_id,
        max_prompt_length=max_prompt_length,
        google_speech_api_key=google_speech_api_key,
    )


def get_config() -> Config:
    return load_config()
