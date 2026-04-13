# -*- coding: utf-8 -*-
import logging
import random
from config.settings import config
from services.ai_service import ai_service
from services.memory_service import memory_service
from services.persona_service import persona_service
from services.getgems_service import getgems_service

logger = logging.getLogger(__name__)

class AgentLoop:
    async def run(self, user_message: str, user_data: dict, chat_id: int = None) -> str:
        # Initial State
        memory_context = memory_service.build_context(user_data)
        chat_context = ""
        if chat_id:
            chat_context = await memory_service.build_chat_context(chat_id)

        nft_context = ""
        candidate = ""
        persona = await persona_service.get_persona()
        style = persona_service.adapt_personality(user_data.get("personality_traits", {}))

        for i in range(config.MAX_ITERATIONS):
            logger.info(f"Agent Loop Iteration {i+1}")

            # 1. Decide if NFT context is needed
            msg_lower = user_message.lower()
            needs_nft = any(kw in msg_lower for kw in [
                "floor", "price", "цена", "коллекци", "volume", "whale", "флор", "кит", "продаж"
            ])

            if needs_nft and not nft_context:
                try:
                    stats = await getgems_service.get_collection_stats()
                    nft_context = f"NFT DATA: {stats}"
                except Exception as e:
                    logger.error(f"NFT fetch error: {e}")
                    nft_context = ""

            # 2. Generate candidate
            messages = [
                {"role": "system", "content": persona["system_prompt"]},
                {"role": "system", "content": f"STYLE: {style}"},
                {"role": "system", "content": f"CONTEXT:\n{memory_context}"}
            ]

            if chat_context:
                messages.append({"role": "system", "content": f"CHAT HISTORY:\n{chat_context}"})

            if nft_context:
                messages.append({"role": "system", "content": nft_context})

            # Add short-term user history
            for msg in (user_data.get("last_messages") or [])[-4:]:
                messages.append(msg)

            messages.append({"role": "user", "content": user_message})

            try:
                candidate = await ai_service.call_llm(messages)
            except Exception as e:
                logger.error(f"LLM call error: {e}")
                return "хм... что-то сломалось, попробуй ещё раз"

            # 3. Persona enforcement
            candidate = persona_service.enforce_persona(candidate)

            # 4. Quality check & Early stop
            if candidate and len(candidate) < 500:
                logger.info("Candidate valid. Breaking loop.")
                break

        return candidate or "хм... сформулируй иначе"

agent_loop = AgentLoop()
