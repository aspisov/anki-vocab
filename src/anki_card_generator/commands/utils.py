from __future__ import annotations

from contextlib import contextmanager
from typing import Any
import sys
import termios
import tty

import typer
from rich.console import Console, Group
from rich.live import Live
from rich.text import Text


_CONSOLE = Console(stderr=True)


@contextmanager
def _raw_mode() -> None:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _read_key() -> str | None:
    ch = sys.stdin.read(1)
    if ch in {"\r", "\n"}:
        return "enter"
    if ch in {"q", "Q"}:
        return "quit"
    if ch in {"k", "K"}:
        return "up"
    if ch in {"j", "J"}:
        return "down"
    if ch == "\x1b":
        seq = sys.stdin.read(2)
        if seq == "[A":
            return "up"
        if seq == "[B":
            return "down"
        return "quit"
    return None


def _render_menu(
    title: str,
    hint: str | None,
    options: list[str],
    selected: int,
) -> Group:
    lines: list[Text] = []
    lines.append(Text(title, style="bold white"))
    if hint:
        lines.append(Text(hint, style="dim"))
    lines.append(Text(""))
    for idx, option in enumerate(options, start=1):
        is_selected = idx - 1 == selected
        arrow = "> " if is_selected else "  "
        line = Text(arrow, style="green" if is_selected else "dim")
        line.append(f"{idx}. ", style="dim")
        line.append(option, style="green" if is_selected else "white")
        lines.append(line)
    return Group(*lines)


def select_menu(
    title: str,
    options: list[str],
    *,
    hint: str | None = "Use ↑/↓ and Enter.",
    default_index: int = 0,
    allow_quit: bool = True,
) -> int:
    if not sys.stdin.isatty():
        _CONSOLE.print(title)
        if hint:
            _CONSOLE.print(hint, style="dim")
        for idx, option in enumerate(options, start=1):
            _CONSOLE.print(f"{idx}. {option}")
        while True:
            raw = input("Select option: ").strip()
            if allow_quit and raw.lower() in {"q", "quit"}:
                raise typer.Abort()
            if raw.isdigit():
                number = int(raw) - 1
                if 0 <= number < len(options):
                    return number
            _CONSOLE.print("Invalid choice.", style="red")

    selected = max(0, min(default_index, len(options) - 1))
    with _raw_mode(), Live(
        _render_menu(title, hint, options, selected),
        console=_CONSOLE,
        refresh_per_second=30,
    ) as live:
        while True:
            key = _read_key()
            if key is None:
                continue
            if key == "enter":
                return selected
            if key == "quit" and allow_quit:
                raise typer.Abort()
            if key == "up":
                selected = (selected - 1) % len(options)
            if key == "down":
                selected = (selected + 1) % len(options)
            live.update(_render_menu(title, hint, options, selected))


def confirm_menu(title: str, *, default_yes: bool = False) -> bool:
    options = ["Yes", "No"]
    default_index = 0 if default_yes else 1
    return select_menu(title, options, default_index=default_index) == 0


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
    options = [format_note_summary(note, field_map) for note in notes]
    options.append("Enter note-id...")

    selected = select_menu("Pick a note to update", options)
    if selected < len(notes):
        return int(notes[selected]["noteId"])

    while True:
        raw = input("Note id: ").strip()
        if raw.lower() in {"q", "quit"}:
            raise typer.Abort()
        if raw.isdigit():
            return int(raw)
        _CONSOLE.print("Invalid note id.", style="red")
