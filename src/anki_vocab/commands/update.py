from __future__ import annotations

from dataclasses import replace
from typing import Annotated

import typer
from rich.console import Console

from ..core.ankimapping import card_to_fields, note_to_card_payload, word_field_name
from ..core.audio import build_audio_field
from ..core.cleaning import clean_context
from ..core.config import resolve_config
from ..core.prompting import render_card
from ..integrations.ankiconnect import (
    notes_info,
    update_note_fields,
)
from ..integrations.openai_client import generate_card
from .utils import confirm_menu, note_field_value


def update_command(
    note_id: Annotated[int, typer.Option("--note-id", help="Specific Anki note id.")],
    prompt: Annotated[str | None, typer.Option("--prompt", help="Instruction for updating the note.")] = None,
    note_model: Annotated[str | None, typer.Option("--note-model", help="Anki note model name.")] = None,
    openai_model: Annotated[str | None, typer.Option("--openai-model", help="OpenAI model name.")] = None,
    voice: Annotated[str | None, typer.Option("--voice", help="Edge TTS voice.")] = None,
    rate: Annotated[str | None, typer.Option("--rate", help="Edge TTS rate.")] = None,
    no_tts: Annotated[bool, typer.Option("--no-tts", help="Disable TTS.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview only, no writes.")] = False,
) -> None:
    config = resolve_config()
    config = replace(
        config,
        note_model=note_model or config.note_model,
        openai_model=openai_model or config.openai_model,
        tts_voice=voice or config.tts_voice,
        tts_rate=rate or config.tts_rate,
        tts_enabled=(not no_tts) and config.tts_enabled,
    )

    notes = notes_info(config.ankiconnect_url, [note_id])
    if not notes:
        raise typer.BadParameter(f"Note id {note_id} not found.")
    note = notes[0]

    word_field = word_field_name(config.field_map)
    existing_word = note_field_value(note, word_field)
    if not existing_word:
        raise typer.BadParameter("Selected note is missing the word field.")

    sentence_field = config.field_map.get("context", "Context Sentence")
    existing_sentence = note_field_value(note, sentence_field)
    sentence = existing_sentence or ""

    sentence_clean = clean_context(sentence)
    current_card = note_to_card_payload(note, config.field_map)
    try:
        card = generate_card(
            sentence_clean,
            existing_word,
            model=config.openai_model,
            api_key=config.openai_api_key,
            source_language=config.source_language,
            current_card=current_card,
            user_prompt=prompt,
        )
    except Exception as exc:
        typer.echo(f"OpenAI error: {exc}", err=True)
        raise typer.Exit(code=4) from exc
    console = Console(stderr=True)
    render_card(console, card)

    if dry_run:
        return

    if not confirm_menu("Update this note?", default_yes=False):
        typer.echo("Skipped.", err=True)
        return

    fields = card_to_fields(card, config.field_map)

    if config.tts_enabled:
        existing_audio = note_field_value(note, config.tts_field)
        if not existing_audio:
            tts_text = card.tts_text or card.lemma
            audio_field_value = build_audio_field(
                config.ankiconnect_url,
                tts_text,
                voice=config.tts_voice,
                rate=config.tts_rate,
            )
            fields[config.tts_field] = audio_field_value

    update_note_fields(config.ankiconnect_url, note_id, fields)
    typer.echo(f"Updated note id: {note_id}", err=True)
