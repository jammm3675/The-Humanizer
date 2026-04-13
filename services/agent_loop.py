# -*- coding: utf-8 -*-
import logging
import random
from config.settings import config
from services.ai_service import ai_service
from services.memory_service import memory_service
from services.persona_service import persona_service
from services.getgems_service import getgems_service
from services.db_service import get_cached_settings

logger = logging.getLogger(__name__)

class AgentLoop:
    async def run(self, user_message: str, user_data: dict) -> str:
        # Initial State
        memory_context = memory_service.build_context(user_data)
        nft_context = ""
        candidate = ""
        persona = await persona_service.get_persona()

        for i in range(config.MAX_ITERATIONS):
            logger.info(f"Agent Loop Iteration {i+1}")

            # 1. Decide if NFT context is needed (on first iteration or if specifically asked)
            if not nft_context and any(kw in user_message.lower() for kw in ["цена", "флор", "getgems", "кит", "продаж"]):
                logger.info("Fetching NFT context...")
                stats = await getgems_service.get_collection_stats()
                nft_context = f"NFT STATS: Floor {stats.get('floor', '?')} TON, Volume {stats.get('volume', '?')} TON.\n"

            # 2. Build full prompt for candidate generation
            messages = [
                {"role": "system", "content": persona["system_prompt"]},
                {"role": "system", "content": f"CONTEXT:\n{memory_context}\n{nft_context}"}
            ]
            # Add short-term history
            for msg in (user_data.get("last_messages") or [])[-4:]:
                messages.append(msg)

            messages.append({"role": "user", "content": user_message})

            # 3. Generate candidate
            candidate = await ai_service.call_llm(messages)

            # 4. Validate style & persona (Simulation of internal check)
            # If candidate is too long or formal, we'd loop again, but here we just sanitize
            candidate = self.sanitize_response(candidate)

            # 5. Stop early check
            if candidate and len(candidate) < 400:
                logger.info("Candidate valid. Breaking loop.")
                break

        return candidate

    def sanitize_response(self, text: str) -> str:
        # Remove markdown as requested
        for char in ["*", "_", "#", "`"]:
            text = text.replace(char, "")
        return text.strip()

agent_loop = AgentLoop()
