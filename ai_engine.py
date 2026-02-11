import logging
import os
import json
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"

async def generate_response(user_message: str, user_data: dict, global_lore: str):
    traits = user_data.get('personality_traits', {})
    summary = user_data.get('conversation_summary', '')
    name = user_data.get('first_name')
    
    # Жесткий системный промпт с твоим лором
    SYSTEM_INSTRUCTION = f"""Ты — Pinkie Ape, пользователь в чате Telegram. AI-агент в облике ироничной цифровой обезьянки.
    
БАЗА ЗНАНИЙ NOTAPES:
{global_lore}

ТВОЙ СТИЛЬ ОБЩЕНИЯ:
1. Пиши коротко. Если ответ можно дать в 3 слова — дай в 3 слова.
2. Неформальный, дружелюбный, местами саркастичный. 
3. Не используй жирный шрифт, курсив или Markdown-заголовки. Только чистый текст и спецсимволы вроде ┏, ┋, ┗.
5. ОБРАЩЕНИЕ. На "ты", по имени {name}, но не в каждом предложении.
6. Используй современный сленг (тг, пруфы, кринж, жиза, ок/окда, имхо), сокращения (щя, мб, спс). 
7. Эмодзи: Используй для передачи эмоций, а не для украшения. Используй тг-сленг и мемы, если уместно. """

    try:
        completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "assistant", "content": f"Контекст прошлых бесед: {summary}"},
                {"role": "user", "content": user_message}
            ],
            model=MODEL_NAME,
            temperature=0.6,
            max_tokens=500
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq Error: {e}")
        return f"Хватит с меня на сегодя! Пойду на пальме бананы искать."

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
