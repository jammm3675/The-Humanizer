import sys

content = open('services/db_service.py', 'r').read()

new_methods = """
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
"""

with open('services/db_service.py', 'a') as f:
    f.write(new_methods)

print("db_service.py updated successfully")
