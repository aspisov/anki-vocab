from __future__ import annotations

from typing import Any

from .schema import CARD_OPTIONAL_FIELDS, CARD_REQUIRED_FIELDS, Card


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


def _note_field_value(note: dict[str, Any], field_name: str) -> str | None:
    fields = note.get("fields", {})
    entry = fields.get(field_name)
    if isinstance(entry, dict):
        value = entry.get("value")
        if isinstance(value, str):
            return value.strip()
    return None


def note_to_card_payload(note: dict[str, Any], field_map: dict[str, str]) -> dict[str, str]:
    payload: dict[str, str] = {}
    for key in (*CARD_REQUIRED_FIELDS, *CARD_OPTIONAL_FIELDS):
        field_name = field_map.get(key)
        if not field_name:
            continue
        value = _note_field_value(note, field_name)
        payload[key] = value if value is not None else ""
    return payload
