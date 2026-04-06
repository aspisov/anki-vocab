from __future__ import annotations

import typer

from .card_fields import (
    CefrOption,
    ClozeOption,
    ContextOption,
    ContextRuOption,
    ContextSourceOption,
    DefinitionOption,
    LemmaOption,
    MeaningRuOption,
    NotesOption,
    PatternOption,
    PosOption,
    RarityOption,
    SynonymsOption,
    TargetSurfaceOption,
    parse_explicit_card,
)
from ..core.config import resolve_config
from ..core.note_builder import add_card_note


def add_card_command(
    lemma: LemmaOption,
    target_surface: TargetSurfaceOption,
    pos: PosOption,
    meaning_ru: MeaningRuOption,
    definition: DefinitionOption,
    context_source: ContextSourceOption,
    context: ContextOption,
    cloze: ClozeOption,
    context_ru: ContextRuOption,
    pattern: PatternOption,
    synonyms: SynonymsOption,
    notes: NotesOption,
    rarity: RarityOption,
    cefr: CefrOption,
) -> None:
    config = resolve_config()
    card = parse_explicit_card(
        lemma=lemma,
        target_surface=target_surface,
        pos=pos,
        meaning_ru=meaning_ru,
        definition=definition,
        context_source=context_source,
        context=context,
        cloze=cloze,
        context_ru=context_ru,
        pattern=pattern,
        synonyms=synonyms,
        notes=notes,
        rarity=rarity,
        cefr=cefr,
    )
    try:
        note_id = add_card_note(config, card)
    except Exception as exc:
        typer.echo(f"Failed to add note: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(str(note_id))
