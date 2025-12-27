# app/services/suno_playwright.py
"""
Suno automation using Playwright.
Simple flow: prompt → wait 130s → download 2 tracks
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import List, Optional

from app.config import load_config

try:
    from playwright.async_api import async_playwright, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)
CONFIG = load_config()
BROWSER_STATE_DIR = Path("data") / "browser_state"
MP3_TIMEOUT = 120
DOWNLOAD_TIMEOUT = 120


def should_run_headless() -> bool:
    """Headless if HEADLESS=true or no DISPLAY."""
    headless_env = os.getenv("HEADLESS", "").lower()
    if headless_env in ["true", "1", "yes"]:
        return True
    if headless_env in ["false", "0", "no"]:
        return False
    return "DISPLAY" not in os.environ


class SunoPlaywrightClient:
    """Suno automation client."""

    def __init__(self):
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page = None
        self.initialized = False
        self.download_folder = Path("downloads")
        self.download_folder.mkdir(exist_ok=True)
        self.headless = should_run_headless()
        BROWSER_STATE_DIR.mkdir(parents=True, exist_ok=True)

    async def init(self):
        """Launch browser and load cookies."""
        if self.initialized:
            return

        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed")

        logger.info(f"Starting browser (headless={self.headless})")

        self.playwright = await async_playwright().start()
        
        args = ["--disable-blink-features=AutomationControlled"]
        if self.headless:
            args.extend(["--no-sandbox", "--disable-setuid-sandbox"])

        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_STATE_DIR),
            headless=self.headless,
            viewport={"width": 1280, "height": 800},
            args=args,
        )
        
        if CONFIG.suno_cookie:
            cookies = []
            for part in CONFIG.suno_cookie.split(";"):
                if "=" not in part:
                    continue
                name, value = part.split("=", 1)
                cookies.append({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".suno.com",
                    "path": "/",
                })
            await self.context.add_cookies(cookies)
            logger.info(f"Loaded {len(cookies)} cookies")

        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        
        await self.page.goto("https://suno.com/create", wait_until="load", timeout=30000)
        await asyncio.sleep(3 if self.headless else 5)
        
        self.initialized = True
        logger.info("Browser ready")


    async def _enter_prompt_and_create(self, prompt: str):
        """Enter prompt and click Create."""
        textarea = self.page.locator('textarea[placeholder*="song"]').first
        await textarea.wait_for(timeout=5000)
        await textarea.click()
        await textarea.fill(prompt)
        
        create_btn = self.page.locator('button[aria-label="Create song"]').first
        await create_btn.wait_for(timeout=3000)
        await create_btn.click()
        logger.info("Prompt submitted")

    async def download_latest_tracks(self, count: int = 2, start_index: int = 0) -> List[str]:
        """Download tracks starting from start_index."""
        logger.info(f"Downloading {count} tracks from position {start_index}")
        
        rows = self.page.locator("div[role='row']")
        await rows.first.wait_for(timeout=2000)
        total = await rows.count()
        
        if total == 0:
            logger.error("No tracks found")
            return []
        
        saved = []
        for idx in range(start_index, min(start_index + count, total)):
            row = rows.nth(idx)
            await row.scroll_into_view_if_needed()
            await row.wait_for(state="visible", timeout=4000)

            # Click menu button (три точки)
            more_btn = row.locator("button").filter(has=self.page.locator("svg")).last
            await more_btn.wait_for(state="visible", timeout=3000)
            await more_btn.click()
            logger.info(f"Track {idx + 1} menu opened")
            await asyncio.sleep(0.5)
            
            # Click Download from context menu
            download_btn = self.page.locator("button:has-text('Download')").first
            await download_btn.wait_for(timeout=3000)
            await download_btn.click()
            logger.info(f"Track {idx + 1} download clicked")
            await asyncio.sleep(0.5)
            
            # Click MP3 Audio button
            mp3_btn = self.page.locator("button[aria-label='MP3 Audio']").first
            await mp3_btn.wait_for(timeout=5000)
            
            # Wait until MP3 is enabled
            start_time = asyncio.get_event_loop().time()
            while True:
                if await mp3_btn.is_enabled():
                    break
                if asyncio.get_event_loop().time() - start_time > MP3_TIMEOUT:
                    logger.error(f"Track {idx + 1} MP3 not ready")
                    await self.page.keyboard.press("Escape")
                    continue
                await asyncio.sleep(2)
            
            await mp3_btn.click()
            logger.info(f"Track {idx + 1} MP3 selected")
            await asyncio.sleep(0.5)
            
            # Download file
            try:
                async with self.page.expect_download(timeout=DOWNLOAD_TIMEOUT * 1000) as dl_info:
                    # Click "Download Anyway"
                    anyway_btn = self.page.locator("button:has-text('Download Anyway')").first
                    await anyway_btn.wait_for(timeout=2000)
                    await anyway_btn.click()
                    logger.info(f"Track {idx + 1} download anyway clicked")
                
                download = await dl_info.value
                filename = self.download_folder / f"track_{idx + 1}_{int(asyncio.get_event_loop().time())}.mp3"
                await download.save_as(str(filename))
                saved.append(str(filename))
                logger.info(f"Track {idx + 1} saved")
            except Exception as e:
                logger.error(f"Download failed for track {idx + 1}: {e}")
            
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
        
        return saved

    async def generate_song(self, prompt: str, wait_timeout: int = 130) -> Optional[List[str]]:
        """Generate and download tracks."""
        await self.init()
        # For manual download testing we skip creating a new song from the prompt.
        await self._enter_prompt_and_create(prompt)
        logger.info(f"Waiting {wait_timeout}s for generation...")
        await asyncio.sleep(wait_timeout)
        
        files = await self.download_latest_tracks(count=2, start_index=2)
        return files if files else None

    async def close(self):
        """Close browser."""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
        self.initialized = False


# Singleton

_client: Optional[SunoPlaywrightClient] = None


async def get_client() -> SunoPlaywrightClient:
    global _client
    if _client is None:
        _client = SunoPlaywrightClient()
    return _client


async def generate_song_async(prompt: str) -> Optional[List[str]]:
    """Generate song and return downloaded files."""
    client = await get_client()
    return await client.generate_song(prompt)
