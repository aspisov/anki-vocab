from __future__ import annotations

from dataclasses import replace
from typing import Annotated

import typer

from ..core.ankimapping import card_to_fields, word_field_name
from ..core.audio import build_audio_field
from ..core.cleaning import clean_context
from ..core.config import Config, resolve_config
from rich.console import Console

from ..core.prompting import render_card
from ..integrations.ankiconnect import (
    add_note,
    find_notes,
    notes_info,
    update_note_fields,
)
from ..integrations.openai_client import generate_card
from .utils import select_menu, select_note_id


def _parse_session_line(line: str, last_context: str | None) -> tuple[str, str, str | None]:
    stripped = line.strip()
    if not stripped:
        return "", "", last_context

    if stripped.startswith(":context "):
        return "", "", stripped[len(":context ") :].strip()
    if stripped in {":context"}:
        return "", "", last_context
    if stripped in {":quit", ":q"}:
        raise typer.Exit()

    if "|" in stripped:
        left, right = stripped.split("|", 1)
        context = left.strip()
        word = right.strip()
    else:
        context = ""
        word = stripped

    if not word:
        raise ValueError("Provide a word/phrase after the separator.")
    if not context:
        if "|" in stripped:
            if not last_context:
                raise ValueError("Context is missing. Use ':context ...' or include it before '|'.")
            context = last_context
    else:
        last_context = context

    return context, word, last_context


def _pick_existing_note(config: Config, note_ids: list[int], *, allow_pick: bool) -> int | None:
    if not note_ids:
        return None
    if len(note_ids) == 1 or not allow_pick:
        return note_ids[0]
    notes = notes_info(config.ankiconnect_url, note_ids)
    if not notes:
        return None
    return select_note_id(notes, config.field_map)


def session_command(
    deck: Annotated[str | None, typer.Option("--deck", help="Target Anki deck.")] = None,
    note_model: Annotated[str | None, typer.Option("--note-model", help="Anki note model name.")] = None,
    openai_model: Annotated[str | None, typer.Option("--openai-model", help="OpenAI model name.")] = None,
    voice: Annotated[str | None, typer.Option("--voice", help="Edge TTS voice.")] = None,
    rate: Annotated[str | None, typer.Option("--rate", help="Edge TTS rate.")] = None,
    yes: Annotated[bool, typer.Option("--yes", help="Auto-accept default actions.")] = False,
    no_tts: Annotated[bool, typer.Option("--no-tts", help="Disable TTS.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview only, no writes.")] = False,
) -> None:
    config = resolve_config()
    config = replace(
        config,
        deck=deck or config.deck,
        note_model=note_model or config.note_model,
        openai_model=openai_model or config.openai_model,
        tts_voice=voice or config.tts_voice,
        tts_rate=rate or config.tts_rate,
        tts_enabled=(not no_tts) and config.tts_enabled,
    )

    last_context: str | None = None
    console = Console(stderr=True)
    typer.echo("Session started. Use ':context ...' or ':quit'.", err=True)

    while True:
        try:
            line = input("anki-vocab> ")
        except EOFError:
            typer.echo("Cancelled.", err=True)
            return

        try:
            context, word, last_context = _parse_session_line(line, last_context)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            continue

        if not word:
            continue

        context_clean = clean_context(context)
        existing_note_ids: list[int] = []

        try:
            card = generate_card(
                context_clean,
                word,
                model=config.openai_model,
                api_key=config.openai_api_key,
            )
        except Exception as exc:
            typer.echo(f"OpenAI error: {exc}", err=True)
            continue

        render_card(console, card)

        if dry_run:
            continue

        if not existing_note_ids:
            word_field = word_field_name(config.field_map)
            query = f'note:"{config.note_model}" {word_field}:"{card.word_base}"'
            existing_note_ids = find_notes(config.ankiconnect_url, query)

        has_existing = bool(existing_note_ids)
        default_action = "a" if not has_existing else "s"

        if yes:
            action = default_action
        else:
            actions = ["Add", "Update", "Skip", "Regenerate", "Quit"]
            action_map = ["a", "u", "s", "r", "q"]
            default_index = action_map.index(default_action)
            selected = select_menu(
                "Choose an action",
                actions,
                hint="Use ↑/↓ and Enter.",
                default_index=default_index,
            )
            action = action_map[selected]

        if action == "q":
            return
        if action == "r":
            continue
        if action == "s":
            typer.echo("Skipped.", err=True)
            continue
        if action not in {"a", "u"}:
            typer.echo("Unknown action.", err=True)
            continue

        tts_text = card.tts_text or card.word_base
        fields = card_to_fields(card, config.field_map)

        if action == "a":
            audio_field_value: str | None = None
            if config.tts_enabled and tts_text:
                audio_field_value = build_audio_field(
                    config.ankiconnect_url,
                    tts_text,
                    voice=config.tts_voice,
                    rate=config.tts_rate,
                )
                fields[config.tts_field] = audio_field_value
            note = {
                "deckName": config.deck,
                "modelName": config.note_model,
                "fields": fields,
                "options": {"allowDuplicate": False},
                "tags": ["auto"] + (["tts"] if audio_field_value else []),
            }
            try:
                new_id = add_note(config.ankiconnect_url, note)
            except Exception as exc:
                typer.echo(f"AnkiConnect error: {exc}", err=True)
                continue
            typer.echo(f"Added note id: {new_id}", err=True)
            continue

        if not existing_note_ids:
            typer.echo("No existing note found to update.", err=True)
            continue

        note_id = _pick_existing_note(config, existing_note_ids, allow_pick=True)
        if note_id is None:
            typer.echo("No existing note found to update.", err=True)
            continue

        notes = notes_info(config.ankiconnect_url, [note_id])
        existing_audio = None
        if notes:
            existing_audio = notes[0]["fields"].get(config.tts_field, {}).get("value")

        if config.tts_enabled and tts_text:
            if not existing_audio:
                fields[config.tts_field] = build_audio_field(
                    config.ankiconnect_url,
                    tts_text,
                    voice=config.tts_voice,
                    rate=config.tts_rate,
                )

        update_note_fields(config.ankiconnect_url, note_id, fields)
        typer.echo(f"Updated note id: {note_id}", err=True)
