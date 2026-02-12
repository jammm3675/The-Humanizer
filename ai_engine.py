import logging
import os
import json
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL_NAME = "groq/compound"

import re
from ton_engine import get_collection_full_stats, get_wallet_nfts

async def generate_response(user_message: str, user_data: dict, global_lore: str):
    stats_data = None

    # 1. ПРОВЕРКА НА АДРЕС КОШЕЛЬКА (UQ... или EQ...)
    wallet_match = re.search(r'(UQ|EQ)[a-zA-Z0-9_-]{46}', user_message)

    if wallet_match:
        address = wallet_match.group(0)
        logger.info(f"Detected wallet address: {address}")
        stats_data = await get_wallet_nfts(address)

    # 2. ПРОВЕРКА НА ОБЩУЮ СТАТИСТИКУ
    elif any(kw in user_message.lower() for kw in ["стату", "цены", "floor", "коллекци"]):
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

    # ВАЖНО: Добавь stats_data в промпт, если они найдены
    if stats_data:
        context_injection = f"\n\nАКТУАЛЬНЫЕ ДАННЫЕ ИЗ БЛОКЧЕЙНА:\n{json.dumps(stats_data, ensure_ascii=False)}"
        DYNAMIC_PROMPT += context_injection

    # ФИКС ОШИБКИ 413: Берем только последние 4 сообщения истории
    user_history = user_data.get('last_bot_messages', [])
    short_history = user_history[-4:]

    try:
        completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": DYNAMIC_PROMPT},
                *short_history,
                {"role": "user", "content": user_message}
            ],
            model=MODEL_NAME,
            temperature=0.7,
            # Включаем поиск для курса валют (TON to USD)
            compound_custom={
                "tools": {"enabled_tools": ["web_search"]}
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
