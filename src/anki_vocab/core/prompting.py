from rich.console import Console
from rich.text import Text

from .schema import Card


CARD_DISPLAY_ORDER = (
    "word_base",
    "pos",
    "ru_meaning",
    "definition",
    "context_en",
    "context_ru",
    "notes",
    "rarity",
    "cefr",
    "tts_text",
)


def format_card_for_display(card: Card) -> Text:
    data = card.as_dict()
    keys = [key for key in CARD_DISPLAY_ORDER if key in data]
    keys.extend(sorted(k for k in data.keys() if k not in keys))

    max_key_len = max((len(key) for key in keys), default=0)
    gutter = max_key_len + 2

    output = Text()
    output.append("\nGenerated card:\n", style="bold white")
    for key in keys:
        value = data[key].strip()
        output.append(key, style="white")
        output.append(" " * (gutter - len(key)))
        output.append(value, style="dim")
        output.append("\n")
    return output


def render_card(console: Console, card: Card) -> None:
    console.print(format_card_for_display(card), highlight=False)
