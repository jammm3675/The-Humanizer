import asyncio
import logging
import os
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from config.settings import config
from handlers.message_handlers import router
from middlewares.antiflood import ThrottlingMiddleware
from services.db_service import get_active_groups, get_global_lore
from services.ai_service import ai_service


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(request):
    return web.Response(text="I am alive!", status=200)

async def keep_alive_task():
    """Background task to ping the health endpoint."""
    logger.info("Starting keep-alive background task...")
    await asyncio.sleep(10)
    async with aiohttp.ClientSession() as session:
        while True:
            url = config.RENDER_EXTERNAL_URL
            if not url:
                logger.warning("⚠️ RENDER_EXTERNAL_URL not found. Skipping keep-alive.")
                await asyncio.sleep(60)
                continue

            health_url = f"{url.rstrip('/')}/health"
            try:
                async with session.get(health_url, timeout=30) as response:
                    if response.status == 200:
                        logger.info(f"✅ Keep-alive successful to {health_url}")
            except Exception as e:
                logger.error(f"❌ Keep-alive error: {e}")

            await asyncio.sleep(10 * 60)

async def main():
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return

    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    # Register Anti-flood Middleware
    dp.message.middleware(ThrottlingMiddleware(limit=1.5))

    dp.include_router(router)

    app = web.Application()
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.PORT)
    await site.start()

    logger.info(f"Starting web server on port {config.PORT}")
    asyncio.create_task(keep_alive_task())

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
