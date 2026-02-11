import asyncio
import logging
import os
import aiohttp
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv
from database import get_user, create_user, increment_counters, update_conversation_history, get_global_lore
from ai_engine import generate_response
from voice_engine import text_to_speech

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config из .env
API_ID = int(os.environ.get("TELEGRAM_API_ID"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") [cite: 1]
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") [cite: 1]
RENDER_SERVICE_NAME = os.environ.get("RENDER_SERVICE_NAME")
PORT = int(os.environ.get("PORT", 8080))

client = TelegramClient(StringSession(''), API_ID, API_HASH)

async def health_check(request):
    """Эндпоинт для проверки жизнеспособности."""
    return web.Response(text="Pinkie Ape is alive!", status=200)

async def keep_alive_task():
    """Фоновая задача, которая пингует сама себя, чтобы Render не усыплял бота."""
    logger.info("Starting keep-alive background task...")
    await asyncio.sleep(15) # Даем серверу время завестись

    async with aiohttp.ClientSession() as session:
        while True:
            url = RENDER_EXTERNAL_URL
            if not url and RENDER_SERVICE_NAME:
                url = f"https://{RENDER_SERVICE_NAME}.onrender.com"

            if url:
                health_url = f"{url.rstrip('/')}/health"
                try:
                    async with session.get(health_url, timeout=30) as response:
                        if response.status == 200:
                            logger.info(f"✅ Self-ping success: {health_url}")
                except Exception as e:
                    logger.error(f"❌ Keep-alive error: {e}")
            
            await asyncio.sleep(10 * 60) # Спим 10 минут


@client.on(events.NewMessage(incoming=True))
async def handle_message(event):
    if not event.is_private: return
    
    user_id = event.sender_id
    user = await get_user(user_id)
    if not user:
        sender = await event.get_sender()
        user = await create_user(user_id, sender.username or "none", sender.first_name or "Ape")

    lore = await get_global_lore()
    response_text = await generate_response(event.text, user, lore)
    
    _, _, should_voice = await increment_counters(user_id)
    
    if should_voice:
        voice_path = await text_to_speech(response_text)
        if voice_path:
            await client.send_file(event.chat_id, voice_path, caption=response_text)
            if os.path.exists(voice_path): os.remove(voice_path)
            return

    await event.respond(response_text)
    await update_conversation_history(user_id, f"User: {event.text}\nAI: {response_text}")


async def main():
    app = web.Application()
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    asyncio.create_task(keep_alive_task())

    await client.start(bot_token=TOKEN)
    logger.info("Pinkie Ape (Telethon) is running with Keep-Alive...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
