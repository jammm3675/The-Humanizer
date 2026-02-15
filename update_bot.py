import sys
import os

with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
new_imports = "from services.db_service import get_active_groups, get_global_lore\nfrom services.ai_service import ai_service\n"
content = content.replace('from middlewares.antiflood import ThrottlingMiddleware',
                         'from middlewares.antiflood import ThrottlingMiddleware\n' + new_imports)

# 2. Add interjection_task
interjection_task_code = """
async def interjection_task(bot: Bot):
    \"\"\"Background task to send periodic jokes/memes to chats.\"\"\"
    logger.info("Starting interjection background task...")
    while True:
        try:
            # Wait for 1 hour
            await asyncio.sleep(3600)

            active_groups = await get_active_groups()
            if not active_groups:
                logger.info("No active groups for interjections.")
                continue

            lore = await get_global_lore()
            interjection = await ai_service.generate_interjection(lore)

            if interjection:
                for chat_id in active_groups:
                    try:
                        await bot.send_message(chat_id, interjection, parse_mode="Markdown")
                        logger.info(f"Sent interjection to chat {chat_id}")
                    except Exception as e:
                        logger.error(f"Failed to send interjection to {chat_id}: {e}")

        except Exception as e:
            logger.error(f"Error in interjection_task: {e}")
"""

# Insert before 'async def main():'
content = content.replace('async def main():', interjection_task_code + '\nasync def main():')

# 3. Start task in main()
content = content.replace('asyncio.create_task(keep_alive_task())',
                         'asyncio.create_task(keep_alive_task())\n    asyncio.create_task(interjection_task(bot))')

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("bot.py updated successfully")
