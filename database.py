import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_user(telegram_id: int):
    response = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    if response.data:
        return response.data[0]
    return None

async def create_user(telegram_id: int, username: str, bio_info: str = ""):
    data = {
        "telegram_id": telegram_id,
        "username": username,
        "bio_info": bio_info,
        "personality_traits": {
            "occupation": "Unknown",
            "vibe": "Neutral",
            "humanity_score": 50,
            "interests": [],
            "last_interaction_mood": "Neutral"
        },
        "conversation_summary": "",
        "message_count": 0,
        "voice_count": 0
    }
    response = supabase.table("users").insert(data).execute()
    return response.data[0]

async def update_user(telegram_id: int, updates: dict):
    response = supabase.table("users").update(updates).eq("telegram_id", telegram_id).execute()
    return response.data

async def increment_counters(telegram_id: int):
    user = await get_user(telegram_id)
    if not user:
        return False, False

    new_msg_count = (user.get("message_count", 0) + 1) % 5
    new_voice_count = (user.get("voice_count", 0) + 1) % 3

    updates = {
        "message_count": new_msg_count,
        "voice_count": new_voice_count
    }

    await update_user(telegram_id, updates)

    should_update_personality = (new_msg_count == 0)
    should_send_voice = (new_voice_count == 0)

    return should_update_personality, should_send_voice

async def update_conversation_history(telegram_id: int, new_message: str):
    user = await get_user(telegram_id)
    if not user:
        return

    current_summary = user.get("conversation_summary") or ""
    updated_summary = (current_summary + "\n" + new_message).strip()

    if len(updated_summary) > 5000:
        updated_summary = updated_summary[-5000:]

    await update_user(telegram_id, {"conversation_summary": updated_summary})
