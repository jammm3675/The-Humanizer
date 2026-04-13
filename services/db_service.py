# -*- coding: utf-8 -*-
import logging
import time
import json
from typing import Dict, Any, Optional, List
from supabase import create_client, Client
from config.settings import config

logger = logging.getLogger(__name__)

try:
    supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None

# Simple config cache
_config_cache: Dict[str, Any] = {}
_config_cache_timestamp: float = 0
CACHE_TTL = 300

async def get_cached_settings() -> Dict[str, Any]:
    global _config_cache, _config_cache_timestamp
    now = time.time()
    if _config_cache and (now - _config_cache_timestamp < CACHE_TTL):
        return _config_cache
    if not supabase: return {}
    try:
        response = supabase.table("global_config").select("*").execute()
        if response.data:
            new_cache = {row['key']: row['content'] for row in response.data}
            # Attempt to parse JSON content
            for k, v in new_cache.items():
                if isinstance(v, str) and (v.startswith('{') or v.startswith('[')):
                    try: new_cache[k] = json.loads(v)
                    except: pass
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
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error fetching user {telegram_id}: {e}")
    return None

async def upsert_user(telegram_id: int, username: str, first_name: str):
    if not supabase: return None
    data = {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "updated_at": "now()"
    }
    try:
        response = supabase.table("users").upsert(data, on_conflict="telegram_id").execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error upserting user: {e}")
        return None

async def update_user(telegram_id: int, updates: dict):
    if not supabase: return None
    try:
        response = supabase.table("users").update(updates).eq("telegram_id", telegram_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error updating user {telegram_id}: {e}")
    return None

async def register_chat(chat_id: int, chat_type: str, title: str = None):
    if not supabase: return
    try:
        supabase.table("chats").upsert({
            "chat_id": chat_id,
            "chat_type": chat_type,
            "title": title
        }, on_conflict="chat_id").execute()
    except Exception as e:
        logger.error(f"Error registering chat {chat_id}: {e}")

async def get_active_chats() -> List[int]:
    if not supabase: return []
    try:
        response = supabase.table("chats").select("chat_id").execute()
        return [row['chat_id'] for row in response.data] if response.data else []
    except Exception as e:
        logger.error(f"Error fetching chats: {e}")
    return []

async def save_message(telegram_id: int, chat_id: int, role: str, content: str):
    if not supabase: return
    try:
        supabase.table("messages").insert({
            "telegram_id": telegram_id,
            "chat_id": chat_id,
            "role": role,
            "content": content
        }).execute()
    except Exception as e:
        logger.error(f"Error saving message: {e}")

async def save_summary(telegram_id: int, summary_text: str, traits: dict):
    if not supabase: return
    try:
        supabase.table("summaries").insert({
            "telegram_id": telegram_id,
            "summary_text": summary_text,
            "traits_snapshot": traits
        }).execute()
    except Exception as e:
        logger.error(f"Error saving summary: {e}")
