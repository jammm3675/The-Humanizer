import os
import uuid
import logging
import asyncio
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Инициализация клиента
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "pMs3N412499T79yS6YJ4") # Дефолтный ID

async def text_to_speech(text: str) -> str:
    """Генерирует аудио через ElevenLabs. Возвращает путь к файлу или None, если лимит исчерпан."""
    file_path = f"voice_{uuid.uuid4()}.mp3"

    try:
        # Сама генерация (выполняем в отдельном потоке, так как SDK синхронный)
        def generate():
            return client.text_to_speech.convert(
                voice_id=VOICE_ID,
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            )

        # Запускаем генерацию
        audio_stream = await asyncio.to_thread(generate)

        # Сохраняем поток в файл
        with open(file_path, "wb") as f:
            for chunk in audio_stream:
                if chunk:
                    f.write(chunk)

        return file_path

    except Exception as e:
        # Проверяем, не закончилась ли квота (код ошибки 401/400 с текстом quota_exceeded)
        if "quota_exceeded" in str(e).lower():
            logger.warning("ElevenLabs quota exhausted! Switching to text-only mode.")
        else:
            logger.error(f"ElevenLabs error: {e}")

        # Если ошибка или лимит — возвращаем None
        if os.path.exists(file_path):
            os.remove(file_path)
        return None
