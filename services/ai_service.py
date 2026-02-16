# -*- coding: utf-8 -*-
import logging
import json
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from groq import AsyncGroq
from config.settings import config
from services.ton_service import ton_service

logger = logging.getLogger(__name__)

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

        stats_data = None

        # 1. ПРОВЕРКА НА АДРЕС КОШЕЛЬКА
        wallet_match = re.search(r'(UQ|EQ)[a-zA-Z0-9_-]{46}', user_message)
        if wallet_match:
            address = wallet_match.group(0)
            logger.info(f"Detected wallet address: {address}")
            stats_data = await ton_service.get_wallet_nfts(address)

        # 2. ПРОВЕРКА НА ОБЩУЮ СТАТИСТИКУ
        elif any(kw in user_message.lower() for kw in ["стату", "цены", "floor", "коллекци", "дашборд", "getgems", "холдер", "volume", "объем"]):
            try:
                stats_data = await ton_service.get_collection_full_stats()
            except Exception as e:
                logger.error(f"TON Stats Error: {e}")

        name = user_data.get('first_name', 'Анон')

        system_prompt = self.bot_params.get("description", "")

        DYNAMIC_PROMPT = f"""{system_prompt}

БАЗА ЗНАНИЙ (Lore):
{global_lore}

ТЕКУЩИЙ КОНТЕКСТ:
Имя пользователя: {name}
Черты личности: {json.dumps(user_data.get('personality_traits', {}), ensure_ascii=False)}


ПРАВИЛА:
1. НЕТ Markdown, JSON, {{ }}.
2. Текст + символы (┏, ┃, ┗, 🧿, 👾, 🤖).
3. RU/EN only. NO Chinese.
4. НИКАКИХ фигурных скобок или JSON-структур в ответе.
5. Приоритет: локальная статистика блокчейна."""

        if stats_data:
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
                model=self.model_name,
                temperature=self.chat_params.get("temperature", 0.7),
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
            "relationship": {
                "trust_level": "number (0-100)",
                "annoyance_level": "number (0-100)",
                "status": "string"
            },
            "memory": {
                "last_topic": "string",
                "key_insights": ["string"]
            },
            "experience": ["string"]
        }

        system_prompt = f"""Ты - аналитик личности. На основе диалога обнови профиль пользователя.
Верни ТОЛЬКО валидный JSON, строго соответствующий следующей схеме:
{json.dumps(schema, indent=2, ensure_ascii=False)}

ТЕКУЩИЙ ПРОФИЛЬ:
{json.dumps(current_traits, indent=2, ensure_ascii=False) if current_traits else "Нет данных"}

КРИТИЧЕСКИЕ ПРАВИЛА:
1. 'experience' - это ВСЕГДА массив строк (массив []), а не объект ({{}}).
2. Любые числовые диапазоны или значения с тире (например, курс валют '90-95', возраст '20-25') ДОЛЖНЫ быть в кавычках как строки. JSON не поддерживает тире в числах.
3. Не добавляй новые поля, не предусмотренные схемой.
4. Отвечай только чистым JSON без Markdown-разметки или пояснений."""

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

        system_prompt = self.bot_params.get("description", "")

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
                model=self.model_name,
                temperature=0.9,
                max_tokens=200
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Interjection generation error: {e}")
            return None

ai_service = AIService()
