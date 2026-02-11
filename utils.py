KEYWORDS = ["обезьяна", "ape", "бананы", "floor price", "когда минт", "wen lambo", "lfg", "moon", "когда листинг", "банан"]

def calculate_trigger_chance(text: str) -> float:
    if not text:
        return 0.0
    text_lower = text.lower()
    found_keywords = [kw for kw in KEYWORDS if kw in text_lower]
    if not found_keywords:
        return 0.0

    # Return exactly 15% as per user request
    return 0.15
