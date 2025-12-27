# Suno Music Bot

Telegram bot that generates AI music using Suno.com via browser automation (Playwright).

## Features

- Generate unique songs from text prompts
- Voice message support with Google Speech API transcription
- Download 2 tracks per generation
- Automatic cleanup of old files
- Persistent browser session
- Admin notifications

## Important: Suno Subscription

**Free Suno Account:**
- Bot downloads tracks at positions **3 and 4** in your library
- This avoids downloading preview-only tracks (1-2)
- Requires at least 4 existing tracks in your Suno library

**Paid Suno Subscription:**
- Bot can download tracks at positions **1 and 2** (newest)
- Full tracks available immediately
- To change: edit `start_index=2` to `start_index=0` in [app/services/suno_playwright.py](app/services/suno_playwright.py#L191) line 191

## Requirements

- Python 3.11+
- Telegram Bot Token
- Suno.com account with active session
- ffmpeg (for audio format conversion)

## Installation

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd music-bot
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Install FFmpeg

FFmpeg is required to convert voice messages (OGG) to FLAC format for Google Speech API.

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Configuration

### 1. Get Telegram Bot Token

1. Open Telegram and find [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Copy the bot token

### 2. Extract Suno Session Cookie

**Method 1: Using Browser DevTools**

1. Open [suno.com](https://suno.com) and login
2. Open DevTools (F12)
3. Go to Application → Cookies → https://suno.com
4. Copy all cookies in format: `name1=value1; name2=value2; ...`

**Method 2: Using save_suno_session.py Script**

```bash
python save_suno_session.py
```

This will:
- Open browser window
- Wait for you to login to Suno
- Automatically extract cookies
- Save to `.env` file

### 3. Create .env File

Create `.env` file in project root:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_user_id

# Suno Configuration
SUNO_COOKIE=cookie1=value1; cookie2=value2; ...

# Optional Settings
MAX_PROMPT_LENGTH=400
HEADLESS=false
```

**Get your Telegram User ID:**
- Start chat with [@userinfobot](https://t.me/userinfobot)
- It will show your user ID

## Running the Bot

### Development (with visible browser)

```bash
source venv/bin/activate
python bot.py
```

Browser window will open - useful for debugging and solving captchas.

### Production (headless mode)

Set in `.env`:
```env
HEADLESS=true
```

Then run:
```bash
python bot.py
```

## Usage

1. Start bot: `/start`
2. Click "Create song" button
3. Send text prompt or voice message
   - Text: max 400 characters
   - Voice: will be automatically transcribed
4. Wait for generation (~2 minutes)
5. Receive 2 MP3 files

## Project Structure

```
music-bot/
├── bot.py                      # Main entry point
├── requirements.txt            # Python dependencies
├── .env                        # Configuration (create this)
├── app/
│   ├── config.py              # Configuration loader
│   ├── handlers/
│   │   ├── start.py           # /start command
│   │   └── generate.py        # Song generation logic
│   ├── services/
│   │   └── suno_playwright.py # Suno automation
│   └── utils/
│       ├── cleanup.py         # File cleanup
│       └── notify_admin.py    # Admin notifications
├── data/
│   └── browser_state/         # Persistent browser session
├── downloads/                 # Downloaded MP3 files
└── logs/                      # Log files
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Telegram bot token from BotFather |
| `SUNO_COOKIE` | Yes | - | Suno session cookies |
| `ADMIN_ID` | No | 0 | Telegram user ID for notifications |
| `MAX_PROMPT_LENGTH` | No | 400 | Maximum prompt length |
| `HEADLESS` | No | false | Run browser in headless mode |

## Troubleshooting

### Browser Session Expired

If you see authentication errors:

1. Delete `data/browser_state/` folder
2. Re-extract Suno cookies
3. Update `SUNO_COOKIE` in `.env`
4. Restart bot

### Playwright Not Found

```bash
playwright install chromium
```

### FFmpeg Not Found

Install ffmpeg (see Installation section)

### Bot Not Responding

Check logs in `logs/` folder for errors

## Development

### Run with Debug Logging

```bash
# Modify bot.py
setup_logging(level=logging.DEBUG)
```

### Test Browser Automation

```bash
python test_browser.py
```

## Production Deployment

### Railway / Heroku

1. Set environment variables in platform dashboard
2. Set `HEADLESS=true`
3. Add buildpack for Playwright (if needed)

### VPS / Dedicated Server

1. Install system dependencies:
```bash
sudo apt install -y chromium-browser ffmpeg
```

2. Use systemd service:
```bash
sudo systemctl enable music-bot
sudo systemctl start music-bot
```

## License

MIT

## Support

For issues and questions, open an issue on GitHub.