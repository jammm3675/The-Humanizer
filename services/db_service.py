import os
import logging
import time
import json
from typing import Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None

# Simple time-based cache for global config
_config_cache: Dict[str, Any] = {}
_config_cache_timestamp: float = 0
CACHE_TTL = 300  # 5 minutes

async def get_cached_settings() -> Dict[str, Any]:
    global _config_cache, _config_cache_timestamp
    now = time.time()

    if _config_cache and (now - _config_cache_timestamp < CACHE_TTL):
        return _config_cache

    if not supabase:
        return {}

    try:
        response = supabase.table("global_config").select("*").execute()
        if response.data:
            new_cache = {}
            for row in response.data:
                key = row['key']
                content = row['content']
                # Try to parse content if it looks like JSON
                try:
                    if content.startswith('{') or content.startswith('['):
                        new_cache[key] = json.loads(content)
                    else:
                        new_cache[key] = content
                except:
                    new_cache[key] = content

            _config_cache = new_cache
            _config_cache_timestamp = now
            return _config_cache
    except Exception as e:
        logger.error(f"Error fetching global config: {e}")

    return _config_cache or {}

async def get_user(telegram_id: int):
    if not supabase: return None
    try:
        response = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.error(f"Error fetching user {telegram_id}: {e}")
    return None

async def create_user(telegram_id: int, username: str, first_name: str):
    data = {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "personality_traits": {
            "status": "Stranger",
            "trust_level": 30,
            "last_topic": "None"
        },
        "conversation_summary": "",
        "message_count": 0
    }
    if not supabase: return None
    try:
        response = supabase.table("users").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None

async def update_user(telegram_id: int, updates: dict):
    if not supabase: return None
    try:
        response = supabase.table("users").update(updates).eq("telegram_id", telegram_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error updating user {telegram_id}: {e}")
    return None

async def increment_counters(telegram_id: int):
    user = await get_user(telegram_id)
    if not user: return False, False

    current_msg_count = user.get("message_count", 0)
    new_msg_count = current_msg_count + 1

    updates = {"message_count": new_msg_count}
    await update_user(telegram_id, updates)

    return (new_msg_count % 15 == 0), (new_msg_count % 40 == 0)

async def update_conversation_history(telegram_id: int, new_message: str):
    user = await get_user(telegram_id)
    if not user:
        return

    current_summary = user.get("conversation_summary") or ""
    updated_summary = (current_summary + "\n" + new_message).strip()

    if len(updated_summary) > 5000:
        updated_summary = updated_summary[-5000:]

    await update_user(telegram_id, {"conversation_summary": updated_summary})

async def get_global_lore():
    """Получает актуальный лор из кэшированных настроек."""
    settings = await get_cached_settings()
    # Try collection_lore first, fallback to notapes_lore (old key)
    return settings.get("collection_lore") or settings.get("notapes_lore") or ""

async def update_global_lore(new_content: str):
    if not supabase: return
    try:
        # Update both keys for compatibility if needed, but primary is collection_lore
        supabase.table("global_config").upsert({"key": "collection_lore", "content": new_content}).execute()
        # Invalidate cache
        global _config_cache_timestamp
        _config_cache_timestamp = 0
    except Exception as e:
        logger.error(f"Error updating lore: {e}")

async def get_personality_config():
    """Забирает настройки личности из кэшированных настроек."""
    settings = await get_cached_settings()
    # Key is now pinkie_persona according to the new spec, fallback to bot_personality
    persona = settings.get("pinkie_persona") or settings.get("bot_personality")

    if isinstance(persona, str):
        return {"system_prompt": persona}
    return persona

async def register_chat(chat_id: int, chat_type: str):
    if not supabase: return
    try:
        supabase.table("chats").upsert({"chat_id": chat_id, "chat_type": chat_type}).execute()
    except Exception as e:
        logger.error(f"Error registering chat {chat_id}: {e}")

async def get_active_groups():
    if not supabase: return []
    try:
        response = supabase.table("chats").select("chat_id").in_("chat_type", ["group", "supergroup"]).execute()
        return [item['chat_id'] for item in response.data] if response.data else []
    except Exception as e:
        logger.error(f"Error fetching active groups: {e}")
    return []
