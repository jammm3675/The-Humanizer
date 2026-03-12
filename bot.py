# -*- coding: utf-8 -*-
import asyncio
import logging
import time
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from datetime import datetime
from config.settings import config
from handlers.message_handlers import router
from middlewares.antiflood import ThrottlingMiddleware
from services.db_service import get_active_groups, get_global_lore, get_cached_settings
from services.ai_service import ai_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LAST_MESSAGE_TIME = time.time()

async def health_check(request):
    return web.Response(text="I am alive!", status=200)

async def keep_alive_task():
    logger.info("Starting keep-alive background task...")
    await asyncio.sleep(10)
    async with aiohttp.ClientSession() as session:
        while True:
            url = config.RENDER_EXTERNAL_URL
            if not url:
                await asyncio.sleep(60)
                continue
            health_url = f"{url.rstrip('/')}/health"
            try:
                async with session.get(health_url, timeout=30) as response:
                    if response.status == 200:
                        logger.info(f"✅ Keep-alive successful")
            except Exception as e:
                logger.error(f"❌ Keep-alive error: {e}")
            await asyncio.sleep(10 * 60)

async def silence_breaker(bot: Bot):
    """Background task to send messages if the chat is quiet."""
    logger.info("Starting silence breaker task...")
    while True:
        try:
            settings = await get_cached_settings()
            bot_settings = settings.get("bot_settings", {})
            timeout = bot_settings.get("silence_timeout", 3600)

            global LAST_MESSAGE_TIME
            if time.time() - LAST_MESSAGE_TIME > timeout:
                active_chats = await get_active_groups()
                if active_chats:
                    lore = await get_global_lore()
                    text = await ai_service.generate_interjection(lore)
                    if text:
                        # Pick one random active chat to interject
                        chat_id = random.choice(active_chats)
                        try:
                            await bot.send_message(chat_id, text)
                            LAST_MESSAGE_TIME = time.time()
                            logger.info(f"Silence broken in {chat_id}")
                        except Exception as e:
                            logger.error(f"Failed to send silence breaker: {e}")
        except Exception as e:
            logger.error(f"Silence breaker error: {e}")

        await asyncio.sleep(600) # Check every 10 mins

async def main():
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return

    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    # Middleware to track last message time
    @dp.message.outer_middleware()
    async def track_message_time(handler, event, data):
        global LAST_MESSAGE_TIME
        LAST_MESSAGE_TIME = time.time()
        return await handler(event, data)

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
    asyncio.create_task(silence_breaker(bot))

    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    import random # Needed for silence_breaker
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
