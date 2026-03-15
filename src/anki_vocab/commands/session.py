from __future__ import annotations

from dataclasses import dataclass

import typer
from rich.console import Console

from ..core.ankimapping import card_to_fields, note_field_value, note_to_card_payload, word_field_name
from ..core.audio import build_audio_fields
from ..core.cleaning import clean_context
from ..core.config import Config, resolve_config
from ..core.prompting import render_card
from ..integrations.ankiconnect import add_note, find_notes, notes_info, update_note_fields
from ..integrations.llm_client import generate_card
from .utils import confirm_menu, select_menu, select_note_id

DEFAULT_UPDATE_PROMPT = "make target predictable from context"


@dataclass(frozen=True)
class AddRequest:
    context: str
    word: str


@dataclass(frozen=True)
class UpdateRequest:
    note_id: int
    prompt: str


@dataclass(frozen=True)
class QuitRequest:
    pass


def _parse_session_line(line: str) -> AddRequest | UpdateRequest | QuitRequest | None:
    stripped = line.strip()
    if not stripped:
        return None
    if stripped == "q":
        return QuitRequest()
    if "|" in stripped:
        left, right = stripped.split("|", 1)
        left = left.strip()
        right = right.strip()
        if left.isdigit():
            if not right:
                raise ValueError("Prompt is missing after '|'.")
            return UpdateRequest(note_id=int(left), prompt=right)
        if not right:
            raise ValueError("Provide a word/phrase after the separator.")
        if not left:
            raise ValueError("Context is missing. Include it before '|'.")
        return AddRequest(context=left, word=right)
    if stripped.isdigit():
        return UpdateRequest(note_id=int(stripped), prompt=DEFAULT_UPDATE_PROMPT)
    return AddRequest(context="", word=stripped)


def _pick_existing_note(config: Config, note_ids: list[int], *, allow_pick: bool) -> int | None:
    if not note_ids:
        return None
    if len(note_ids) == 1 or not allow_pick:
        return note_ids[0]
    notes = notes_info(config.ankiconnect_url, note_ids)
    if not notes:
        return None
    return select_note_id(notes, config.field_map)


def _attach_audio_fields(
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


def _run_add_request(config: Config, console: Console, request: AddRequest) -> bool:
    context_clean = clean_context(request.context)
    current_card: dict[str, str] | None = None
    user_prompt: str | None = None
    existing_note_ids: list[int] | None = None
    last_lemma: str | None = None

    while True:
        try:
            card = generate_card(
                config,
                context_clean,
                request.word,
                current_card=current_card,
                user_prompt=user_prompt,
            )
        except Exception as exc:
            typer.echo(f"LLM error ({config.llm_provider}): {exc}", err=True)
            return True

        render_card(console, card)

        if existing_note_ids is None or last_lemma != card.lemma:
            word_field = word_field_name(config.field_map)
            query = f'note:"{config.note_model}" {word_field}:"{card.lemma}"'
            existing_note_ids = find_notes(config.ankiconnect_url, query)
            last_lemma = card.lemma

        has_existing = bool(existing_note_ids)
        default_action = "a" if not has_existing else "s"
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
            return False
        if action == "r":
            feedback = input("Feedback for regeneration (optional): ").strip()
            current_card = card.as_dict()
            user_prompt = feedback or None
            continue
        if action == "s":
            typer.echo("Skipped.", err=True)
            return True
        if action not in {"a", "u"}:
            typer.echo("Unknown action.", err=True)
            continue

        fields = card_to_fields(card, config.field_map)

        if action == "a":
            lemma_audio, context_audio = _attach_audio_fields(
                config,
                fields,
                lemma=card.lemma,
                context=card.context,
            )
            note = {
                "deckName": config.deck,
                "modelName": config.note_model,
                "fields": fields,
                "options": {"allowDuplicate": False},
                "tags": ["auto"] + (["tts"] if (lemma_audio or context_audio) else []),
            }
            try:
                new_id = add_note(config.ankiconnect_url, note)
            except Exception as exc:
                typer.echo(f"AnkiConnect error: {exc}", err=True)
                continue
            typer.echo(f"Added note id: {new_id}", err=True)
            return True

        if not existing_note_ids:
            typer.echo("No existing note found to update.", err=True)
            return True

        note_id = _pick_existing_note(config, existing_note_ids, allow_pick=True)
        if note_id is None:
            typer.echo("No existing note found to update.", err=True)
            return True

        _attach_audio_fields(
            config,
            fields,
            lemma=card.lemma,
            context=card.context,
        )
        update_note_fields(config.ankiconnect_url, note_id, fields)
        typer.echo(f"Updated note id: {note_id}", err=True)
        return True


def _run_update_request(config: Config, console: Console, request: UpdateRequest) -> None:
    notes = notes_info(config.ankiconnect_url, [request.note_id])
    if not notes:
        typer.echo(f"Note id {request.note_id} not found.", err=True)
        return
    note = notes[0]

    word_field = word_field_name(config.field_map)
    existing_word = note_field_value(note, word_field)
    if not existing_word:
        typer.echo("Selected note is missing the word field.", err=True)
        return

    context_field = config.field_map.get("context", "Context Sentence")
    context_sentence = note_field_value(note, context_field) or ""

    source_field = config.field_map.get("context_source", "Context Sentence Source")
    source_context = note_field_value(note, source_field) or context_sentence

    sentence_clean = clean_context(source_context)
    context_clean = clean_context(context_sentence)
    current_card = note_to_card_payload(note, config.field_map)
    tts_only = request.prompt.strip().lower() == "tts"
    card = None
    if not tts_only:
        try:
            card = generate_card(
                config,
                sentence_clean,
                existing_word,
                current_card=current_card,
                user_prompt=request.prompt,
            )
        except Exception as exc:
            typer.echo(f"LLM error ({config.llm_provider}): {exc}", err=True)
            return
        render_card(console, card)

    if not confirm_menu("Update this note?", default_yes=True):
        typer.echo("Skipped.", err=True)
        return

    fields = {} if tts_only else card_to_fields(card, config.field_map)
    lemma_text = existing_word if tts_only else card.lemma
    context_text = context_clean if tts_only else card.context
    _attach_audio_fields(
        config,
        fields,
        lemma=lemma_text,
        context=context_text,
    )
    update_note_fields(config.ankiconnect_url, request.note_id, fields)
    typer.echo(f"Updated note id: {request.note_id}", err=True)


def session_command() -> None:
    config = resolve_config()
    console = Console(stderr=True)
    typer.echo("Session started. Use 'q' to quit.", err=True)

    while True:
        try:
            line = input("anki-vocab> ")
        except EOFError:
            typer.echo("Cancelled.", err=True)
            return

        try:
            request = _parse_session_line(line)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            continue

        if request is None:
            continue
        if isinstance(request, QuitRequest):
            return
        if isinstance(request, UpdateRequest):
            _run_update_request(config, console, request)
            continue
        if not _run_add_request(config, console, request):
            return
