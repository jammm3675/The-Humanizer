# -*- coding: utf-8 -*-
import logging
import json
from services.db_service import get_user, update_user, save_message, save_summary
from services.ai_service import ai_service

logger = logging.getLogger(__name__)

class MemoryService:
    async def process_memory(self, telegram_id: int, chat_id: int, role: str, content: str):
        # 1. Get user and history
        user = await get_user(telegram_id)
        if not user: return

        last_msgs = user.get("last_messages") or []
        if not isinstance(last_msgs, list): last_msgs = []

        # 2. Append new message to short-term memory (keep last 10)
        new_msg = {"role": role, "content": content}
        updated_msgs = (last_msgs + [new_msg])[-10:]

        # 3. Save to full log and update short memory
        await save_message(telegram_id, chat_id, role, content)

        msg_count = user.get("message_count", 0) + (1 if role == "user" else 0)
        updates = {"last_messages": updated_msgs, "message_count": msg_count}

        # 4. Check for background updates
        if role == "user":
            if msg_count % 15 == 0:
                logger.info(f"Triggering summary update for {telegram_id}")
                history_str = "\n".join([f"{m['role']}: {m['content']}" for m in updated_msgs])
                new_summary = await ai_service.summarize(history_str)
                updates["conversation_summary"] = new_summary
                await save_summary(telegram_id, new_summary, user.get("personality_traits"))

            if msg_count % 40 == 0:
                logger.info(f"Triggering traits update for {telegram_id}")
                history_str = "\n".join([f"{m['role']}: {m['content']}" for m in updated_msgs])
                new_traits = await ai_service.update_traits(history_str, user.get("personality_traits"))
                updates["personality_traits"] = new_traits

        await update_user(telegram_id, updates)

    def build_context(self, user_data: dict) -> str:
        traits = user_data.get("personality_traits", {})
        summary = user_data.get("conversation_summary", "")
        context = f"USER STATUS: {traits.get('status', 'Stranger')}\n"
        context += f"TRUST LEVEL: {traits.get('trust_level', 30)}\n"
        if summary:
            context += f"SUMMARY: {summary}\n"
        return context

memory_service = MemoryService()
