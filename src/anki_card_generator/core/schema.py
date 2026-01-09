from dataclasses import dataclass
from typing import Any


CARD_REQUIRED_FIELDS = (
    "word_base",
    "pos",
    "ru_meaning",
    "definition",
    "context_en",
    "context_ru",
    "rarity",
    "cefr",
)

CARD_OPTIONAL_FIELDS = ("tts_text",)


@dataclass(frozen=True)
class Card:
    word_base: str
    pos: str
    ru_meaning: str
    definition: str
    context_en: str
    context_ru: str
    rarity: str
    cefr: str
    tts_text: str | None = None

    def as_dict(self) -> dict[str, str]:
        data = {
            "word_base": self.word_base,
            "pos": self.pos,
            "ru_meaning": self.ru_meaning,
            "definition": self.definition,
            "context_en": self.context_en,
            "context_ru": self.context_ru,
            "rarity": self.rarity,
            "cefr": self.cefr,
        }
        if self.tts_text:
            data["tts_text"] = self.tts_text
        return data


def parse_card(payload: dict[str, Any]) -> Card:
    missing = [key for key in CARD_REQUIRED_FIELDS if key not in payload]
    if missing:
        raise RuntimeError(f"OpenAI returned invalid card JSON: missing {missing}")

    for key in CARD_REQUIRED_FIELDS:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError(f"OpenAI returned invalid card JSON: {key!r} must be a non-empty string")

    tts_text = payload.get("tts_text")
    if tts_text is not None and (not isinstance(tts_text, str) or not tts_text.strip()):
        raise RuntimeError("OpenAI returned invalid card JSON: 'tts_text' must be a non-empty string")

    return Card(
        word_base=payload["word_base"].strip(),
        pos=payload["pos"].strip(),
        ru_meaning=payload["ru_meaning"].strip(),
        definition=payload["definition"].strip(),
        context_en=payload["context_en"].strip(),
        context_ru=payload["context_ru"].strip(),
        rarity=payload["rarity"].strip(),
        cefr=payload["cefr"].strip(),
        tts_text=tts_text.strip() if isinstance(tts_text, str) else None,
    )
