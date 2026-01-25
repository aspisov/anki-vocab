from __future__ import annotations

from dataclasses import replace
from typing import Annotated

import typer
from rich.console import Console

from ..core.ankimapping import card_to_fields, note_to_card_payload, word_field_name
from ..core.audio import audio_tag_count, build_audio_bundle
from ..core.cleaning import clean_context
from ..core.config import resolve_config
from ..core.prompting import render_card
from ..integrations.ankiconnect import (
    notes_info,
    update_note_fields,
)
from ..integrations.openai_client import generate_card
from .utils import confirm_menu, note_field_value


def _parse_note_id_input(raw: str) -> tuple[int, str | None]:
    if "|" in raw:
        left, right = raw.split("|", 1)
        note_id = left.strip()
        prompt = right.strip()
        if not prompt:
            raise ValueError("Prompt is missing after '|'.")
    else:
        note_id = raw.strip()
        prompt = None

    if not note_id.isdigit():
        raise ValueError("Invalid note id.")

    return int(note_id), prompt


def _prompt_note_id() -> tuple[int | None, str | None]:
    while True:
        raw = input("Note id (or 'q' to quit): ").strip()
        if raw.lower() in {"q", "quit"}:
            return None, None
        try:
            return _parse_note_id_input(raw)
        except ValueError as exc:
            typer.echo(str(exc), err=True)


def update_command(
    note_id: Annotated[int | None, typer.Option("--note-id", help="Specific Anki note id.")] = None,
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

    base_prompt = prompt

    while True:
        if note_id is not None:
            current_note_id = note_id
            inline_prompt = None
        else:
            current_note_id, inline_prompt = _prompt_note_id()
        note_id = None
        if current_note_id is None:
            return
        effective_prompt = base_prompt if base_prompt is not None else inline_prompt

        notes = notes_info(config.ankiconnect_url, [current_note_id])
        if not notes:
            typer.echo(f"Note id {current_note_id} not found.", err=True)
            continue
        note = notes[0]

        word_field = word_field_name(config.field_map)
        existing_word = note_field_value(note, word_field)
        if not existing_word:
            typer.echo("Selected note is missing the word field.", err=True)
            continue

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
                user_prompt=effective_prompt,
            )
        except Exception as exc:
            typer.echo(f"OpenAI error: {exc}", err=True)
            raise typer.Exit(code=4) from exc
        console = Console(stderr=True)
        render_card(console, card)

        if dry_run:
            continue

        if not confirm_menu("Update this note?", default_yes=True):
            typer.echo("Skipped.", err=True)
            continue

        fields = card_to_fields(card, config.field_map)

        if config.tts_enabled:
            existing_audio = note_field_value(note, config.tts_field)
            if audio_tag_count(existing_audio) < 2:
                audio_field_value = build_audio_bundle(
                    config.ankiconnect_url,
                    lemma=card.lemma,
                    context=card.context,
                    voice=config.tts_voice,
                    rate=config.tts_rate,
                )
                if audio_field_value:
                    fields[config.tts_field] = audio_field_value

        update_note_fields(config.ankiconnect_url, current_note_id, fields)
        typer.echo(f"Updated note id: {current_note_id}", err=True)
