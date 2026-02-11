import asyncio
import logging
import os
import aiohttp
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Импорт вашей логики
from database import get_user, create_user, update_user, increment_counters, update_conversation_history, get_global_lore
from ai_engine import generate_response
from voice_engine import text_to_speech
from utils import calculate_trigger_chance

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
API_ID = int(os.environ.get("TELEGRAM_API_ID"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

# Инициализация клиента Telethon (используем пустую строку для бота)
client = TelegramClient(StringSession(''), API_ID, API_HASH)

async def health_check(request):
    return web.Response(text="Pinkie Ape is online!", status=200)

@client.on(events.NewMessage(incoming=True))
async def handle_message(event):
    if not event.is_private:
        return # Работаем только в ЛС (или добавьте логику для групп)

    user_id = event.sender_id
    text = event.text
    
    # 1. Работа с БД
    user = await get_user(user_id)
    if not user:
        sender = await event.get_sender()
        user = await create_user(user_id, sender.username or "none", sender.first_name or "Ape")

    # 2. Генерация ответа через Groq
    lore = await get_global_lore()
    response_text = await generate_response(text, user, lore)

    # 3. Логика счетчиков и голоса (каждое 7-е сообщение)
    should_profile, should_sum, should_voice = await increment_counters(user_id)
    
    if should_voice:
        voice_path = await text_to_speech(response_text)
        if voice_path:
            await client.send_file(event.chat_id, voice_path, caption=response_text)
            os.remove(voice_path)
            return

    await event.respond(response_text)
    await update_conversation_history(user_id, f"User: {text}\nAI: {response_text}")

async def main():
    # Запуск веб-сервера для Render Health Check
    app = web.Application()
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Health check server started on port {PORT}")

    # Запуск Telethon бота
    await client.start(bot_token=TOKEN)
    logger.info("Telethon Bot is running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
