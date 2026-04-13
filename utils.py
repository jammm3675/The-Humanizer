# -*- coding: utf-8 -*-
# General utilities and constants
KEYWORDS = ["обезьяна", "ape", "бананы", "floor price", "когда минт", "wen lambo", "lfg", "moon", "когда листинг", "банан", "стату", "цены", "кто купил", "анекдот", "шутка", "рассмеши", "joke", "getgems", "холдер", "volume", "объем"]

def calculate_trigger_chance(text: str) -> float:
    # Logic moved to handlers but kept for compatibility if needed
    if not text: return 0.0
    text_lower = text.lower()
    if any(kw in text_lower for kw in KEYWORDS):
        return 0.15
    return 0.0
