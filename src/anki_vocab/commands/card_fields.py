from __future__ import annotations

from typing import Annotated

import typer

from ..core.schema import Card, parse_card

LemmaOption = Annotated[str, typer.Option(help="Lemma or dictionary form.")]
TargetSurfaceOption = Annotated[str, typer.Option(help="Exact surface form to cloze.")]
PosOption = Annotated[str, typer.Option(help="Part of speech.")]
MeaningRuOption = Annotated[str, typer.Option(help="Short Russian meaning.")]
DefinitionOption = Annotated[str, typer.Option(help="Short definition.")]
ContextSourceOption = Annotated[str, typer.Option(help="Original source sentence or N/A.")]
ContextOption = Annotated[str, typer.Option(help="Card context sentence.")]
ClozeOption = Annotated[str, typer.Option(help="Single-blank cloze sentence.")]
ContextRuOption = Annotated[str, typer.Option(help="Russian translation of context.")]
PatternOption = Annotated[str, typer.Option(help="Pattern or N/A.")]
SynonymsOption = Annotated[str, typer.Option(help="Comma-separated synonyms or N/A.")]
NotesOption = Annotated[str, typer.Option(help="Short note or N/A.")]
RarityOption = Annotated[str, typer.Option(help="Rarity label.")]
CefrOption = Annotated[str, typer.Option(help="CEFR label.")]


def parse_explicit_card(
    *,
    lemma: str,
    target_surface: str,
    pos: str,
    meaning_ru: str,
    definition: str,
    context_source: str,
    context: str,
    cloze: str,
    context_ru: str,
    pattern: str,
    synonyms: str,
    notes: str,
    rarity: str,
    cefr: str,
) -> Card:
    try:
        return parse_card(
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
