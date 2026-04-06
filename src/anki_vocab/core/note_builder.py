from __future__ import annotations

from typing import Any

from ..integrations.ankiconnect import add_note, update_note_fields
from .ankimapping import card_to_fields
from .audio import build_audio_fields
from .config import Config
from .schema import Card


def attach_audio_fields(
    config: Config,
    fields: dict[str, str],
    *,
    lemma: str,
    context: str,
) -> tuple[str | None, str | None]:
    if not config.tts_enabled:
        return None, None
    lemma_audio, context_audio = build_audio_fields(
        config.ankiconnect_url,
        lemma=lemma,
        context=context,
        voice=config.tts_voice,
        rate=config.tts_rate,
    )
    if lemma_audio:
        fields[config.tts_lemma_field] = lemma_audio
    if context_audio:
        fields[config.tts_context_field] = context_audio
    return lemma_audio, context_audio


def build_note_fields(config: Config, card: Card) -> tuple[dict[str, str], bool]:
    fields = card_to_fields(card, config.field_map)
    lemma_audio, context_audio = attach_audio_fields(
        config,
        fields,
        lemma=card.lemma,
        context=card.context,
    )
    return fields, bool(lemma_audio or context_audio)


def build_add_note_payload(config: Config, card: Card) -> dict[str, Any]:
    fields, has_audio = build_note_fields(config, card)
    return {
        "deckName": config.deck,
        "modelName": config.note_model,
        "fields": fields,
        "options": {"allowDuplicate": False},
        "tags": ["auto"] + (["tts"] if has_audio else []),
    }


def add_card_note(config: Config, card: Card) -> int:
    return add_note(config.ankiconnect_url, build_add_note_payload(config, card))


def update_card_note(config: Config, note_id: int, card: Card) -> None:
    fields, _ = build_note_fields(config, card)
    update_note_fields(config.ankiconnect_url, note_id, fields)
