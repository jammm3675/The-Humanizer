import os
import uuid
import logging
import asyncio
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from config.settings import config

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.api_key = config.ELEVENLABS_API_KEY
        self.voice_id = config.ELEVEN_VOICE_ID or "TX3LPaxmHKxFfWic98QC"
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                logger.error("ELEVENLABS_API_KEY not found")
                return None
            self._client = ElevenLabs(api_key=self.api_key)
        return self._client

    async def text_to_speech(self, text: str) -> str:
        if not self.client:
            return None

        clean_text = text.replace("*", "").replace("_", "").replace("#", "")
        file_path = f"voice_{uuid.uuid4()}.mp3"

        try:
            def generate():
                return self.client.text_to_speech.convert(
                    voice_id=self.voice_id,
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
            logger.error(f"ElevenLabs error: {e}")
            return None

voice_service = VoiceService()
