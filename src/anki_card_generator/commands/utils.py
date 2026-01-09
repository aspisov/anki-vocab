from typing import Any

import typer


def note_field_value(note: dict[str, Any], field_name: str) -> str | None:
    fields = note.get("fields", {})
    entry = fields.get(field_name)
    if isinstance(entry, dict):
        value = entry.get("value")
        if isinstance(value, str):
            return value.strip()
    return None


def format_note_summary(note: dict[str, Any], field_map: dict[str, str]) -> str:
    word_field = field_map.get("word_base", "Word")
    pos_field = field_map.get("pos", "Part of Speech")
    ru_field = field_map.get("ru_meaning", "Russian Meaning")
    note_id = note.get("noteId", "unknown")
    word = note_field_value(note, word_field) or "?"
    pos = note_field_value(note, pos_field) or "?"
    ru = note_field_value(note, ru_field) or "?"
    return f"{note_id} | {word} | {pos} | {ru}"


def select_note_id(notes: list[dict[str, Any]], field_map: dict[str, str]) -> int:
    typer.echo("Multiple notes found:", err=True)
    for idx, note in enumerate(notes, start=1):
        typer.echo(f"{idx}) {format_note_summary(note, field_map)}", err=True)

    while True:
        choice = input("Pick number or type note-id (q to cancel): ").strip()
        if choice.lower() in {"q", "quit"}:
            raise typer.Abort()
        if not choice:
            continue
        if choice.isdigit():
            number = int(choice)
            if 1 <= number <= len(notes):
                return int(notes[number - 1]["noteId"])
            return number
        typer.echo("Invalid choice. Enter a number or note-id.", err=True)
