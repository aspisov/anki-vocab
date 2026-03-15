from dataclasses import asdict, dataclass
from typing import Any


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
        return asdict(self)


CARD_FIELDS = tuple(Card.__dataclass_fields__)


def parse_card(payload: dict[str, Any]) -> Card:
    missing = [key for key in CARD_FIELDS if key not in payload]
    if missing:
        raise RuntimeError(f"Model returned invalid card JSON: missing {missing}")

    for key in CARD_FIELDS:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError(f"Model returned invalid card JSON: {key!r} must be a non-empty string")

    return Card(**{key: payload[key].strip() for key in CARD_FIELDS})
