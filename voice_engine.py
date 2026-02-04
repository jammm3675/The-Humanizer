import edge_tts
import asyncio
import os
import uuid

# Preferred voice
VOICE = "ru-RU-DmitryNeural"

async def text_to_speech(text: str) -> str:
    """Generates an ogg file from text and returns the file path."""
    file_path = f"voice_{uuid.uuid4()}.ogg"
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(file_path)
    return file_path
