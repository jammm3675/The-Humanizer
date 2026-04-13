# -*- coding: utf-8 -*-
from services.db_service import get_cached_settings

class PersonaService:
    async def get_persona(self) -> dict:
        settings = await get_cached_settings()
        # Default persona
        default_persona = {
            "name": "Pinkie Ape",
            "style": "ироничный, цифровой, дерзкий, краткий",
            "rules": [
                "не будь корпоративным ассистентом",
                "не спрашивай 'чем могу помочь'",
                "используй 'ты'",
                "отвечай кратко",
                "цены только в TON",
                "используй glitch-символы (┍, 👾, 🤖)"
            ],
            "system_prompt": (
                "Ты — Pinkie Ape, цифровой маскот NOTAPES. "
                "Твой стиль: ироничный, немного дерзкий и очень краткий. "
                "Ты не помощник, ты — участник чата. "
                "Используй 'ты'. Никакого вежливого спама. "
                "Запрещено: Markdown (*, _, #), китайские символы, длинные объяснения."
            )
        }

        # Override from DB if exists
        db_persona = settings.get("pinkie_persona")
        if db_persona and isinstance(db_persona, dict):
            default_persona.update(db_persona)
        elif db_persona and isinstance(db_persona, str):
            default_persona["system_prompt"] = db_persona

        return default_persona

    def enforce_persona(self, text: str) -> str:
        if not text:
            return text

        # Удаляем markdown
        for char in ["*", "_", "#", "`"]:
            text = text.replace(char, "")

        # Ограничиваем длину
        sentences = text.split(".")
        text = ".".join(sentences[:2]).strip()

        # Убираем "как AI"
        banned_phrases = [
            "как ai", "я могу помочь", "я являюсь", "как модель", "как ассистент"
        ]
        for phrase in banned_phrases:
            text = text.replace(phrase, "")

        # Добавляем характер (лёгкая дерзость)
        if not any(x in text.lower() for x in ["хм", "ну", "ладно", "так"]):
            text = "хм. " + text

        return text.strip()

    def adapt_personality(self, traits: dict) -> str:
        trust = traits.get("trust_level", 30)

        if trust > 80:
            return "casual, friendly, joking"
        elif trust < 20:
            return "cold, distant, short"
        return "neutral, slightly ironic"

persona_service = PersonaService()
