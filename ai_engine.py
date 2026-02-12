import logging
import os
import json
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL_NAME = "groq/compound"

from ton_engine import get_collection_full_stats

async def generate_response(user_message: str, user_data: dict, global_lore: str):
    # TON Stats Local Tool Logic
    stats_data = None
    if any(kw in user_message.lower() for kw in ["стату", "цены", "кто купил"]):
        try:
            stats_data = await get_collection_full_stats()
        except Exception as e:
            logger.error(f"TON Stats Error: {e}")

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
2. Обращение на "ты", имя: {name}.
3. Сленг: TON, щитки, гем

ИНСТРУКЦИЯ ПО ИНСТРУМЕНТАМ:
Если пользователь спрашивает о ценах, информации связанной с TON/NOTAPES или событиях реального времени — обязательно используй web_search. Для истории используй предоставленный Lore. Вам предоставлены данные блокчейна в режиме реального времени. Приоритет: используйте предоставленную локальную статистику вместо веб-поиска для повышения точности цен."""

    if stats_data:
        stats_json = json.dumps(stats_data, ensure_ascii=False, indent=2)
        DYNAMIC_PROMPT += f"\n\nАКТУАЛЬНЫЕ ДАННЫЕ ИЗ БЛОКЧЕЙНА (Используй их для ответа):\n{stats_json}"

    # Parse history
    history_lines = [line for line in summary.split("\n") if line.strip()]
    user_history = []
    for line in history_lines:
        if line.startswith("User: "):
            user_history.append({"role": "user", "content": line.replace("User: ", "")})
        elif line.startswith("The Humanizer: "):
            user_history.append({"role": "assistant", "content": line.replace("The Humanizer: ", "")})

    try:
        completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": DYNAMIC_PROMPT},
                *user_history[-6:],
                {"role": "user", "content": user_message}
            ],
            model=MODEL_NAME,
            temperature=0.7,
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
