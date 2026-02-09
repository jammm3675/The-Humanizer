import logging
logger = logging.getLogger(__name__)
import os
import json
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

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

model = genai.GenerativeModel(
    model_name='models/gemini-1.5-flash',
    system_instruction=SYSTEM_PROMPT
)

async def generate_response(user_message: str, user_data: dict, last_bot_messages: list = None):
    traits = user_data.get('personality_traits', {})
    summary = user_data.get('conversation_summary', '')
    username = user_data.get('username', 'Друг')
    
    bot_history = ""
    if last_bot_messages:
        bot_history = "\nТвои последние ответы для контекста:\n" + "\n".join([f"- {msg}" for msg in last_bot_messages])

    # Формируем контекст для модели
    full_prompt = (
        f"Данные объекта:\n"
        f"Имя пользователя: {username}\n"
        f"Личность: {json.dumps(traits, ensure_ascii=False)}\n"
        f"Краткая память: {summary}\n"
        f"{bot_history}\n\n"
        f"Сигнал от объекта: {user_message}"
    )

    try:
        response = await model.generate_content_async(
            full_prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.8)
        )
        if not response.candidates:
            logger.warning("AI Response blocked or empty candidates.")
            return "Мои нейронные связи временно затуманены. Попробуй позже."
        return response.text.strip()
    except exceptions.ResourceExhausted:
        logger.error("Quota exceeded!")
        return "Друг, я слишком много сегодня думал. Мои нейроны перегрелись, дай мне отдохнуть пару минут, и продолжим."
    except Exception as e:
        logger.exception("Full AI Error stack trace:")
        return "Мои нейронные связи временно затуманены. Повтори позже."

async def update_personality(conversation_text: str):
    update_model = genai.GenerativeModel('models/gemini-1.5-flash')
    
    instruction = (
        "Ты — биометрический сканер. Анализируй диалог и возвращай ТОЛЬКО JSON по схеме relationship и memory. "
        "Оценивай уровень доверия и раздражения бота к пользователю. "
        "Верни ТОЛЬКО валидный JSON без лишнего текста и кавычек. "
        "Схема: {\"relationship\": {\"trust_level\": int, \"annoyance_level\": int, \"status\": str}, \"memory\": {\"last_topic\": str, \"key_insights\": list}}"
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

async def summarize_history(conversation_text: str):
    summarize_model = genai.GenerativeModel('models/gemini-1.5-flash')

    instruction = (
        "Ты — аналитик памяти. Твоя задача — сжать историю диалога, сохранив ключевые факты о пользователе, "
        "его интересах и текущем контексте общения. Верни краткое резюме (до 500 символов)."
    )

    prompt = f"{instruction}\n\nДиалог для сжатия:\n{conversation_text}"

    try:
        response = await summarize_model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.3)
        )
        if not response.candidates:
            return conversation_text[:1000]
        return response.text.strip()
    except Exception as e:
        logger.exception("Summarize History Error:")
        return conversation_text[:1000]
