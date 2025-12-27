#!/usr/bin/env python3
"""
Automatic Suno Session Saver
1. Opens browser on suno.com
2. You login manually
3. Press ENTER
4. Automatically finds and saves __client cookie to .env
"""
import asyncio
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright not installed!")
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))


async def save_suno_session():
    print("\n" + "=" * 60)
    print("🎵 SUNO SESSION SAVER".center(60))
    print("=" * 60)
    
    async with async_playwright() as p:
        print("\n🌐 Launching Chromium browser...")
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        print("📍 Opening https://suno.com ...")
        await page.goto('https://suno.com', wait_until='domcontentloaded')
        await asyncio.sleep(2)
        
        print("\n" + "=" * 60)
        print("=" * 60)
        print("1. Login to your Suno account in the browser")
        print("2. Wait until you see the main page")
        print("3. Press ENTER in this terminal")
        print("=" * 60)
        
        input("\nPress ENTER after login >>> ")
        
        print("\n🔍 Extracting cookies...")
        cookies = await context.cookies()
        
        client_cookie = None
        all_cookies_text = ""
        
        for cookie in cookies:
            name = cookie.get('name', '')
            value = cookie.get('value', '')
            
            # Build full cookie string
            all_cookies_text += f"{name}={value}; "
            
            if name == '__client':
                client_cookie = value
                print(f"Found __client cookie: {value[:50]}...")
        
        if client_cookie:
            print(f"\nSUCCESS! Cookie length: {len(client_cookie)} chars")
            
            # Update .env file
            env_file = Path('.env')
            
            if env_file.exists():
                content = env_file.read_text()
                lines = content.split('\n')
                updated = False
                
                for i, line in enumerate(lines):
                    if line.startswith('SUNO_COOKIE='):
                        lines[i] = f'SUNO_COOKIE="{all_cookies_text.strip()}"'
                        updated = True
                        break
                
                if not updated:
                    lines.append(f'SUNO_COOKIE="{all_cookies_text.strip()}"')
                
                env_file.write_text('\n'.join(lines))
            else:
                env_file.write_text(f'SUNO_COOKIE="{all_cookies_text.strip()}"\n')
            
            print(f"✅ Saved to .env file")
            print(f"\n📋 Full cookie string saved ({len(all_cookies_text)} chars)")
        else:
            print("\n❌ ERROR: __client cookie not found!")
            print("Make sure you're fully logged in to Suno")
            print("\nAll cookies found:")
            for cookie in cookies:
                print(f"  - {cookie.get('name')}")
        
        print("\n🔒 Closing browser...")
        await browser.close()
        
        if client_cookie:
            print("\n" + "=" * 60)
            print("✅ ALL DONE!".center(60))
            print("=" * 60)
            print("You can now run: python bot.py")
            print("=" * 60 + "\n")
        else:
            print("\n⚠️  Please try again and make sure you're logged in")
            sys.exit(1)


if __name__ == '__main__':
    try:
        asyncio.run(save_suno_session())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
