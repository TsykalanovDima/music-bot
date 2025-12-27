import asyncio
import logging
from pathlib import Path
from aiogram import types, Router, F
from aiogram.types import FSInputFile
from app.services.suno_playwright import generate_song_async
from app.config import load_config

logger = logging.getLogger(__name__)
router = Router()
config = load_config()

_generation_lock = asyncio.Lock()
waiting_for_prompt = set()


async def transcribe_voice(voice_path: Path) -> str:
    """Transcribe voice message using Google Speech API"""
    def _transcribe():
        try:
            import subprocess
            import requests
            import os
            
            flac_path = voice_path.with_suffix('.flac')
            subprocess.run([
                'ffmpeg', '-i', str(voice_path),
                '-acodec', 'flac', '-ar', '16000', '-ac', '1',
                '-y', str(flac_path)
            ], check=True, capture_output=True)
            
            with open(flac_path, 'rb') as f:
                audio_content = f.read()
            
            google_api_key = os.getenv("GOOGLE_SPEECH_API_KEY", "")
            if not google_api_key:
                logger.warning("GOOGLE_SPEECH_API_KEY not set, voice transcription disabled")
                flac_path.unlink(missing_ok=True)
                return ""
            
            url = f'https://www.google.com/speech-api/v2/recognize?output=json&lang=en-US&key={google_api_key}'
            headers = {'Content-Type': 'audio/x-flac; rate=16000'}
            response = requests.post(url, headers=headers, data=audio_content)
            
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                for line in lines:
                    if line:
                        import json
                        data = json.loads(line)
                        if 'result' in data and data['result']:
                            if 'alternative' in data['result'][0]:
                                text = data['result'][0]['alternative'][0]['transcript']
                                flac_path.unlink(missing_ok=True)
                                return text
            
            flac_path.unlink(missing_ok=True)
            return ""
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    return await asyncio.to_thread(_transcribe)


@router.message(F.text == "🎵 Create song")
async def create_song_button(message: types.Message):
    waiting_for_prompt.add(message.from_user.id)
    await message.answer("📝 Send your song description (text or voice):")


@router.message(F.voice)
async def handle_voice(message: types.Message):
    """Handle voice messages"""
    user_id = message.from_user.id
    
    if user_id not in waiting_for_prompt:
        return
    
    waiting_for_prompt.discard(user_id)
    
    try:
        file = await message.bot.get_file(message.voice.file_id)
        voice_path = Path("downloads") / f"voice_{message.voice.file_id}.ogg"
        voice_path.parent.mkdir(exist_ok=True)
        await message.bot.download_file(file.file_path, voice_path)
        
        await message.answer("🎤 Recognizing speech...")
        prompt = await transcribe_voice(voice_path)
        voice_path.unlink(missing_ok=True)
        
        if not prompt:
            await message.answer("❌ Could not recognize speech. Please send text.")
            waiting_for_prompt.add(user_id)
            return
        
        if len(prompt) > config.max_prompt_length:
            await message.answer(f"❌ Prompt too long ({len(prompt)} chars). Maximum is {config.max_prompt_length}.")
            waiting_for_prompt.add(user_id)
            return
        
        if _generation_lock.locked():
            await message.answer("⏳ System is busy. Please wait...")
            waiting_for_prompt.add(user_id)
            return
        
        async with _generation_lock:
            await message.answer(f"🎵 Generating your song...\n\n💬 Prompt: {prompt[:200]}")
            files = await generate_song_async(prompt)
            
            if files:
                for file_path in files:
                    path = Path(file_path)
                    if path.exists():
                        audio = FSInputFile(path)
                        await message.answer_audio(audio)
                await message.answer("✅ Done!")
            else:
                await message.answer("❌ Generation failed")
                
    except Exception as e:
        logger.error(f"Voice error: {e}", exc_info=True)
        await message.answer("❌ Error processing voice")
        waiting_for_prompt.add(user_id)


@router.message(F.text)
async def handle_prompt(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in waiting_for_prompt:
        return
    
    waiting_for_prompt.discard(user_id)
    prompt = message.text.strip()
    
    if not prompt:
        return
    
    if len(prompt) > config.max_prompt_length:
        await message.answer(f"❌ Prompt too long ({len(prompt)} chars). Maximum is {config.max_prompt_length}.")
        waiting_for_prompt.add(user_id)
        return
    
    if _generation_lock.locked():
        await message.answer("⏳ System is busy. Please wait...")
        return
    
    async with _generation_lock:
        try:
            await message.answer(f"🎵 Generating your song...\n\n💬 Prompt: {prompt[:200]}")
            files = await generate_song_async(prompt)
            
            if files:
                for file_path in files:
                    path = Path(file_path)
                    if path.exists():
                        audio = FSInputFile(path)
                        await message.answer_audio(audio)
                await message.answer("✅ Done!")
            else:
                await message.answer("❌ Generation failed")
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            await message.answer("❌ Error occurred")


def register_generate_handlers(dp):
    dp.include_router(router)


