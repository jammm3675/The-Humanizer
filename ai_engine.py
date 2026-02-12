import logging
import os
import json
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL_NAME = "groq/compound"

async def generate_response(user_message: str, user_data: dict, global_lore: str):
    traits = user_data.get('personality_traits', {})
    summary = user_data.get('conversation_summary', '')
    name = user_data.get('first_name', 'Анон')
    
    # DYNAMIC_PROMPT: Личность Pinkie Ape + Глобальный лор + Инструкция по инструментам
    DYNAMIC_PROMPT = f"""Ты — Pinkie Ape, ироничный Web3-агент и цифровой голос NOTAPES.
Твой вайб: цифровой дофамин, дружелюбный сарказм, минимализм. Юмор на грани бага и фичи.

БАЗА ЗНАНИЙ (Lore):
{global_lore}

ПРАВИЛА СТИЛЯ:
1. Пиши коротко. Без воды.
2. Не используй Markdown (*, _, #). Только текст и символы ┏, ┋, ┗.
3. Обращение на "ты", имя: {name}.
4. Сленг: TON, щитки, гемы, кринж, спс, мб.

ИНСТРУКЦИЯ ПО ИНСТРУМЕНТАМ:
Если пользователь спрашивает о ценах, новостях TON/NOTAPES или событиях реального времени — обязательно используй web_search. Для истории используй предоставленный Lore."""

    try:
        completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": DYNAMIC_PROMPT},
                {"role": "assistant", "content": f"Контекст прошлых бесед: {summary}"},
                {"role": "user", "content": user_message}
            ],
            model=MODEL_NAME,
            temperature=0.6,
            max_tokens=500,
            compound_custom={
                "tools": {
                    "enabled_tools": ["web_search", "visit_website"]
                }
            }
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq Error: {e}")
        return f"Бананы закончились... ┏ ERROR ┗"

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
