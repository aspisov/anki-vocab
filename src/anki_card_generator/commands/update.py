from __future__ import annotations

from dataclasses import replace
from typing import Annotated, Any

import typer
from rich.console import Console

from ..core.ankimapping import card_to_fields, word_field_name
from ..core.audio import build_audio_field
from ..core.cleaning import clean_context
from ..core.config import Config, resolve_config
from ..core.prompting import render_card
from ..integrations.ankiconnect import (
    find_notes,
    notes_info,
    update_note_fields,
)
from ..integrations.openai_client import generate_card
from .utils import confirm_menu, note_field_value, select_note_id


def _resolve_note_id(
    config: Config, *, word: str | None, note_id: int | None
) -> tuple[int, dict[str, Any]]:
    if note_id is not None:
        notes = notes_info(config.ankiconnect_url, [note_id])
        if not notes:
            raise typer.BadParameter(f"Note id {note_id} not found.")
        return note_id, notes[0]

    if not word:
        raise typer.BadParameter("Provide --word or --note-id.")

    word_field = word_field_name(config.field_map)
    query = f'note:"{config.note_model}" {word_field}:"{word}"'
    note_ids = find_notes(config.ankiconnect_url, query)
    if not note_ids:
        raise typer.BadParameter("No matching notes found.")

    notes = notes_info(config.ankiconnect_url, note_ids)
    if not notes:
        raise typer.BadParameter("No matching notes found.")

    if len(notes) == 1:
        return int(notes[0]["noteId"]), notes[0]

    selected = select_note_id(notes, config.field_map)
    picked = next((note for note in notes if int(note["noteId"]) == selected), None)
    if picked is None:
        notes = notes_info(config.ankiconnect_url, [selected])
        if not notes:
            raise typer.BadParameter("Selected note id not found.")
        return selected, notes[0]
    return selected, picked


def update_command(
    word: Annotated[str | None, typer.Option("--word", help="Word/phrase to update.")] = None,
    note_id: Annotated[
        int | None, typer.Option("--note-id", help="Specific Anki note id.")
    ] = None,
    sentence: Annotated[
        str | None,
        typer.Option("--sentence", help="Context sentence (defaults to note field)."),
    ] = None,
    note_model: Annotated[
        str | None, typer.Option("--note-model", help="Anki note model name.")
    ] = None,
    openai_model: Annotated[
        str | None, typer.Option("--openai-model", help="OpenAI model name.")
    ] = None,
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

    note_id_value, note = _resolve_note_id(config, word=word, note_id=note_id)

    word_field = config.field_map.get("word_base", "Word")
    existing_word = note_field_value(note, word_field)
    if not existing_word:
        raise typer.BadParameter("Selected note is missing the word field.")

    sentence_field = config.field_map.get("context_en", "Context Sentence")
    existing_sentence = note_field_value(note, sentence_field)
    if not sentence:
        if not existing_sentence:
            raise typer.BadParameter(
                "Provide --sentence because the note has no context sentence."
            )
        sentence = existing_sentence

    sentence_clean = clean_context(sentence)
    try:
        card = generate_card(sentence_clean, existing_word, model=config.openai_model)
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
            tts_text = card.tts_text or card.word_base
            audio_field_value = build_audio_field(
                config.ankiconnect_url,
                tts_text,
                voice=config.tts_voice,
                rate=config.tts_rate,
            )
            fields[config.tts_field] = audio_field_value

    update_note_fields(config.ankiconnect_url, note_id_value, fields)
    typer.echo(f"Updated note id: {note_id_value}", err=True)
