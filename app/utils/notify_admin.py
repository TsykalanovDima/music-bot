# app/utils/notify_admin.py
"""Utility for sending notifications to bot admin"""

import logging
from aiogram import Bot
from app.config import load_config

logger = logging.getLogger(__name__)

_notification_bot = None


def get_notification_bot() -> Bot:
    """Get bot instance for notifications"""
    global _notification_bot

    if _notification_bot is None:
        config = load_config()
        _notification_bot = Bot(token=config.bot_token, parse_mode="HTML")

    return _notification_bot


async def notify_admin(text: str) -> bool:
    """Send notification to admin"""
    try:
        config = load_config()

        if not config.admin_id or config.admin_id == 0:
            logger.warning("ADMIN_ID not set. Notification skipped.")
            return False

        bot = get_notification_bot()
        await bot.send_message(chat_id=config.admin_id, text=text, parse_mode="HTML")
        return True

    except Exception as e:
        logger.error(f"Failed to notify admin: {e}", exc_info=True)
        return False


async def notify_admin_error(error: Exception, context: str = "", user_id: int = None) -> bool:
    """Send error notification to admin"""
    error_text = f"<b>Error:</b> {type(error).__name__}\n"
    error_text += f"<b>Message:</b> {str(error)}\n"

    if context:
        error_text += f"<b>Context:</b> {context}\n"

    if user_id:
        error_text += f"<b>User ID:</b> {user_id}\n"

    return await notify_admin(error_text)


async def close_notification_bot():
    """Close bot session for notifications"""
    global _notification_bot

    if _notification_bot:
        try:
            await _notification_bot.session.close()
            _notification_bot = None
        except Exception as e:
            logger.error(f"Error closing notification bot: {e}")