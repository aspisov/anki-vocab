from __future__ import annotations

from typing import Any

import pytest

from anki_vocab.commands import update as update_module
from anki_vocab.core.config import Config, DEFAULT_FIELD_MAP
from anki_vocab.core.schema import Card


def _sample_card() -> Card:
    return Card(
        lemma="run",
        target_surface="run",
        pos="verb",
        meaning_ru="бежать",
        definition="to move swiftly",
        context_source="Book",
        context="I run.",
        cloze="I ____.",
        context_ru="Я бегу.",
        pattern="run fast",
        synonyms="sprint",
        notes="",
        rarity="common",
        cefr="A1",
    )


def test_update_command_uses_note_id_and_field_map(monkeypatch: pytest.MonkeyPatch) -> None:
    field_map = dict(DEFAULT_FIELD_MAP)
    field_map["lemma"] = "Headword"
    field_map["context"] = "Sentence"

    config = Config(
        deck="Test",
        note_model="English",
        field_map=field_map,
        ankiconnect_url="http://anki.test",
        source_language="en",
        openai_api_key="sk-test",
        openai_model="gpt-test",
        tts_voice="voice",
        tts_rate="+0%",
        tts_field="Audio",
        tts_enabled=False,
    )

    captured: dict[str, Any] = {}

    def fake_notes_info(url: str, note_ids: list[int]) -> list[dict[str, Any]]:
        captured["notes_info"] = {"url": url, "note_ids": note_ids}
        return [
            {
                "noteId": note_ids[0],
                "fields": {
                    "Headword": {"value": "run"},
                    "Sentence": {"value": "I run."},
                },
            }
        ]

    def fake_generate_card(sentence: str, word: str, **kwargs: Any) -> Card:
        captured["sentence"] = sentence
        captured["word"] = word
        captured["prompt"] = kwargs.get("user_prompt")
        return _sample_card()

    def fake_update_note_fields(url: str, note_id: int, fields: dict[str, str]) -> None:
        captured["update_note_fields"] = {"url": url, "note_id": note_id, "fields": fields}

    monkeypatch.setattr(update_module, "resolve_config", lambda: config)
    monkeypatch.setattr(update_module, "notes_info", fake_notes_info)
    monkeypatch.setattr(update_module, "generate_card", fake_generate_card)
    monkeypatch.setattr(update_module, "update_note_fields", fake_update_note_fields)
    monkeypatch.setattr(update_module, "confirm_menu", lambda *args, **kwargs: True)
    monkeypatch.setattr(update_module, "render_card", lambda *args, **kwargs: None)
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: "q")

    update_module.update_command(note_id=123, prompt="Refine the definition.")

    assert captured["notes_info"]["note_ids"] == [123]
    assert captured["sentence"] == "I run."
    assert captured["word"] == "run"
    assert captured["prompt"] == "Refine the definition."
    assert captured["update_note_fields"]["note_id"] == 123


def test_update_command_uses_inline_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        deck="Test",
        note_model="English",
        field_map=DEFAULT_FIELD_MAP,
        ankiconnect_url="http://anki.test",
        source_language="en",
        openai_api_key="sk-test",
        openai_model="gpt-test",
        tts_voice="voice",
        tts_rate="+0%",
        tts_field="Audio",
        tts_enabled=False,
    )

    captured: dict[str, Any] = {}

    def fake_notes_info(url: str, note_ids: list[int]) -> list[dict[str, Any]]:
        return [
            {
                "noteId": note_ids[0],
                "fields": {
                    "Word": {"value": "run"},
                    "Context Sentence": {"value": "I run."},
                },
            }
        ]

    def fake_generate_card(sentence: str, word: str, **kwargs: Any) -> Card:
        captured["prompt"] = kwargs.get("user_prompt")
        return _sample_card()

    def fake_update_note_fields(url: str, note_id: int, fields: dict[str, str]) -> None:
        captured["update_note_fields"] = {"note_id": note_id, "fields": fields}

    inputs = iter(["123 | Update only notes", "q"])
    monkeypatch.setattr(update_module, "resolve_config", lambda: config)
    monkeypatch.setattr(update_module, "notes_info", fake_notes_info)
    monkeypatch.setattr(update_module, "generate_card", fake_generate_card)
    monkeypatch.setattr(update_module, "update_note_fields", fake_update_note_fields)
    monkeypatch.setattr(update_module, "confirm_menu", lambda *args, **kwargs: True)
    monkeypatch.setattr(update_module, "render_card", lambda *args, **kwargs: None)
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: next(inputs))

    update_module.update_command()

    assert captured["prompt"] == "Update only notes"
    assert captured["update_note_fields"]["note_id"] == 123
