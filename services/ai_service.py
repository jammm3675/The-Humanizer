# -*- coding: utf-8 -*-
import logging
import json
from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import config

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = AsyncGroq(api_key=config.GROQ_API_KEY) if config.GROQ_API_KEY else None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6))
    async def call_llm(self, messages: list, model: str = "llama-3.3-70b-versatile", temperature: float = 0.7, max_tokens: int = 500, json_mode: bool = False):
        if not self.client:
            return "API key missing"

        opts = {"messages": messages, "model": model, "temperature": temperature, "max_tokens": max_tokens}
        if json_mode:
            opts["response_format"] = {"type": "json_object"}

        try:
            completion = await self.client.chat.completions.create(**opts)
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq error: {e}")
            raise

    async def summarize(self, history: str):
        prompt = f"Summarize relationship in 1-2 sentences based on this history:\\n{history}"\n        messages = [{"role": "system", "content": "Ты аналитик памяти."}, {"role": "user", "content": prompt}]
        return await self.call_llm(messages, model="llama-3.1-8b-instant")

    async def update_traits(self, history: str, current_traits: dict):
        schema = {"status": "str", "trust_level": "int", "last_topic": "str"}
        prompt = (
            f"Обнови черты личности пользователя на основе диалога. Верни ТОЛЬКО JSON.\n"
            f"Схема: {json.dumps(schema)}\n"
            f"Текущие: {json.dumps(current_traits)}\n"
            f"Диалог: {history}"
        )
        messages = [{"role": "system", "content": "Ты психоаналитик. Пиши только JSON."}, {"role": "user", "content": prompt}]
        res = await self.call_llm(messages, model="llama-3.1-8b-instant", json_mode=True)
        try: return json.loads(res)
        except: return current_traits

ai_service = AIService()
