from __future__ import annotations

from typing import Annotated

import typer

from ..core.config import resolve_config
from ..core.note_builder import add_card_note
from ..core.schema import parse_card


def add_card_command(
    lemma: Annotated[str, typer.Option(help="Lemma or dictionary form.")],
    target_surface: Annotated[str, typer.Option(help="Exact surface form to cloze.")],
    pos: Annotated[str, typer.Option(help="Part of speech.")],
    meaning_ru: Annotated[str, typer.Option(help="Short Russian meaning.")],
    definition: Annotated[str, typer.Option(help="Short definition.")],
    context_source: Annotated[str, typer.Option(help="Original source sentence or N/A.")],
    context: Annotated[str, typer.Option(help="Card context sentence.")],
    cloze: Annotated[str, typer.Option(help="Single-blank cloze sentence.")],
    context_ru: Annotated[str, typer.Option(help="Russian translation of context.")],
    pattern: Annotated[str, typer.Option(help="Pattern or N/A.")],
    synonyms: Annotated[str, typer.Option(help="Comma-separated synonyms or N/A.")],
    notes: Annotated[str, typer.Option(help="Short note or N/A.")],
    rarity: Annotated[str, typer.Option(help="Rarity label.")],
    cefr: Annotated[str, typer.Option(help="CEFR label.")],
) -> None:
    config = resolve_config()
    try:
        card = parse_card(
            {
                "lemma": lemma,
                "target_surface": target_surface,
                "pos": pos,
                "meaning_ru": meaning_ru,
                "definition": definition,
                "context_source": context_source,
                "context": context,
                "cloze": cloze,
                "context_ru": context_ru,
                "pattern": pattern,
                "synonyms": synonyms,
                "notes": notes,
                "rarity": rarity,
                "cefr": cefr,
            }
        )
    except RuntimeError as exc:
        typer.echo(f"Invalid card fields: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    try:
        note_id = add_card_note(config, card)
    except Exception as exc:
        typer.echo(f"Failed to add note: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(str(note_id))
