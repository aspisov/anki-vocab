from __future__ import annotations

from .schema import Card


def card_to_fields(card: Card, field_map: dict[str, str]) -> dict[str, str]:
    data = card.as_dict()
    fields: dict[str, str] = {}
    for key, value in data.items():
        mapped = field_map.get(key)
        if mapped:
            fields[mapped] = value
    return fields


def word_field_name(field_map: dict[str, str]) -> str:
    return field_map.get("word_base", "Word")
