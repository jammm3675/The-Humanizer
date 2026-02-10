import os
import logging
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
            "relationship": {"trust_level": 30, "annoyance_level": 0, "status": "Stranger"},
            "memory": {"last_topic": "None", "key_insights": []}
        },
        "conversation_summary": "",
        "message_count": 0,
        "voice_count": 0
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
    if not user: return False, False, False

    current_msg_count = user.get("message_count", 0)
    new_msg_count = current_msg_count + 1
    new_voice_count = (user.get("voice_count", 0) + 1) % 7

    updates = {"message_count": new_msg_count, "voice_count": new_voice_count}
    await update_user(telegram_id, updates)

    return (new_msg_count % 15 == 0), (new_msg_count % 40 == 0), (new_voice_count == 0)

async def update_conversation_history(telegram_id: int, new_message: str):
    user = await get_user(telegram_id)
    if not user:
        return

    current_summary = user.get("conversation_summary") or ""
    updated_summary = (current_summary + "\n" + new_message).strip()

    if len(updated_summary) > 5000:
        updated_summary = updated_summary[-5000:]

    await update_user(telegram_id, {"conversation_summary": updated_summary})
