import os
import uuid
import logging
import asyncio
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
VOICE_ID = os.getenv("ELEVEN_VOICE_ID")

async def text_to_speech(text: str) -> str:
    file_path = f"voice_{uuid.uuid4()}.mp3"
    try:
        def generate():
            return client.text_to_speech.convert(
                voice_id=VOICE_ID,
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(stability=0.4, similarity_boost=0.8)
            )

        audio_stream = await asyncio.to_thread(generate)
        with open(file_path, "wb") as f:
            for chunk in audio_stream:
                if chunk: f.write(chunk)
        return file_path
    except Exception as e:
        logger.error(f"ElevenLabs error: {e}")
        return None
