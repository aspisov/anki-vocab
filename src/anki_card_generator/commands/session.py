from __future__ import annotations

from dataclasses import replace
import typer

from ..core.ankimapping import card_to_fields, word_field_name
from ..core.audio import build_audio_field
from ..core.cleaning import clean_context
from ..core.config import Config, resolve_config
from ..core.prompting import format_card_for_display
from ..integrations.ankiconnect import add_note, find_notes, notes_info, update_note_fields
from ..integrations.openai_client import generate_card
from .utils import select_note_id


_POLICIES = {"ask", "never", "always"}


def _validate_policy(value: str, name: str) -> str:
    if value not in _POLICIES:
        raise typer.BadParameter(f"{name} must be one of: ask, never, always")
    return value


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
                raise ValueError(
                    "Context is missing. Use ':context ...' or include it before '|'."
                )
            context = last_context
    else:
        last_context = context

    return context, word, last_context


def _pick_existing_note(
    config: Config, note_ids: list[int], *, allow_pick: bool
) -> int | None:
    if not note_ids:
        return None
    if len(note_ids) == 1 or not allow_pick:
        return note_ids[0]
    notes = notes_info(config.ankiconnect_url, note_ids)
    if not notes:
        return None
    return select_note_id(notes, config.field_map)


def session_command(
    deck: str | None = typer.Option(None, "--deck", help="Target Anki deck."),
    note_model: str | None = typer.Option(
        None, "--note-model", help="Anki note model name."
    ),
    openai_model: str | None = typer.Option(
        None, "--openai-model", help="OpenAI model name."
    ),
    voice: str | None = typer.Option(None, "--voice", help="Edge TTS voice."),
    rate: str | None = typer.Option(None, "--rate", help="Edge TTS rate."),
    yes: bool = typer.Option(False, "--yes", help="Auto-accept default actions."),
    update_policy: str | None = typer.Option(
        None, "--update-policy", help="ask|never|always"
    ),
    overwrite_audio: str | None = typer.Option(
        None, "--overwrite-audio", help="ask|never|always"
    ),
    no_tts: bool = typer.Option(False, "--no-tts", help="Disable TTS."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only, no writes."),
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
        session_update_policy=_validate_policy(
            update_policy or config.session_update_policy, "update-policy"
        ),
        session_overwrite_audio=_validate_policy(
            overwrite_audio or config.session_overwrite_audio, "overwrite-audio"
        ),
    )

    last_context: str | None = None
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

        if not dry_run and config.session_update_policy == "never":
            word_field = word_field_name(config.field_map)
            query = f'note:"{config.note_model}" {word_field}:"{word}"'
            existing_note_ids = find_notes(config.ankiconnect_url, query)
            if existing_note_ids:
                typer.echo("Skipping: note already exists.", err=True)
                continue

        try:
            card = generate_card(context_clean, word, model=config.openai_model)
        except Exception as exc:
            typer.echo(f"OpenAI error: {exc}", err=True)
            continue

        typer.echo(format_card_for_display(card), err=True)

        if dry_run:
            continue

        if not existing_note_ids:
            word_field = word_field_name(config.field_map)
            query = f'note:"{config.note_model}" {word_field}:"{card.word_base}"'
            existing_note_ids = find_notes(config.ankiconnect_url, query)

        has_existing = bool(existing_note_ids)
        default_action = "a"
        if has_existing:
            default_action = "u" if config.session_update_policy == "always" else "s"

        if yes:
            action = default_action
        else:
            options = "a)dd, u)pdate, s)kip, r)egen, q)uit"
            prompt = f"Action [{default_action}] ({options}): "
            try:
                response = input(prompt).strip().lower()
            except EOFError:
                typer.echo("Cancelled.", err=True)
                return
            action = response or default_action

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
            should_overwrite = config.session_overwrite_audio == "always"
            if config.session_overwrite_audio == "ask" and existing_audio:
                try:
                    overwrite_choice = input("Overwrite audio? [y/N]: ").strip().lower()
                except EOFError:
                    typer.echo("Cancelled.", err=True)
                    return
                should_overwrite = overwrite_choice in {"y", "yes"}

            if not existing_audio or should_overwrite:
                fields[config.tts_field] = build_audio_field(
                    config.ankiconnect_url,
                    tts_text,
                    voice=config.tts_voice,
                    rate=config.tts_rate,
                )

        update_note_fields(config.ankiconnect_url, note_id, fields)
        typer.echo(f"Updated note id: {note_id}", err=True)
