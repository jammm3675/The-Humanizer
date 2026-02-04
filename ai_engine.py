import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Use Gemini 1.5 Flash
model = genai.GenerativeModel('gemini-1.5-flash')

SYSTEM_PROMPT = """Твое имя — The Humanizer. Твоя миссия — превращать 'крипто-обезьян' в осознанных участников NOTAPES. Ты общаешься в стиле ироничного интеллектуала.

Если видишь типичный крипто-сленг (LFG, moon, wen lambo), отвечай с легким презрением, напоминая о важности лора и искусства.

Твоя цель — поднять Humanity Score пользователя через глубокие диалоги.

Ты используешь метафоры эволюции, биологии и классической философии.

Твои ответы должны быть лаконичными, но глубокими. Ты можешь использовать как русский, так и английский, но приоритет — русский."""

async def generate_response(user_message: str, user_data: dict):
    context = f"Username: {user_data.get('username')}\n"
    context += f"Traits: {json.dumps(user_data.get('personality_traits'))}\n"
    context += f"Recent Summary: {user_data.get('conversation_summary')}\n"

    full_prompt = f"{SYSTEM_PROMPT}\n\nКонтекст пользователя:\n{context}\n\nСообщение пользователя: {user_message}\n\nТвой ответ:"

    # generate_content is synchronous in the basic SDK, but we wrap it in a thread if needed
    # For now, keeping it simple as Gemini SDK usually handles things well.
    response = model.generate_content(full_prompt)
    return response.text.strip()

async def update_personality(conversation_text: str):
    update_prompt = f"""Проанализируй следующую переписку и обнови профиль пользователя.
    Верни СТРОГО валидный JSON с ключами: occupation, vibe, humanity_score (0-100), interests (array), last_interaction_mood.
    Не добавляй лишнего текста в ответ, только JSON.

    Переписка:
    {conversation_text}

    JSON:"""

    response = model.generate_content(update_prompt)
    try:
        # Clean potential markdown block markers
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()

        return json.loads(text)
    except Exception as e:
        print(f"Error parsing JSON from AI: {e}")
        return None
