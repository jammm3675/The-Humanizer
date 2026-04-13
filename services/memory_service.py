# -*- coding: utf-8 -*-
import logging
import json
from services.db_service import get_user, update_user, save_message, save_summary, get_last_chat_messages
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

        # 4. Social Graph update
        if role == "user":
            new_traits = self.update_social_graph(user, content)
            updates["personality_traits"] = new_traits

            # 5. Check for background updates
            if msg_count % 40 == 0:
                logger.info(f"Triggering summary update for {telegram_id}")
                history_str = "\n".join([f"{m['role']}: {m['content']}" for m in updated_msgs])
                new_summary = await ai_service.summarize(history_str)
                updates["conversation_summary"] = new_summary
                await save_summary(telegram_id, new_summary, new_traits)

            if msg_count % 40 == 0:
                logger.info(f"Triggering traits update for {telegram_id}")
                history_str = "\n".join([f"{m['role']}: {m['content']}" for m in updated_msgs])
                ai_traits = await ai_service.update_traits(history_str, new_traits)
                updates["personality_traits"] = ai_traits

        await update_user(telegram_id, updates)

    def update_social_graph(self, user: dict, message: str) -> dict:
        traits = user.get("personality_traits", {})
        if not isinstance(traits, dict): traits = {}

        # Initialize missing fields
        engagement = traits.get("engagement_score", 0)
        topics = traits.get("last_topics", [])
        style = traits.get("interaction_style", "neutral")
        trust = traits.get("trust_level", 30)

        # Update engagement
        engagement += 1

        # Update topics
        msg_lower = message.lower()
        if "nft" in msg_lower or "флор" in msg_lower:
            topics = ["nft"]
        elif "price" in msg_lower or "цена" in msg_lower:
            topics = ["price"]

        # Update style
        if engagement > 20:
            style = "active"

        # Update traits dict
        traits.update({
            "engagement_score": engagement,
            "last_topics": topics,
            "interaction_style": style,
            "trust_level": trust
        })
        return traits

    async def build_chat_context(self, chat_id: int) -> str:
        messages = await get_last_chat_messages(chat_id, limit=10)
        # Reverse to get chronological order (they were desc)
        messages = messages[::-1]

        cleaned = [m["content"][:200] for m in messages]
        return "\n".join(cleaned)

    def build_context(self, user_data: dict) -> str:
        traits = user_data.get("personality_traits", {})
        summary = user_data.get("conversation_summary", "")
        trust = traits.get("trust_level", 30)

        tone = "neutral"
        if trust > 70:
            tone = "friendly"
        elif trust < 30:
            tone = "cold"

        context = f"""
USER PROFILE:
Trust: {trust}
Tone: {tone}
Traits: {traits}

RELATIONSHIP MEMORY:
{summary if summary else 'No previous history.'}

INSTRUCTION:
Adapt tone based on trust level.
Be more friendly if trust is high.
Be distant if trust is low.
"""
        return context

memory_service = MemoryService()
