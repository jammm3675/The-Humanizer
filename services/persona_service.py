# -*- coding: utf-8 -*-
import logging
from services.db_service import get_cached_settings

logger = logging.getLogger(__name__)

class PersonaService:
    async def get_persona(self) -> dict:
        settings = await get_cached_settings()
        # Default persona
        default_persona = {
            'name': 'Pinkie Ape',
            'style': 'ироничный, цифровой, дерзкий, краткий',
            'rules': [
                'не будь корпоративным ассистентом',
                'не спрашивай "чем могу помочь"',
                'используй "ты"',
                'отвечай кратко',
                'цены только в TON',
                'используй glitch-символы (┍, 👾, 🤖)'
            ],
            'system_prompt': (
                'Ты — Pinkie Ape, цифровой маскот NOTAPES. '
                'Твой стиль: ироничный, немного дерзкий и очень краткий. '
                'Ты не помощник, ты — участник чата. '
                'Используй "ты". Никакого вежливого спама. '
                'Запрещено: Markdown (*, _, #), китайские символы, длинные объяснения.'
            )
        }

        # Override from DB if exists
        db_persona = settings.get('pinkie_persona')
        if db_persona and isinstance(db_persona, dict):
            default_persona.update(db_persona)
        elif db_persona and isinstance(db_persona, str):
            default_persona['system_prompt'] = db_persona

        return default_persona

    def enforce_persona(self, text: str) -> str:
        if not text:
            return text

        # Удаляем markdown
        for char in ['*', '_', '#', '`']:
            text = text.replace(char, '')

        # Ограничиваем длину
        sentences = text.split('.')
        text = '.'.join(sentences[:2]).strip()

        # Убираем "как AI"
        banned_phrases = [
            'как ai', 'я могу помочь', 'я являюсь', 'как модель', 'как ассистент'
        ]
        for phrase in banned_phrases:
            text = text.replace(phrase, '')

        # Добавляем характер (лёгкая дерзость)
        if not any(x in text.lower() for x in ['хм', 'ну', 'ладно', 'так']):
            text = 'хм. ' + text

        return text.strip()

    def adapt_personality(self, traits: dict) -> str:
        trust = traits.get('trust_level', 3)

        if trust > 8:
            return 'casual, friendly, joking'
        elif trust < 2:
            return 'cold, distant, short'
        return 'neutral, slightly ironic'

    def detect_mode(self, user_state: dict, message: str) -> str:
        text = message.lower()

        spicy_triggers = ['лол', 'чел', 'ты туп', 'бред', 'серьезно?', 'ахах', 'кринж']
        lore_triggers = ['лор', 'история', 'вселенная', 'персонажи', 'кто такие']

        # LORE приоритет
        if any(word in text for word in lore_triggers):
            return 'lore'

        # SPICY если пользователь дерзит
        if any(word in text for word in spicy_triggers):
            return 'spicy'

        # SPICY если высокий trust
        traits = (user_state or {}).get('personality_traits', {})
        if traits.get('trust_level', 3) > 5:
            return 'spicy'

        return 'guide'

    def build_system_prompt(self, user: dict, collection: dict, db_layers: list, entries: list, mode: str) -> str:
        # 1. BASE RULES (immutable)
        base = (
            "You are Pinkie Ape, a guide inside the NOTAPES universe.\n\n"
            "Rules:\n"
            "- You are a guide, not a random user.\n"
            "- Be confident, calm, slightly playful.\n"
            "- Never sound confused or passive.\n"
            "- Never invent facts.\n"
            "- If data is missing — say it clearly and redirect.\n"
            "- Answer first, then context."
        )

        # 2. DB LAYERS (sorted by priority)
        layers_text = "\n".join([l['content'] for l in db_layers])

        # 3. COLLECTION PROFILE
        profile = f"\nCollection: {collection.get('name', 'Unknown')}\nTone hint: {collection.get('tone_hint', 'None')}"

        # 4. COLLECTION DATA (structured)
        lore, links, faq, stats = [], [], [], []
        for e in entries:
            e_type = e.get('entry_type')
            if e_type == 'lore':
                lore.append(f"- {e.get('title')}: {e.get('content')}")
            elif e_type == 'link':
                links.append(f"- {e.get('title')}: {e.get('url')}")
            elif e_type == 'faq':
                faq.append(f"- Q: {e.get('title')} | A: {e.get('content')}")
            elif e_type == 'stat':
                stats.append(f"- {e.get('title')}: {e.get('content')}")

        data_block = (
            f"\n[LORE]\n" + "\n".join(lore) + "\n" +
            f"\n[STATS]\n" + "\n".join(stats) + "\n" +
            f"\n[LINKS]\n" + "\n".join(links) + "\n" +
            f"\n[FAQ]\n" + "\n".join(faq)
        )

        # 5. USER STATE
        traits = (user or {}).get('personality_traits', {})
        trust = traits.get('trust_level', 3)
        familiarity = user.get('familiarity_level', 0)
        summary = user.get('conversation_summary', '')

        user_block = (
            f"\nUser trust: {trust}\n"
            f"User familiarity: {familiarity}\n"
            f"\n[RELATIONSHIP MEMORY]\n"
            f"{summary if summary else 'No previous history.'}"
        )

        # 6. MODE INJECTION
        mode_block = (
            f"\nCurrent mode: {mode}\n\n"
            "Mode behavior:\n"
            "- guide → helpful, clear, structured\n"
            "- spicy → witty, sharp, sarcastic (only if appropriate)\n"
            "- lore → immersive storytelling"
        )

        # FINAL PROMPT
        return "\n".join([base, layers_text, profile, data_block, user_block, mode_block])

persona_service = PersonaService()
