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
from nft_engine import get_collection_stats

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = int(os.environ.get("TELEGRAM_API_ID"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
COLLECTION_ADDR = "УКАЖИ_ЗДЕСЬ_АДРЕС_NFT_КОЛЛЕКЦИИ"
PORT = int(os.environ.get("PORT", 8080))

client = TelegramClient(StringSession(''), API_ID, API_HASH)

async def health_check(request):
    return web.Response(text="Pinkie Ape is active!", status=200)

async def keep_alive_task():
    """Твой оригинальный механизм для Render."""
    await asyncio.sleep(15)
    async with aiohttp.ClientSession() as session:
        while True:
            url = os.environ.get("RENDER_EXTERNAL_URL")
            if url:
                try:
                    async with session.get(f"{url.rstrip('/')}/health") as resp:
                        if resp.status == 200:
                            logger.info("Self-ping success")
                except Exception as e:
                    logger.error(f"Keep-alive error: {e}")
            await asyncio.sleep(10 * 60)

@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    if not event.is_private: return

    user_id = event.sender_id
    user = await get_user(user_id)
    if not user:
        sender = await event.get_sender()
        user = await create_user(user_id, sender.username or "none", sender.first_name or "Ape")

    nft_stats = await get_collection_stats(COLLECTION_ADDR)
    lore = await get_global_lore()
    
    response_text = await generate_response(event.text, user, lore, nft_stats)
    
    _, _, should_voice = await increment_counters(user_id)
    
    if should_voice:
        voice_path = await text_to_speech(response_text)
        if voice_path:
            await client.send_file(event.chat_id, voice_path, caption=response_text)
            os.remove(voice_path)
            return

    await event.respond(response_text)
    await update_conversation_history(user_id, f"U: {event.text}\nAI: {response_text}")

async def main():
    app = web.Application()
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()

    asyncio.create_task(keep_alive_task())

    await client.start(bot_token=TOKEN)
    logger.info("Bot started on Telethon!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
