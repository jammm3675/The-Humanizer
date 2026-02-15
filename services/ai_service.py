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
        self.max_context_len = self.bot_params.get("max_context_len", 4000)
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
        elif any(kw in user_message.lower() for kw in ["стату", "цены", "floor", "коллекци", "дашборд"]):
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

ИНСТРУКЦИЯ:
Если пользователь спрашивает о ценах или TON/NOTAPES — используй предоставленные данные блокчейна.
Приоритет: используй предоставленную локальную статистику вместо веб-поиска."""

        if stats_data:
            context_injection = f"\n\nАКТУАЛЬНЫЕ ДАННЫЕ ИЗ БЛОКЧЕЙНА:\n{json.dumps(stats_data, ensure_ascii=False)}"
            DYNAMIC_PROMPT += context_injection

        user_history = user_data.get('last_bot_messages', [])

        messages = [{"role": "system", "content": DYNAMIC_PROMPT}]
        for msg in user_history[-6:]:
            messages.append(msg)
        messages.append({"role": "user", "content": user_message})

        try:
            completion = await self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=self.chat_params.get("temperature", 0.7),
                max_tokens=self.chat_params.get("max_tokens", 500),
                top_p=self.chat_params.get("top_p", 1.0),
                frequency_penalty=self.chat_params.get("frequency_penalty", 0.0),
                presence_penalty=self.chat_params.get("presence_penalty", 0.0),
                stop=self.chat_params.get("stop")
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq Error: {e}")
            raise

    async def update_personality(self, conversation_text: str):
        if not self.client: return None
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Обнови JSON профиля личности пользователя на основе диалога. Верни ТОЛЬКО JSON."},
                    {"role": "user", "content": conversation_text}
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

ai_service = AIService()
