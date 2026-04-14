# -*- coding: utf-8 -*-
import logging
from config.settings import config
from services.ai_service import ai_service
from services.memory_service import memory_service
from services.persona_service import persona_service
from services.db_service import get_chat, get_collection, get_collection_entries, get_prompt_layers

logger = logging.getLogger(__name__)

class AgentLoop:
    async def run(self, user_message: str, user_data: dict, chat_id: int = None) -> str:
        # 1. Load context data
        chat = await get_chat(chat_id) if chat_id else {}
        collection_slug = chat.get("collection_slug") if chat else None

        collection = await get_collection(collection_slug) if collection_slug else {}
        entries = await get_collection_entries(collection_slug) if collection_slug else []
        layers = await get_prompt_layers()

        # 2. Determine mode
        mode = persona_service.detect_mode(user_data, user_message)

        # 3. Build system prompt
        system_prompt = persona_service.build_system_prompt(
            user_data,
            collection,
            layers,
            entries,
            mode
        )

        # 4. History and context
        chat_context = ""
        if chat_id:
            chat_context = await memory_service.build_chat_context(chat_id)

        candidate = ""

        for i in range(config.MAX_ITERATIONS):
            logger.info(f"Agent Loop Iteration {i+1}")

            messages = [{"role": "system", "content": system_prompt}]

            if chat_context:
                messages.append({"role": "system", "content": f"CHAT HISTORY:\n{chat_context}"})

            # Add short-term user history
            for msg in (user_data.get("last_messages") or [])[-4:]:
                messages.append(msg)

            messages.append({"role": "user", "content": user_message})

            try:
                # Get dynamic config for AI params
                settings = await persona_service.get_persona()
                model = settings.get("model", "llama-3.3-70b-versatile")
                temp = settings.get("temperature", 0.7)

                candidate = await ai_service.call_llm(messages, model=model, temperature=temp)
            except Exception as e:
                logger.error(f"LLM call error: {e}")
                return "хм... что-то сломалось, попробуй ещё раз"

            # 5. Persona enforcement
            candidate = persona_service.enforce_persona(candidate)

            # 6. Quality check & Early stop
            if candidate and len(candidate) < 1000:
                logger.info("Candidate valid. Breaking loop.")
                break

        return candidate or "хм... сформулируй иначе"

agent_loop = AgentLoop()
