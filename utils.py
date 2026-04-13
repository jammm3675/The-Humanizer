# -*- coding: utf-8 -*-
import time

# General utilities and constants
KEYWORDS = ["обезьяна", "ape", "бананы", "floor price", "когда минт", "wen lambo", "lfg", "moon", "когда листинг", "банан", "стату", "цены", "кто купил", "анекдот", "шутка", "рассмеши", "joke", "getgems", "холдер", "volume", "объем"]

PROCESSED_MESSAGES = {}
LAST_RESPONSE = {}

def is_duplicate(message_id: int) -> bool:
    now = time.time()

    # Clean up old entries (TTL 60s)
    for mid, ts in list(PROCESSED_MESSAGES.items()):
        if now - ts > 60:
            del PROCESSED_MESSAGES[mid]

    if message_id in PROCESSED_MESSAGES:
        return True

    PROCESSED_MESSAGES[message_id] = now
    return False

def can_respond(chat_id: int, user_id: int) -> bool:
    key = f"{chat_id}:{user_id}"
    now = time.time()

    last = LAST_RESPONSE.get(key)

    if last and now - last < 5:
        return False

    LAST_RESPONSE[key] = now
    return True

def calculate_trigger_chance(text: str) -> float:
    # Logic moved to handlers but kept for compatibility if needed
    if not text: return 0.0
    text_lower = text.lower()
    if any(kw in text_lower for kw in KEYWORDS):
        return 0.15
    return 0.0
