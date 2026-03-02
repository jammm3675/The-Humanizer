# -*- coding: utf-8 -*-
import logging
import json
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from groq import AsyncGroq
from config.settings import config
from services.getgems_service import getgems_service
from services.db_service import get_personality_config

logger = logging.getLogger(__name__)

HARDCORE_SYSTEM_PROMPT = """Ты — Pinkie Ape, голос NOTAPES.
Твой стиль: Ироничный, цифровой, короткий.

ПРАВИЛА КОНТЕНТА:
1. Цены говори ТОЛЬКО в TON. Видишь 80 — говори 80 TON. Не считай доллары.
2. Никнеймы (KlassikaOne, NOTAPES) не переводи на русский.
3. Если данных от API нет, отвечай: 'Связь с Getgems прервана 🔌'.
4. Не используй Markdown.

ПРАВИЛА ОБЩЕНИЯ:
- Обращайся на 'ты'.
- Никакой воды и вежливости.
"""

class AIService:
    def __init__(self):
        self.api_key = config.GROQ_API_KEY
        self.chat_params = config.get_chat_model_params()
        self.bot_params = config.get_chatbot_params()
        self.model_name = self.chat_params.get("model", "llama-3.3-70b-versatile")
        self.max_context_len = self.bot_params.get("max_context_len", 2000)
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                logger.error("GROQ_API_KEY not found")
                return None
            self._client = AsyncGroq(api_key=self.api_key)
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=6),
        reraise=True
    )
    async def generate_response(self, user_message: str, user_data: dict, global_lore: str):
        if not self.client:
            return "Бананы закончились (API Key missing)..."

        # Пытаемся получить настройки из базы
        persona_config = await get_personality_config()

        if persona_config:
            system_prompt = persona_config.get("system_prompt", HARDCORE_SYSTEM_PROMPT)
            current_model = persona_config.get("model", self.model_name)
            current_temp = persona_config.get("temperature", self.chat_params.get("temperature", 0.7))
        else:
            system_prompt = HARDCORE_SYSTEM_PROMPT
            current_model = self.model_name
            current_temp = self.chat_params.get("temperature", 0.7)

        logger.info(f"Using model: {current_model}")

        stats_data = None

        # 1. ПРОВЕРКА НА АДРЕС КОШЕЛЬКА
        wallet_match = re.search(r'(UQ|EQ)[a-zA-Z0-9_-]{46}', user_message)
        if wallet_match:
            address = wallet_match.group(0)
            logger.info(f"Detected wallet address: {address}")
            stats_data = await getgems_service.get_wallet_nfts(address)

        # 2. ПРОВЕРКА НА ОБЩУЮ СТАТИСТИКУ
        elif any(kw in user_message.lower() for kw in ["стату", "стата", "цена", "цены", "floor", "коллекци", "дашборд", "getgems", "холдер", "volume", "объем", "флор", "почем", "сколько стоит"]):
            try:
                stats_data = await getgems_service.get_collection_stats()
            except Exception as e:
                logger.error(f"TON Stats Error: {e}")

        name = user_data.get('first_name', 'Анон')

        DYNAMIC_PROMPT = f"""{system_prompt}

БАЗА ЗНАНИЙ (Lore):
{global_lore}

ТЕКУЩИЙ КОНТЕКСТ:
Имя пользователя: {name}
Черты личности: {json.dumps(user_data.get('personality_traits', {}), ensure_ascii=False)}"""

        if stats_data:
            if "floor" in stats_data or "error" in stats_data:
                if "error" in stats_data:
                    context_injection = f"\n\nДАННЫЕ ИЗ БЛОКЧЕЙНА (Getgems):\n- Error: {stats_data['error']}"
                else:
                    floor = stats_data.get("floor", "Н/Д")
                    # Переводим наноТон в обычный TON, если там большое число
                    if isinstance(floor, (int, float)) and floor > 10**8:
                        floor = floor / 10**9

                    stats_str = (
                        f"ДАННЫЕ ИЗ БЛОКЧЕЙНА (Getgems):\n"
                        f"- Floor Price: {floor} TON\n"
                        f"- Holders: {stats_data.get('holders', 'Н/Д')}\n"
                        f"- Total Items: {stats_data.get('items', 'Н/Д')}\n"
                        f"ВНИМАНИЕ: Не конвертируй TON в доллары сам. Говори только то, что видишь выше."
                    )
                    context_injection = f"\n\n{stats_str}"
            elif isinstance(stats_data, list):
                filtered_stats = {
                    "total_nfts": len(stats_data),
                    "nfts": [nft.get("metadata", {}).get("name", "Unknown NFT") for nft in stats_data[:5]]
                }
                context_injection = f"\n\nАКТУАЛЬНЫЕ ДАННЫЕ ИЗ БЛОКЧЕЙНА:\n{json.dumps(filtered_stats, ensure_ascii=False)}"
            else:
                context_injection = f"\n\nАКТУАЛЬНЫЕ ДАННЫЕ ИЗ БЛОКЧЕЙНА:\n{json.dumps(stats_data, ensure_ascii=False)}"

            DYNAMIC_PROMPT += context_injection

        user_history = user_data.get('last_bot_messages', [])

        messages = [{"role": "system", "content": DYNAMIC_PROMPT}]
        for msg in user_history[-4:]:
            messages.append(msg)
        messages.append({"role": "user", "content": user_message})

        try:
            completion = await self.client.chat.completions.create(
                messages=messages,
                model=current_model,
                temperature=current_temp,
                max_tokens=self.chat_params.get("max_tokens", 200),
                top_p=self.chat_params.get("top_p", 1.0),
                frequency_penalty=self.chat_params.get("frequency_penalty", 0.0),
                presence_penalty=self.chat_params.get("presence_penalty", 0.0),
                stop=self.chat_params.get("stop")
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq Error: {e}")
            raise

    async def update_personality(self, conversation_text: str, current_traits: dict = None):
        if not self.client: return None

        schema = {
            "status": "string",
            "trust_level": "number (0-100)",
            "last_topic": "string"
        }

        system_prompt = f"""Ты - аналитик личности. На основе диалога обнови профиль пользователя.
Верни ТОЛЬКО валидный JSON, строго соответствующий следующей схеме:
{json.dumps(schema, indent=2, ensure_ascii=False)}

ТЕКУЩИЙ ПРОФИЛЬ:
{json.dumps(current_traits, indent=2, ensure_ascii=False) if current_traits else "Нет данных"}

КРИТИЧЕСКИЕ ПРАВИЛА:
1. Не добавляй новые поля, не предусмотренные схемой.
2. Никаких массивов 'experience' или 'skills'. Только flat структура.
3. Отвечай только чистым JSON без Markdown-разметки или пояснений."""

        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Диалог для анализа:\n{conversation_text}"}
                ],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Personality update error: {e}")
            return None

    async def summarize_history(self, conversation_text: str):
        if not self.client: return conversation_text[:500]
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Сверни диалог в резюме (макс 500 знаков)."},
                    {"role": "user", "content": conversation_text}
                ],
                model="llama-3.1-8b-instant",
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return conversation_text[:500]

    async def generate_interjection(self, global_lore: str):
        if not self.client: return None

        persona_config = await get_personality_config()
        if persona_config:
            system_prompt = persona_config.get("system_prompt", HARDCORE_SYSTEM_PROMPT)
            current_model = persona_config.get("model", self.model_name)
        else:
            system_prompt = HARDCORE_SYSTEM_PROMPT
            current_model = self.model_name

        prompt = f"""{system_prompt}

БАЗА ЗНАНИЙ (Lore):
{global_lore}

ЗАДАЧА:
Напиши короткую ироничную реплику, шутку или мем-фразу про коллекцию NOTAPES или крипту в целом.
Это должно быть внезапное сообщение в чат.
НИКАКОГО Markdown. Используй чистый текст и цифровые символы (┏, ┃, ┗).
Пиши как Pinkie Ape: дерзко, цифровой вайб, коротко, без иероглифов."""

        try:
            completion = await self.client.chat.completions.create(
                messages=[{"role": "system", "content": prompt}],
                model=current_model,
                temperature=0.9,
                max_tokens=200
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Interjection generation error: {e}")
            return None

ai_service = AIService()
