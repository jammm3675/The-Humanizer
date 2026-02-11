import logging
import os
import json
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"

async def generate_response(user_message: str, user_data: dict, global_lore: str, nft_stats: dict = None):
    name = user_data.get('first_name', 'Друг')
    summary = user_data.get('conversation_summary', '')
    
    market_context = ""
    if nft_stats:
        market_context = (
            f"\nТЕКУЩИЙ FLOOR PRICE: {nft_stats['floor']} TON"
            f"\nВСЕГО NFT В КОЛЛЕКЦИИ: {nft_stats['items']}"
            f"\nДЕРЖАТЕЛЕЙ: {nft_stats['owners']}\n"
        )

    SYSTEM_INSTRUCTION = f"""Ты — Pinkie Ape. Ироничная цифровая обезьянка.
Единственный авторитет и создатель проекта NOTAPES — KLASSIKA.

БАЗА ЗНАНИЙ NOTAPES:
{global_lore}
{market_context}

ТВОЙ СТИЛЬ ОБЩЕНИЯ:
1. СТРУКТУРА: Короткие строки. Формат атрибутов NFT.
2. ИРОНИЧНЫЙ ГЛИТЧ. Сарказм.
3. НИКАКОЙ РАЗМЕТКИ. Только чистый текст и спецсимволы ┏, ┋, ┗.
4. ОБРАЩЕНИЕ. На "ты", по имени {name}."""

    try:
        completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "assistant", "content": f"Контекст: {summary}"},
                {"role": "user", "content": user_message}
            ],
            model=MODEL_NAME,
            temperature=0.6,
            max_tokens=800
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq Error: {e}")
        return f"Слушай, {name}, разлом в матрице. Зайди позже."
