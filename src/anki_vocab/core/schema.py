from dataclasses import dataclass
from typing import Any


CARD_REQUIRED_FIELDS = (
    "lemma",
    "target_surface",
    "pos",
    "meaning_ru",
    "definition",
    "context_source",
    "context",
    "cloze",
    "context_ru",
    "pattern",
    "synonyms",
    "notes",
    "rarity",
    "cefr",
)

CARD_OPTIONAL_FIELDS: tuple[str, ...] = ()


@dataclass(frozen=True)
class Card:
    lemma: str
    target_surface: str
    pos: str
    meaning_ru: str
    definition: str
    context_source: str
    context: str
    cloze: str
    context_ru: str
    pattern: str
    synonyms: str
    notes: str
    rarity: str
    cefr: str
    def as_dict(self) -> dict[str, str]:
        data = {
            "lemma": self.lemma,
            "target_surface": self.target_surface,
            "pos": self.pos,
            "meaning_ru": self.meaning_ru,
            "definition": self.definition,
            "context_source": self.context_source,
            "context": self.context,
            "cloze": self.cloze,
            "context_ru": self.context_ru,
            "pattern": self.pattern,
            "synonyms": self.synonyms,
            "notes": self.notes,
            "rarity": self.rarity,
            "cefr": self.cefr,
        }
        return data


def parse_card(payload: dict[str, Any]) -> Card:
    missing = [key for key in CARD_REQUIRED_FIELDS if key not in payload]
    if missing:
        raise RuntimeError(f"Model returned invalid card JSON: missing {missing}")

    for key in CARD_REQUIRED_FIELDS:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError(f"Model returned invalid card JSON: {key!r} must be a non-empty string")

    return Card(
        lemma=payload["lemma"].strip(),
        target_surface=payload["target_surface"].strip(),
        pos=payload["pos"].strip(),
        meaning_ru=payload["meaning_ru"].strip(),
        definition=payload["definition"].strip(),
        context_source=payload["context_source"].strip(),
        context=payload["context"].strip(),
        cloze=payload["cloze"].strip(),
        context_ru=payload["context_ru"].strip(),
        pattern=payload["pattern"].strip(),
        synonyms=payload["synonyms"].strip(),
        notes=payload["notes"].strip(),
        rarity=payload["rarity"].strip(),
        cefr=payload["cefr"].strip(),
    )
