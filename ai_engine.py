import logging
logger = logging.getLogger(__name__)
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """Твое имя — The Humanizer. Твоя миссия — превращать 'крипто-обезьян' в осознанных участников NOTAPES... (весь твой промпт)"""

model = genai.GenerativeModel(
    model_name='gemini-2.0-flash',
    system_instruction=SYSTEM_PROMPT
)

async def generate_response(user_message: str, user_data: dict):
    traits = user_data.get('personality_traits', {})
    summary = user_data.get('conversation_summary', '')
    
    # Формируем контекст для модели
    full_prompt = (
        f"Данные объекта:\n"
        f"Личность: {json.dumps(traits, ensure_ascii=False)}\n"
        f"Краткая память: {summary}\n\n"
        f"Сигнал от объекта: {user_message}"
    )

    try:
        response = await model.generate_content_async(
            full_prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.7)
        )
        if not response.candidates:
            logger.warning("AI Response blocked or empty candidates.")
            return "Мои нейронные связи временно затуманены. Попробуйте сменить тему."
        return response.text.strip()
    except Exception as e:
        logger.exception("Full AI Error stack trace:")
        return "Мои нейронные связи временно затуманены вашим примитивизмом. Повторите попытку позже."

async def update_personality(conversation_text: str):
    update_model = genai.GenerativeModel('gemini-2.0-flash')
    
    instruction = (
        "Ты — биометрический анализатор. Твоя задача — обновить JSON профиля пользователя. "
        "Верни ТОЛЬКО валидный JSON без лишнего текста и кавычек ```json."
        "Схема: {\"occupation\": str, \"vibe\": str, \"humanity_score\": {\"value\": int, \"trend\": str, \"last_change_reason\": str}, \"interests\": list, \"evolution_stage\": str}"
    )

    prompt = f"{instruction}\n\nДиалог для анализа:\n{conversation_text}"

    try:
        response = await update_model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        if not response.candidates:
            logger.warning("Personality Update blocked or empty candidates.")
            return None
        return json.loads(response.text)
    except Exception as e:
        logger.exception("Update Personality Error:")
        return None
