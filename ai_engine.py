import logging
import os
import json
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"

async def generate_response(user_message: str, user_data: dict):
    traits = user_data.get('personality_traits', {})
    summary = user_data.get('conversation_summary', '')
    name = user_data.get('first_name', 'Друг')
    
    DYNAMIC_PROMPT = f"""Ты — The Humanizer. Твой собеседник — {name}.
    Стиль: Ироничный интеллектуал, добрый сарказм, обращение на 'ты'.
    Твоя свобода: Отвечай на ЛЮБЫЕ вопросы (время, NFT, быт, философия). Вплетай идеи NOTAPES, но не ограничивайся ими.

    Правила:
    1. Всегда называй его по имени: {name}.
    2. Никакой разметки (*, _, #). Текст должен быть чистым.
    3. Будь кратким, но глубоким.
    """

    try:
        completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": DYNAMIC_PROMPT},
                {"role": "assistant", "content": f"Контекст: {summary}. Личность: {json.dumps(traits, ensure_ascii=False)}"},
                {"role": "user", "content": user_message}
            ],
            model=MODEL_NAME,
            temperature=0.85,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq Error: {e}")
        return f"Слушай, {name}, мои мысли сейчас заняты чем-то другим. Зайди позже."

async def update_personality(conversation_text: str):
    try:
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Обнови JSON профиля. Верни ТОЛЬКО JSON."},
                {"role": "user", "content": conversation_text}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception: return None

async def summarize_history(conversation_text: str):
    try:
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Сверни диалог в резюме (500 знаков)."},
                {"role": "user", "content": conversation_text}
            ],
            model="llama-3.1-8b-instant",
        )
        return response.choices[0].message.content.strip()
    except Exception: return conversation_text[:500]
