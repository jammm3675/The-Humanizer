# -*- coding: utf-8 -*-
import random
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from services.db_service import get_user, create_user, increment_counters, update_conversation_history, update_user, get_global_lore, update_global_lore, register_chat
from services.ai_service import ai_service
from utils import calculate_trigger_chance

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.voice)
async def handle_voice(message: types.Message):
    """Игнорирование голосовых сообщений с ироничным ответом."""
    response_text = "Я не слушаю шум. Пиши буквами, если эволюционировал."
    await message.reply(response_text)

@router.message(Command("setlore"))
async def handle_set_lore(message: types.Message):
    """Обновление глобального лора админом."""
    user = await get_user(message.from_user.id)
    if not user or not user.get("is_admin"):
        return

    new_lore = message.text.replace("/setlore", "").strip()
    if not new_lore:
        await message.reply("Напиши текст лора после команды /setlore")
        return

    await update_global_lore(new_lore)
    await message.reply("✅ Глобальный лор обновлен.")

@router.message(F.chat.type.in_({"private"}))
async def handle_private_message(message: types.Message):
    if not message.text:
        return
    await process_message(message)

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: types.Message):
    if not message.text:
        return

    bot_user = await message.bot.get_me()

    # Check for triggers
    is_mentioned = f"@{bot_user.username}" in message.text
    is_reply_to_bot = False
    if message.reply_to_message and message.reply_to_message.from_user:
        is_reply_to_bot = message.reply_to_message.from_user.id == bot_user.id

    chance = calculate_trigger_chance(message.text)
    is_joke = any(kw in message.text.lower() for kw in ["анекдот", "шутка", "рассмеши", "joke"])
    should_respond = is_mentioned or is_reply_to_bot or is_joke or (random.random() < chance)

    if should_respond:
        await process_message(message)

async def process_message(message: types.Message):
    # Register chat
    await register_chat(message.chat.id, message.chat.type)
    # Process user in DB
    user = await get_user(message.from_user.id)
    if not user:
        user = await create_user(
            message.from_user.id,
            message.from_user.username or message.from_user.first_name,
            message.from_user.first_name
        )

    # Update conversation history with user message
    await update_conversation_history(message.from_user.id, f"User: {message.text}")

    # Generate AI response
    try:
        lore = await get_global_lore()
        response_text = await ai_service.generate_response(message.text, user, lore)
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        response_text = "┏{🧿}.. Канал Acid Pixel перегружен. Попробуй еще раз."

    if not response_text:
        response_text = "..."

    # Increment counters and check for periodic tasks
    should_update_personality, should_summarize, _ = await increment_counters(message.from_user.id)

    # Update last bot messages (history for context)
    last_bot_messages = user.get("last_bot_messages", [])
    if not isinstance(last_bot_messages, list):
        last_bot_messages = []

    new_history_item_user = {"role": "user", "content": message.text}
    new_history_item_bot = {"role": "assistant", "content": response_text}

    new_last_bot_messages = (last_bot_messages + [new_history_item_user, new_history_item_bot])[-4:]
    await update_user(message.from_user.id, {"last_bot_messages": new_last_bot_messages})

    # Update conversation history summary
    await update_conversation_history(message.from_user.id, f"The Humanizer: {response_text}")

    # Send response
    await message.reply(response_text)

    # Background tasks
    if should_summarize or should_update_personality:
        updated_user = await get_user(message.from_user.id)
        if not updated_user: return

        if should_summarize:
            try:
                new_summary = await ai_service.summarize_history(updated_user.get("conversation_summary", ""))
                if new_summary:
                    await update_user(message.from_user.id, {"conversation_summary": new_summary})
            except Exception as e:
                logger.error(f"Summary task failed: {e}")

        if should_update_personality:
            try:
                new_traits = await ai_service.update_personality(updated_user.get("conversation_summary", ""), updated_user.get("personality_traits"))
                if new_traits:
                    await update_user(message.from_user.id, {"personality_traits": new_traits})
            except Exception as e:
                logger.error(f"Personality task failed: {e}")
