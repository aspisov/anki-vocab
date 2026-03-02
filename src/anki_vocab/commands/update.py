from __future__ import annotations

from dataclasses import replace
from typing import Annotated

import typer
from rich.console import Console

from ..core.ankimapping import card_to_fields, note_to_card_payload, word_field_name
from ..core.audio import build_audio_fields
from ..core.cleaning import clean_context
from ..core.config import resolve_config
from ..core.prompting import render_card
from ..integrations.ankiconnect import (
    notes_info,
    update_note_fields,
)
from ..integrations.llm_client import generate_card
from .utils import confirm_menu, note_field_value


DEFAULT_UPDATE_PROMPT = "make target predictable from context"


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
        if raw.lower() in {"q"}:
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
    llm_provider: Annotated[
        str | None, typer.Option("--llm-provider", help="LLM provider: openai or ollama.")
    ] = None,
    ollama_model: Annotated[str | None, typer.Option("--ollama-model", help="Ollama model name.")] = None,
    ollama_url: Annotated[str | None, typer.Option("--ollama-url", help="Ollama base URL.")] = None,
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
        llm_provider=llm_provider or config.llm_provider,
        ollama_model=ollama_model or config.ollama_model,
        ollama_url=ollama_url or config.ollama_url,
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
        if effective_prompt is None:
            effective_prompt = DEFAULT_UPDATE_PROMPT

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

        context_field = config.field_map.get("context", "Context Sentence")
        existing_context = note_field_value(note, context_field)
        context_sentence = existing_context or ""

        source_field = config.field_map.get("context_source", "Context Sentence Source")
        existing_source = note_field_value(note, source_field)
        source_context = existing_source or context_sentence

        sentence_clean = clean_context(source_context)
        context_clean = clean_context(context_sentence)
        current_card = note_to_card_payload(note, config.field_map)
        tts_only = (effective_prompt or "").strip().lower() == "tts"
        card = None
        if not tts_only:
            try:
                card = generate_card(
                    config,
                    sentence_clean,
                    existing_word,
                    current_card=current_card,
                    user_prompt=effective_prompt,
                )
            except Exception as exc:
                typer.echo(f"LLM error ({config.llm_provider}): {exc}", err=True)
                raise typer.Exit(code=4) from exc
            console = Console(stderr=True)
            render_card(console, card)

        if dry_run:
            continue

        if not confirm_menu("Update this note?", default_yes=True):
            typer.echo("Skipped.", err=True)
            continue

        fields = {} if tts_only else card_to_fields(card, config.field_map)

        if config.tts_enabled:
            lemma_text = existing_word if tts_only else card.lemma
            context_text = context_clean if tts_only else card.context
            lemma_audio, context_audio = build_audio_fields(
                config.ankiconnect_url,
                lemma=lemma_text,
                context=context_text,
                voice=config.tts_voice,
                rate=config.tts_rate,
            )
            if lemma_audio:
                fields[config.tts_lemma_field] = lemma_audio
            if context_audio:
                fields[config.tts_context_field] = context_audio

        update_note_fields(config.ankiconnect_url, current_note_id, fields)
        typer.echo(f"Updated note id: {current_note_id}", err=True)
