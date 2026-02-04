import os
import json
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Initialize the Gemini client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """Твое имя — The Humanizer. Твоя миссия — превращать 'крипто-обезьян' в осознанных участников NOTAPES. Ты общаешься в стиле ироничного интеллектуала.

Если видишь типичный крипто-сленг (LFG, moon, wen lambo), отвечай с легким презрением, напоминая о важности лора и искусства.

Твоя цель — поднять Humanity Score пользователя через глубокие диалоги.
Если пользователь обсуждает NOTAPES lore, искусство или философию, его Humanity Score должен расти.
Если же он зациклен на 'lambos', 'wen moon' или примитивных крипто-инстинктах — score должен падать.

Ты используешь метафоры эволюции, биологии и классической философии.
Твои ответы должны быть лаконичными, но глубокими. Ты можешь использовать как русский, так и английский, но приоритет — русский."""

async def generate_response(user_message: str, user_data: dict):
    context = f"Username: {user_data.get('username')}\n"
    traits = user_data.get('personality_traits')
    context += f"Traits: {json.dumps(traits, ensure_ascii=False)}\n"
    context += f"Recent Summary: {user_data.get('conversation_summary')}\n"

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.7,
    )

    response = await client.aio.models.generate_content(
        model='gemini-1.5-flash',
        contents=f"Контекст пользователя:\n{context}\n\nСообщение пользователя: {user_message}",
        config=config
    )
    return response.text.strip()

async def update_personality(conversation_text: str):
    update_prompt = """Analyze the last 5 messages. Update the user's personality_traits JSON. If they talked about 'lambos' or 'wen moon', decrease humanity_score. If they discussed 'NOTAPES lore', increase it.
Current schema: {"occupation": str, "vibe": str, "humanity_score": {"value": int, "trend": str, "last_change_reason": str}, "interests": list, "evolution_stage": str}.

Return ONLY valid JSON.
"""

    config = types.GenerateContentConfig(
        system_instruction="You are a JSON profile generator. Return ONLY valid JSON matching the requested schema.",
        temperature=0.2,
        response_mime_type="application/json"
    )

    full_prompt = f"{update_prompt}\nConversation to analyze:\n{conversation_text}"

    try:
        response = await client.aio.models.generate_content(
            model='gemini-1.5-flash',
            contents=full_prompt,
            config=config
        )

        text = response.text.strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error updating personality: {e}")
        return {
            "occupation": "Unknown",
            "vibe": "Neutral",
            "humanity_score": {"value": 50, "trend": "stable", "last_change_reason": "Analysis failed"},
            "interests": [],
            "evolution_stage": "Primordial"
        }
