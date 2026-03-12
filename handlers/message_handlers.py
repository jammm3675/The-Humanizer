# -*- coding: utf-8 -*-
import random
import logging
import asyncio
from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from services.db_service import (
    get_user, create_user, increment_counters, update_conversation_history,
    update_user, get_global_lore, update_global_lore, register_chat, get_cached_settings
)
from services.ai_service import ai_service
from services.getgems_service import getgems_service

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.voice)
async def handle_voice(message: types.Message):
    response_text = "я не слушаю шум. пиши буквами, если эволюционировал."
    await message.reply(response_text)

@router.message(Command("setlore"))
async def handle_set_lore(message: types.Message):
    user = await get_user(message.from_user.id)
    if not user or not user.get("is_admin"):
        return
    new_lore = message.text.replace("/setlore", "").strip()
    if not new_lore:
        await message.reply("напиши текст лора после команды /setlore")
        return
    await update_global_lore(new_lore)
    await message.reply("✅ глобальный лор обновлен.")

@router.message(F.text.regexp(r"^(EQ|UQ)[a-zA-Z0-9_-]{46}$"))
async def link_wallet(message: types.Message):
    wallet = message.text.strip()
    result = await getgems_service.check_user_nft(wallet)

    if result.get("is_holder"):
        traits = {"status": "Holder", "trust_level": 100, "linked_at": str(datetime.now())}
        await update_user(message.from_user.id, {
            "ton_wallet": wallet,
            "personality_traits": traits
        })
        response = f"база кормится! вижу твои nft. теперь ты официально в семье, {message.from_user.first_name}"
        await message.reply(response.lower())
    else:
        await message.reply("кошелек пустой, бро. минти или покупай на getgems, если хочешь быть в теме")

@router.message(F.chat.type.in_({"private"}))
async def handle_private_message(message: types.Message):
    if not message.text: return
    await process_message(message)

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: types.Message):
    if not message.text: return
    bot_user = await message.bot.get_me()
    settings = await get_cached_settings()
    bot_settings = settings.get("bot_settings", {})
    random_chance = bot_settings.get("random_chance", 0.02)

    is_mentioned = f"@{bot_user.username}" in message.text
    is_reply_to_bot = message.reply_to_message.from_user.id == bot_user.id if message.reply_to_message and message.reply_to_message.from_user else False

    is_joke = any(kw in message.text.lower() for kw in ["анекдот", "шутка", "рассмеши", "joke"])
    should_respond = is_mentioned or is_reply_to_bot or is_joke or (random.random() < random_chance)

    if should_respond:
        await process_message(message)

async def process_message(message: types.Message):
    await register_chat(message.chat.id, message.chat.type)
    user = await get_user(message.from_user.id)
    if not user:
        user = await create_user(
            message.from_user.id,
            message.from_user.username or message.from_user.first_name,
            message.from_user.first_name
        )

    # Holder Re-verification (once a day)
    if user.get("ton_wallet"):
        last_check = user.get("last_stats_check")
        is_stale = True
        if last_check:
            try:
                if isinstance(last_check, str):
                    last_check_dt = datetime.fromisoformat(last_check.replace("Z", "+00:00"))
                else:
                    last_check_dt = last_check
                is_stale = (datetime.now().astimezone() - last_check_dt.astimezone()).days >= 1
            except Exception as e:
                logger.error(f"Date parse error: {e}")

        if is_stale:
            res = await getgems_service.check_user_nft(user["ton_wallet"])
            new_traits = user.get("personality_traits", {})
            if not res.get("is_holder") and new_traits.get("status") == "Holder":
                new_traits["status"] = "Paper Hands"
                await update_user(message.from_user.id, {
                    "personality_traits": new_traits,
                    "last_stats_check": str(datetime.now())
                })
                user["personality_traits"] = new_traits
            elif res.get("is_holder"):
                await update_user(message.from_user.id, {"last_stats_check": str(datetime.now())})

    await update_conversation_history(message.from_user.id, f"User: {message.text}")

    try:
        lore = await get_global_lore()
        response_text = await ai_service.generate_response(message.text, user, lore)
    except Exception as e:
        logger.error(f"AI response error: {e}")
        response_text = "связь прервана..."

    if not response_text: response_text = "..."

    # Update history and counters
    should_update_personality, should_summarize, _ = await increment_counters(message.from_user.id)
    last_bot_messages = user.get("last_bot_messages", [])
    if not isinstance(last_bot_messages, list): last_bot_messages = []

    new_msgs = (last_bot_messages + [
        {"role": "user", "content": message.text},
        {"role": "assistant", "content": response_text}
    ])[-4:]
    await update_user(message.from_user.id, {"last_bot_messages": new_msgs})
    await update_conversation_history(message.from_user.id, f"Pinkie: {response_text}")

    await message.reply(response_text)

    # Background processing
    if should_summarize or should_update_personality:
        updated_user = await get_user(message.from_user.id)
        if not updated_user: return
        if should_summarize:
            asyncio.create_task(summarize_task(updated_user))
        if should_update_personality:
            asyncio.create_task(personality_task(updated_user))

async def summarize_task(user):
    try:
        new_summary = await ai_service.summarize_history(user.get("conversation_summary", ""))
        if new_summary:
            await update_user(user["telegram_id"], {"conversation_summary": new_summary})
    except Exception as e:
        logger.error(f"Summary task failed: {e}")

async def personality_task(user):
    try:
        new_traits = await ai_service.update_personality(user.get("conversation_summary", ""), user.get("personality_traits"))
        if new_traits:
            await update_user(user["telegram_id"], {"personality_traits": new_traits})
    except Exception as e:
        logger.error(f"Personality task failed: {e}")
