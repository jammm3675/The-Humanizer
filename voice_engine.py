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
# Если переменная не задана, используем стандартного Liam (он доступен на Free)
VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "TX3LPaxmHKxFfWic98QC")

async def text_to_speech(text: str) -> str:
    # Удаляем лишние символы для чистоты речи
    clean_text = text.replace("*", "").replace("_", "").replace("#", "")
    file_path = f"voice_{uuid.uuid4()}.mp3"

    try:
        def generate():
            return client.text_to_speech.convert(
                voice_id=VOICE_ID,
                text=clean_text,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=0.4,
                    similarity_boost=0.75,
                    style=0.1,
                    use_speaker_boost=True
                )
            )

        audio_stream = await asyncio.to_thread(generate)

        with open(file_path, "wb") as f:
            for chunk in audio_stream:
                if chunk:
                    f.write(chunk)

        return file_path
    except Exception as e:
        # Если квота или платная ошибка — просто логируем и возвращаем None
        logger.error(f"ElevenLabs error: {e}")
        return None
