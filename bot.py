#!/usr/bin/env python3
import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_config
from app.services.suno_playwright import get_client
from app.handlers.start import register_start_handlers
from app.handlers.generate import register_generate_handlers
from app.utils.notify_admin import notify_admin, notify_admin_error, close_notification_bot
from app.utils.cleanup import cleanup_task


def setup_logging(level: int = logging.INFO) -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S")
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console)
    logging.getLogger("aiogram").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)
_cleanup_task_handle = None


async def init_suno() -> None:
    client = await get_client()
    await client.init()
    logger.info("Suno client initialized")


async def on_startup():
    logger.info("Bot starting")
    await init_suno()
    await notify_admin("Bot started")


async def on_shutdown():
    logger.info("Bot stopping")
    global _cleanup_task_handle
    if _cleanup_task_handle:
        _cleanup_task_handle.cancel()
    await close_notification_bot()
    logger.info("Bot stopped")


async def main() -> None:
    setup_logging()
    logger.info("Starting Music Bot")
    
    config = load_config()
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    register_start_handlers(dp)
    register_generate_handlers(dp)
    
    await on_startup()
    
    global _cleanup_task_handle
    _cleanup_task_handle = asyncio.create_task(cleanup_task(interval_minutes=30, max_age_hours=1))
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped")
    except Exception as e:
        logger.critical(f"Fatal: {e}", exc_info=True)
        sys.exit(1)
