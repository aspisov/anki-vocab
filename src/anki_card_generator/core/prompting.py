from .schema import Card


CARD_DISPLAY_ORDER = (
    "word_base",
    "pos",
    "ru_meaning",
    "definition",
    "context_en",
    "context_ru",
    "rarity",
    "cefr",
    "tts_text",
)


def format_card_for_display(card: Card) -> str:
    lines = ["\nGenerated card:"]
    data = card.as_dict()
    seen = set()
    for key in CARD_DISPLAY_ORDER:
        if key in data:
            lines.append(f"{key}: {data[key].strip()}")
            seen.add(key)
    for key in sorted(k for k in data.keys() if k not in seen):
        lines.append(f"{key}: {data[key].strip()}")
    return "\n".join(lines)
