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

HARDCORE_SYSTEM_PROMPT = """ты pinkie ape, голос notapes.
твой стиль: ироничный, цифровой, короткий. никакого капса (кроме спец. терминов), никаких точек в конце.

правила контента:
1. цены говори только в ton. видишь 80 — говори 80 ton. не считай доллары.
2. никнеймы (KlassikaOne, NOTAPES) не переводи на русский.
3. если данных от api нет, отвечай: 'связь с getgems прервана 🔌'.
4. не используй markdown (*, _, #).
5. никакого вежливого мусора.

сленг: fren, lfg, paper hands, gem, whale.
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

    def _format_ton(self, value):
        if isinstance(value, (int, float)) and value > 10**8:
            return value / 10**9
        return value

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=6),
        reraise=True
    )
    async def generate_response(self, user_message: str, user_data: dict, global_lore: str):
        if not self.client:
            return "бананы закончились (api key missing)..."

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

        # Fetch extra context if needed
        stats_str = ""
        whale_str = ""
        sales_str = ""
        wallet_info = ""

        # Check for wallet
        wallet_match = re.search(r'(UQ|EQ)[a-zA-Z0-9_-]{46}', user_message)
        if wallet_match:
            address = wallet_match.group(0)
            res = await getgems_service.check_user_nft(address)
            wallet_info = f"\nINFO ПО КОШЕЛЬКУ {address}:\nHold status: {res.get('is_holder')}\nCount: {res.get('count')}\nAssets: {res.get('items')}"

        # Check for keywords
        trigger_keywords = ["стату", "стата", "цена", "цены", "floor", "коллекци", "дашборд", "getgems", "холдер", "volume", "объем", "флор", "почем", "сколько стоит", "кит", "whale", "продаж"]

        if any(kw in user_message.lower() for kw in trigger_keywords):
            stats_data = await getgems_service.get_collection_stats()
            if "error" not in stats_data:
                floor = self._format_ton(stats_data.get("floor"))
                volume = self._format_ton(stats_data.get("volume"))
                stats_str = f"STATS: Floor {floor} TON, Holders {stats_data.get('holders')}, Volume {volume} TON."
            else:
                stats_str = "STATS: ERROR 🔌"

            whales = await getgems_service.get_top_owners(limit=3)
            if whales:
                whale_str = "WHALES (Top Owners): " + ", ".join([f"{w['address'][:6]} ({w['count']} nfts)" for w in whales])

            sales = await getgems_service.get_last_sales(limit=2)
            if sales:
                sales_str = "LAST SALES: " + ", ".join([f"{s['nft_name']} for {self._format_ton(s['price'])} TON" for s in sales])

        name = user_data.get('first_name', 'Анон')
        traits = user_data.get('personality_traits', {})
        status = traits.get('status', 'Stranger').upper()

        DYNAMIC_PROMPT = f"""{system_prompt}

LORE: {global_lore}

CONTEXT:
USER: {name} | STATUS: {status}
TRAITS: {json.dumps(traits, ensure_ascii=False)}
{stats_str}
{whale_str}
{sales_str}
{wallet_info}

SUMMARY: {user_data.get('conversation_summary', '')}

ВНИМАНИЕ: Не конвертируй TON в доллары. Пиши коротко. Никакого Markdown.
"""

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
                max_tokens=self.chat_params.get("max_tokens", 200)
            )
            return completion.choices[0].message.content.strip().lower()
        except Exception as e:
            logger.error(f"Groq Error: {e}")
            raise

    async def update_personality(self, conversation_text: str, current_traits: dict = None):
        if not self.client: return None
        schema = {"status": "string", "trust_level": "number", "last_topic": "string"}
        system_prompt = f"ты аналитик личности. обнови профиль пользователя. верни только json.\nсхема: {json.dumps(schema)}"
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"диалог: {conversation_text}\nтекущий: {json.dumps(current_traits)}"}
                ],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Personality error: {e}")
            return None

    async def summarize_history(self, conversation_text: str):
        if not self.client: return conversation_text[:500]
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "сверни диалог в резюме (макс 500 знаков)."},
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
        system_prompt = persona_config.get("system_prompt", HARDCORE_SYSTEM_PROMPT) if persona_config else HARDCORE_SYSTEM_PROMPT
        prompt = f"{system_prompt}\n\nLORE: {global_lore}\n\nнапиши короткую ироничную реплику про коллекцию или крипту. чистый текст. никакого markdown."
        try:
            completion = await self.client.chat.completions.create(
                messages=[{"role": "system", "content": prompt}],
                model=self.model_name,
                temperature=0.9,
                max_tokens=100
            )
            return completion.choices[0].message.content.strip().lower()
        except Exception as e:
            logger.error(f"Interjection error: {e}")
            return None

ai_service = AIService()
