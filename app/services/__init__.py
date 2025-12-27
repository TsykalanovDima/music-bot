# app/services/__init__.py

# Suno Playwright (primary method)
try:
    from .suno_playwright import (
        generate_song_sync,
        is_playwright_available,
        SunoPlaywrightClient,
        get_client
    )
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    generate_song_sync = None
    is_playwright_available = lambda: False
    SunoPlaywrightClient = None
    get_client = None

# Legacy API method (may not work due to 503 errors)
try:
    from .suno_client import generate_simple_song
except ImportError:
    generate_simple_song = None

__all__ = [
    # Credits
    'has_credits',
    'consume_credit',
    'add_credits',
    # Playwright
    'generate_song_sync',
    'is_playwright_available',
    'SunoPlaywrightClient',
    'get_client',
    'PLAYWRIGHT_AVAILABLE',
    # API
    'generate_simple_song',
]