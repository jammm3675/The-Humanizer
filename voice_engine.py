import edge_tts
import asyncio
import os
import uuid
import re

# Preferred voice
VOICE = "ru-RU-DmitryNeural"

def clean_text(text: str) -> str:
    """Removes markdown characters and other unwanted symbols for cleaner TTS."""
    if not text:
        return ""
    # Remove *, _, #, [, ]
    cleaned = re.sub(r'[*_#\[\]]', '', text)
    return cleaned.strip()

async def text_to_speech(text: str) -> str:
    """Generates an ogg file from text and returns the file path."""
    file_path = f"voice_{uuid.uuid4()}.ogg"
    cleaned_text = clean_text(text)
    if not cleaned_text:
        cleaned_text = "Хм."

    communicate = edge_tts.Communicate(cleaned_text, VOICE)
    await communicate.save(file_path)
    return file_path
