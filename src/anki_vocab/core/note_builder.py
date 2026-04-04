from __future__ import annotations

from typing import Any

from ..integrations.ankiconnect import add_note
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


def build_add_note_payload(config: Config, card: Card) -> dict[str, Any]:
    fields = card_to_fields(card, config.field_map)
    lemma_audio, context_audio = attach_audio_fields(
        config,
        fields,
        lemma=card.lemma,
        context=card.context,
    )
    return {
        "deckName": config.deck,
        "modelName": config.note_model,
        "fields": fields,
        "options": {"allowDuplicate": False},
        "tags": ["auto"] + (["tts"] if (lemma_audio or context_audio) else []),
    }


def add_card_note(config: Config, card: Card) -> int:
    return add_note(config.ankiconnect_url, build_add_note_payload(config, card))
