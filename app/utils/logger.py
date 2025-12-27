# app/utils/logger.py
"""
Simple logging helper for song orders.
"""
from __future__ import annotations

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


def _ensure_logs_dir() -> Path:
    path = Path("logs")
    path.mkdir(exist_ok=True)
    return path


def log_song_order(*, user_id: int, username: str, lang: str, credits_before: int, prompt: str) -> None:
    """Log a song order both to the logger and to `logs/song_orders.csv`.

    Args:
        user_id: Telegram user id
        username: Telegram username (may be empty)
        lang: User language
        credits_before: Credits before the order
        prompt: Prompt text
    """
    ts = datetime.utcnow().isoformat()
    msg = f"Order: user={user_id} username={username!s} lang={lang} credits_before={credits_before} prompt={prompt[:100]!s}"
    logger.info(msg)

    logs_dir = _ensure_logs_dir()
    csv_path = logs_dir / "song_orders.csv"

    try:
        with csv_path.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow([ts, user_id, username, lang, credits_before, prompt])
    except Exception as e:
        logger.error(f"Failed to write song order to CSV: {e}")
