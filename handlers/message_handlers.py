import random
import os
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from database import get_user, create_user, increment_counters, update_conversation_history, update_user
from ai_engine import generate_response, update_personality
from voice_engine import text_to_speech
from utils import calculate_trigger_chance

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: types.Message):
    bot_user = await message.bot.get_me()
    # Check for mention or keyword trigger
    is_mentioned = False
    if message.text:
        is_mentioned = f"@{bot_user.username}" in message.text

    chance = 0.0
    if not is_mentioned and message.text:
        chance = calculate_trigger_chance(message.text)

    should_respond = is_mentioned or (random.random() < chance)

    if not should_respond:
        return

    # Process user in DB
    user = await get_user(message.from_user.id)
    if not user:
        user = await create_user(message.from_user.id, message.from_user.username or message.from_user.first_name)

    # Update conversation history with user message
    await update_conversation_history(message.from_user.id, f"User: {message.text}")

    # Generate AI response
    try:
        response_text = await generate_response(message.text, user)
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        response_text = "Мои мыслительные цепи временно перегружены примитивностью этого мира. Попробуй позже."

    # Increment counters and check for triggers
    should_update_personality, should_send_voice = await increment_counters(message.from_user.id)

    # Update conversation history with Bot message
    await update_conversation_history(message.from_user.id, f"The Humanizer: {response_text}")

    # Send response
    if should_send_voice:
        try:
            voice_path = await text_to_speech(response_text)
            voice_file = FSInputFile(voice_path)
            await message.answer_voice(voice_file)
            if os.path.exists(voice_path):
                os.remove(voice_path)
        except Exception as e:
            logger.error(f"Voice generation failed: {e}")
            # Fallback to text if voice fails
            await message.answer(response_text)
    else:
        await message.answer(response_text)

    # Periodic personality update
    if should_update_personality:
        updated_user = await get_user(message.from_user.id)
        if updated_user:
            summary = updated_user.get("conversation_summary", "")
            try:
                new_traits = await update_personality(summary)
                if new_traits:
                    await update_user(message.from_user.id, {"personality_traits": new_traits})
            except Exception as e:
                logger.error(f"Personality update failed: {e}")
