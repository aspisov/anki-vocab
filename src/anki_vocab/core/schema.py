from dataclasses import dataclass
from typing import Any


CARD_REQUIRED_FIELDS = (
    "word_base",
    "target_surface",
    "pos",
    "ru_meaning",
    "definition",
    "context_en_source",
    "context_en",
    "cloze_en",
    "context_ru",
    "pattern",
    "synonyms",
    "notes",
    "rarity",
    "cefr",
)

CARD_OPTIONAL_FIELDS = ("tts_text",)


@dataclass(frozen=True)
class Card:
    word_base: str
    target_surface: str
    pos: str
    ru_meaning: str
    definition: str
    context_en_source: str
    context_en: str
    cloze_en: str
    context_ru: str
    pattern: str
    synonyms: str
    notes: str
    rarity: str
    cefr: str
    tts_text: str | None = None

    def as_dict(self) -> dict[str, str]:
        data = {
            "word_base": self.word_base,
            "target_surface": self.target_surface,
            "pos": self.pos,
            "ru_meaning": self.ru_meaning,
            "definition": self.definition,
            "context_en_source": self.context_en_source,
            "context_en": self.context_en,
            "cloze_en": self.cloze_en,
            "context_ru": self.context_ru,
            "pattern": self.pattern,
            "synonyms": self.synonyms,
            "notes": self.notes,
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
        target_surface=payload["target_surface"].strip(),
        pos=payload["pos"].strip(),
        ru_meaning=payload["ru_meaning"].strip(),
        definition=payload["definition"].strip(),
        context_en_source=payload["context_en_source"].strip(),
        context_en=payload["context_en"].strip(),
        cloze_en=payload["cloze_en"].strip(),
        context_ru=payload["context_ru"].strip(),
        pattern=payload["pattern"].strip(),
        synonyms=payload["synonyms"].strip(),
        notes=payload["notes"].strip(),
        rarity=payload["rarity"].strip(),
        cefr=payload["cefr"].strip(),
        tts_text=tts_text.strip() if isinstance(tts_text, str) else None,
    )
