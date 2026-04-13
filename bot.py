# -*- coding: utf-8 -*-
import asyncio
import logging
import time
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from config.settings import config
from handlers.message_handlers import router
from middlewares.antiflood import ThrottlingMiddleware
from services.db_service import get_active_chats
from services.ai_service import ai_service
from services.persona_service import persona_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def health_check(request):
    return web.Response(text="Pinkie Ape is online 🐒", status=200)

async def heartbeat_task():
    logger.info("Starting heartbeat...")
    async with aiohttp.ClientSession() as session:
        while True:
            if config.RENDER_EXTERNAL_URL:
                url = f"{config.RENDER_EXTERNAL_URL.rstrip('/')}/health"
                try:
                    async with session.get(url) as r:
                        if r.status == 200: logger.info("Heartbeat: Ping success")
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
            await asyncio.sleep(600)

async def silence_breaker(bot: Bot):
    logger.info("Starting silence breaker...")
    while True:
        await asyncio.sleep(3600) # Check every hour
        chats = await get_active_chats()
        if chats:
            chat_id = chats[0] # Just an example, could be random
            persona = await persona_service.get_persona()
            msg = [{"role": "system", "content": persona["system_prompt"]}, {"role": "user", "content": "Скажи что-нибудь ироничное в чат."}]
            text = await ai_service.call_llm(msg)
            if text:
                await bot.send_message(chat_id, text)

async def main():
    if not config.TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN is missing!")
        return

    bot = Bot(token=config.TELEGRAM_TOKEN)
    dp = Dispatcher()
    dp.message.middleware(ThrottlingMiddleware(limit=1.5))
    dp.include_router(router)

    # Web Health Server
    app = web.Application()
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.PORT)
    await site.start()

    # Background Tasks
    asyncio.create_task(heartbeat_task())
    asyncio.create_task(silence_breaker(bot))

    logger.info("Pinkie Ape is starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Pinkie Ape offline.")
