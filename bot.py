import asyncio
import logging
import os
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers.message_handlers import router

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
RENDER_SERVICE_NAME = os.environ.get("RENDER_SERVICE_NAME")
PORT = int(os.environ.get("PORT", 8080))

async def health_check(request):
    return web.Response(text="I am alive!", status=200)

async def keep_alive_task():
    """Background task to ping the health endpoint."""
    logger.info("Starting keep-alive background task...")

    # Wait a bit for the server to start
    await asyncio.sleep(10)

    async with aiohttp.ClientSession() as session:
        while True:
            url = RENDER_EXTERNAL_URL
            if not url and RENDER_SERVICE_NAME:
                url = f"https://{RENDER_SERVICE_NAME}.onrender.com"

            if not url:
                logger.warning("⚠️ Neither RENDER_EXTERNAL_URL nor RENDER_SERVICE_NAME found. Skipping keep-alive attempt. Retrying in 60s.")
                await asyncio.sleep(60)
                continue

            health_url = f"{url.rstrip('/')}/health"
            try:
                async with session.get(health_url, timeout=30) as response:
                    if response.status == 200:
                        logger.info(f"✅ Keep-alive successful to {health_url}")
                    else:
                        logger.warning(f"⚠️ Keep-alive to {health_url} returned status {response.status}")
            except Exception as e:
                logger.error(f"❌ Keep-alive error for {health_url}: {e}")

            logger.info("...keep-alive sleeping for 10 minutes...")
            await asyncio.sleep(10 * 60)

async def main():
    # Initialize Bot and Dispatcher
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # Web server for health check
    app = web.Application()
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)

    # Start tasks
    logger.info(f"Starting web server on port {PORT}")
    await site.start()

    # Start keep-alive
    asyncio.create_task(keep_alive_task())

    # Start Polling
    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
