import sys
import re

with open('handlers/message_handlers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
content = content.replace(
    'from services.db_service import get_user, create_user, increment_counters, update_conversation_history, update_user, get_global_lore, update_global_lore',
    'from services.db_service import get_user, create_user, increment_counters, update_conversation_history, update_user, get_global_lore, update_global_lore, register_chat'
)

# 2. Add register_chat call in process_message
content = content.replace(
    'async def process_message(message: types.Message):',
    'async def process_message(message: types.Message):\n    # Register chat\n    await register_chat(message.chat.id, message.chat.type)'
)

# 3. Update message.reply calls
# Replace 'await message.reply(response_text)' with 'await message.reply(response_text, parse_mode="Markdown")'
# Also replace 'await message.reply("Я не слушаю шум. Пиши буквами, если эволюционировал.")' etc?
# I'll do a generic replace for message.reply(

def add_parse_mode(match):
    call = match.group(0)
    if 'parse_mode' in call:
        return call
    return call.rstrip(')') + ', parse_mode="Markdown")'

content = re.sub(r'await message\.reply\([^)]+\)', add_parse_mode, content)

with open('handlers/message_handlers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("handlers/message_handlers.py updated successfully")
