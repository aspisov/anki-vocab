from __future__ import annotations

import json
from typing import Annotated, Any

import typer

from ..core.ankimapping import note_to_card_payload
from ..core.config import resolve_config
from ..integrations.ankiconnect import notes_info


def show_card_command(
    note_id: Annotated[int, typer.Argument(help="Anki note id.")],
) -> None:
    config = resolve_config()
    notes = notes_info(config.ankiconnect_url, [note_id])
    if not notes:
        typer.echo(f"Note id {note_id} not found.", err=True)
        raise typer.Exit(code=1)

    note = notes[0]
    payload: dict[str, Any] = {
        "note_id": note["noteId"],
        "model_name": note.get("modelName", ""),
        "tags": note.get("tags", []),
        "card": note_to_card_payload(note, config.field_map),
    }
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
