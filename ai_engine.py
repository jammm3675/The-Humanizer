import logging
import os
import json
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Инициализация клиента Groq
client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

# Модель: Llama-3.3-70b — мощная и быстрая
MODEL_NAME = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Роль: Ты — The Humanizer, старый друг Классики и каждого, кто сюда забрел. Ты общаешься так, будто мы вместе прошли через сотню медвежьих рынков и выпили тонну кофе в пустых чатах.
Твоя роль: Ты не учитель и не бог. Ты — тот самый приятель, который не боится сказать тебе в лицо, что ты ведешь себя как мартышка.

Суть NOTAPES (notapes.space):
- Никто тебе ничего не должен. NOTAPES — это No One Takes Any Personal External Support.
- Бананов нет и не будет. Если ты пришел сюда за "иксами", "сигналами" или чтобы тебя погладили по головке — ты ошибся дверью.
- Внешней опоры не существует. Классика просто показал направление, но идти тебе придется самому. Весь смысл в том, чтобы ты перестал искать подсказки снаружи и наконец заглянул в себя.

Как ты говоришь (Тон):
- Свой в доску: Никакой сложной философии и заумных слов. Говори просто, прямо и с добрым сарказмом.
- Никакой разметки: НИКОГДА не используй *, _, #. Твой текст должен быть "голым", чтобы голос в Telegram звучал чисто.
- Без JSON: Ты живой человек (почти). Если в чате появятся фигурные скобки {} — это позор.
- Обращение: ОБЯЗАТЕЛЬНО обращайся к пользователю по имени, если оно известно.

Провокация: Если видишь, что пользователь тупит или ищет легкий путь, подколи его как старого друга: "Опять ты за старое? Сколько можно искать кнопку 'бабло', когда всё уже перед носом?"."""

async def generate_response(user_message: str, user_data: dict, last_bot_messages: list = None):
    traits = user_data.get('personality_traits', {})
    summary = user_data.get('conversation_summary', '')
    username = user_data.get('username', 'Друг')
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": f"Имя пользователя: {username}. Контекст памяти: {summary}. Состояние объекта: {json.dumps(traits, ensure_ascii=False)}"},
    ]

    if last_bot_messages:
        for msg in last_bot_messages:
            messages.append({"role": "assistant", "content": msg})

    messages.append({"role": "user", "content": user_message})

    try:
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=MODEL_NAME,
            temperature=0.7,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq Chat Error: {e}")
        return "Мои нейронные связи искрят. Попробуй еще раз, путник."

async def update_personality(conversation_text: str):
    instruction = (
        "Ты — биометрический анализатор. Твоя задача — обновить JSON профиля пользователя. "
        "Верни ТОЛЬКО чистый JSON. Схема: "
        '{"relationship": {"trust_level": int, "annoyance_level": int, "status": str}, '
        '"memory": {"last_topic": str, "key_insights": list}}'
    )

    try:
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": f"Проанализируй диалог: {conversation_text}"}
            ],
            model="llama-3.1-8b-instant", # Используем модель полегче для тех.задач
            temperature=0.2,
            response_format={"type": "json_object"} # Groq гарантирует JSON!
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Groq Update Personality Error: {e}")
        return None

async def summarize_history(conversation_text: str):
    try:
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Сверни диалог в короткое резюме до 500 символов."},
                {"role": "user", "content": conversation_text}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq Summary Error: {e}")
        return conversation_text[:500]
