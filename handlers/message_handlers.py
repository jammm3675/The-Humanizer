# -*- coding: utf-8 -*-
import random
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from config.settings import config
from services.db_service import get_user, upsert_user, register_chat
from services.memory_service import memory_service
from services.agent_loop import agent_loop
from utils import is_duplicate, can_respond

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.chat.type == "private")
async def handle_private(message: types.Message):
    if is_duplicate(message.message_id):
        return
    await process_message(message)

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group(message: types.Message):
    if is_duplicate(message.message_id):
        return

    bot_obj = await message.bot.get_me()

    is_mentioned = bot_obj.username in (message.text or "")
    is_reply_to_bot = (message.reply_to_message and message.reply_to_message.from_user.id == bot_obj.id)
    is_joke = any(kw in (message.text or "").lower() for kw in ["анекдот", "шутка", "joke", "банан"])
    is_random = random.random() < config.RANDOM_CHANCE

    should_respond = is_mentioned or is_reply_to_bot or is_joke or is_random

    if should_respond:
        if not can_respond(message.chat.id, message.from_user.id):
            return
        await process_message(message)

async def process_message(message: types.Message):
    uid = message.from_user.id
    cid = message.chat.id

    # 1. Register and get user
    await register_chat(cid, message.chat.type, message.chat.title)
    user = await get_user(uid)
    if not user:
        user = await upsert_user(uid, message.from_user.username, message.from_user.first_name)

    # 2. Update memory with user input
    await memory_service.process_memory(uid, cid, "user", message.text)

    # 3. Get response from Agent Loop
    response_text = await agent_loop.run(message.text, user, chat_id=cid)

    if response_text:
        # 4. Save response to memory
        await memory_service.process_memory(uid, cid, "assistant", response_text)

        # 5. Send
        try:
            await message.reply(response_text)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
