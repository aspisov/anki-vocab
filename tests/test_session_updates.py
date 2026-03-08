from __future__ import annotations

from typing import Any

import pytest

from anki_vocab.commands import session as session_module
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


def _config(*, field_map: dict[str, str] | None = None, tts_enabled: bool = False) -> Config:
    return Config(
        deck="Test",
        note_model="English",
        field_map=field_map or dict(DEFAULT_FIELD_MAP),
        ankiconnect_url="http://anki.test",
        source_language="en",
        llm_provider="openai",
        openai_api_key="sk-test",
        openai_model="gpt-test",
        ollama_url="http://ollama.test",
        ollama_model="gemma-test",
        tts_voice="voice",
        tts_rate="+0%",
        tts_lemma_field="Audio Lemma",
        tts_context_field="Audio Context",
        tts_enabled=tts_enabled,
    )


def test_session_update_uses_bare_note_id_and_default_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config()
    captured: dict[str, Any] = {}

    def fake_notes_info(_url: str, note_ids: list[int]) -> list[dict[str, Any]]:
        return [
            {
                "noteId": note_ids[0],
                "fields": {
                    "Word": {"value": "run"},
                    "Context Sentence": {"value": "I run."},
                },
            }
        ]

    def fake_generate_card(_config: Config, sentence: str, word: str, **kwargs: Any) -> Card:
        captured["sentence"] = sentence
        captured["word"] = word
        captured["prompt"] = kwargs.get("user_prompt")
        return _sample_card()

    def fake_update_note_fields(_url: str, note_id: int, fields: dict[str, str]) -> None:
        captured["update_note_fields"] = {"note_id": note_id, "fields": fields}

    inputs = iter(["123", "q"])
    monkeypatch.setattr(session_module, "resolve_config", lambda: config)
    monkeypatch.setattr(session_module, "notes_info", fake_notes_info)
    monkeypatch.setattr(session_module, "generate_card", fake_generate_card)
    monkeypatch.setattr(session_module, "update_note_fields", fake_update_note_fields)
    monkeypatch.setattr(session_module, "confirm_menu", lambda *args, **kwargs: True)
    monkeypatch.setattr(session_module, "render_card", lambda *args, **kwargs: None)
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: next(inputs))

    session_module.session_command()

    assert captured["sentence"] == "I run."
    assert captured["word"] == "run"
    assert captured["prompt"] == session_module.DEFAULT_UPDATE_PROMPT
    assert captured["update_note_fields"]["note_id"] == 123


def test_session_update_uses_inline_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config()
    captured: dict[str, Any] = {}

    def fake_notes_info(_url: str, note_ids: list[int]) -> list[dict[str, Any]]:
        return [
            {
                "noteId": note_ids[0],
                "fields": {
                    "Word": {"value": "run"},
                    "Context Sentence": {"value": "I run."},
                },
            }
        ]

    def fake_generate_card(_config: Config, sentence: str, word: str, **kwargs: Any) -> Card:
        captured["prompt"] = kwargs.get("user_prompt")
        return _sample_card()

    def fake_update_note_fields(_url: str, note_id: int, fields: dict[str, str]) -> None:
        captured["update_note_fields"] = {"note_id": note_id, "fields": fields}

    inputs = iter(["123 | Update only notes", "q"])
    monkeypatch.setattr(session_module, "resolve_config", lambda: config)
    monkeypatch.setattr(session_module, "notes_info", fake_notes_info)
    monkeypatch.setattr(session_module, "generate_card", fake_generate_card)
    monkeypatch.setattr(session_module, "update_note_fields", fake_update_note_fields)
    monkeypatch.setattr(session_module, "confirm_menu", lambda *args, **kwargs: True)
    monkeypatch.setattr(session_module, "render_card", lambda *args, **kwargs: None)
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: next(inputs))

    session_module.session_command()

    assert captured["prompt"] == "Update only notes"
    assert captured["update_note_fields"]["note_id"] == 123


def test_session_update_prefers_context_source_for_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    field_map = dict(DEFAULT_FIELD_MAP)
    field_map["lemma"] = "Headword"
    field_map["context"] = "Sentence"
    field_map["context_source"] = "Source Sentence"
    config = _config(field_map=field_map)
    captured: dict[str, Any] = {}

    def fake_notes_info(_url: str, note_ids: list[int]) -> list[dict[str, Any]]:
        return [
            {
                "noteId": note_ids[0],
                "fields": {
                    "Headword": {"value": "run"},
                    "Sentence": {"value": "I run."},
                    "Source Sentence": {"value": "Original source."},
                },
            }
        ]

    def fake_generate_card(_config: Config, sentence: str, word: str, **_kwargs: Any) -> Card:
        captured["sentence"] = sentence
        captured["word"] = word
        return _sample_card()

    inputs = iter(["123", "q"])
    monkeypatch.setattr(session_module, "resolve_config", lambda: config)
    monkeypatch.setattr(session_module, "notes_info", fake_notes_info)
    monkeypatch.setattr(session_module, "generate_card", fake_generate_card)
    monkeypatch.setattr(session_module, "update_note_fields", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(session_module, "confirm_menu", lambda *args, **kwargs: True)
    monkeypatch.setattr(session_module, "render_card", lambda *args, **kwargs: None)
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: next(inputs))

    session_module.session_command()

    assert captured["sentence"] == "Original source."
    assert captured["word"] == "run"


def test_session_update_tts_prompt_skips_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config(tts_enabled=True)
    captured: dict[str, Any] = {}

    def fake_notes_info(_url: str, note_ids: list[int]) -> list[dict[str, Any]]:
        return [
            {
                "noteId": note_ids[0],
                "fields": {
                    "Word": {"value": "run"},
                    "Context Sentence": {"value": "I run."},
                    "Audio Lemma": {"value": "[sound:old-lemma.mp3]"},
                    "Audio Context": {"value": "[sound:old-context.mp3]"},
                },
            }
        ]

    def fake_generate_card(*_args: Any, **_kwargs: Any) -> Card:
        raise AssertionError("generate_card should not be called for tts-only updates")

    def fake_build_audio_fields(
        _url: str,
        *,
        lemma: str,
        context: str,
        voice: str,
        rate: str,
    ) -> tuple[str, str]:
        captured["audio_args"] = {
            "lemma": lemma,
            "context": context,
            "voice": voice,
            "rate": rate,
        }
        return "[sound:lemma.mp3]", "[sound:context.mp3]"

    def fake_update_note_fields(_url: str, note_id: int, fields: dict[str, str]) -> None:
        captured["update_note_fields"] = {"note_id": note_id, "fields": fields}

    inputs = iter(["123 | tts", "q"])
    monkeypatch.setattr(session_module, "resolve_config", lambda: config)
    monkeypatch.setattr(session_module, "notes_info", fake_notes_info)
    monkeypatch.setattr(session_module, "generate_card", fake_generate_card)
    monkeypatch.setattr(session_module, "build_audio_fields", fake_build_audio_fields)
    monkeypatch.setattr(session_module, "update_note_fields", fake_update_note_fields)
    monkeypatch.setattr(session_module, "confirm_menu", lambda *args, **kwargs: True)
    monkeypatch.setattr(session_module, "render_card", lambda *args, **kwargs: None)
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: next(inputs))

    session_module.session_command()

    assert captured["audio_args"] == {
        "lemma": "run",
        "context": "I run.",
        "voice": "voice",
        "rate": "+0%",
    }
    assert captured["update_note_fields"]["note_id"] == 123
    assert captured["update_note_fields"]["fields"] == {
        "Audio Lemma": "[sound:lemma.mp3]",
        "Audio Context": "[sound:context.mp3]",
    }


def test_session_update_missing_note_continues(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    config = _config()

    inputs = iter(["123", "q"])
    monkeypatch.setattr(session_module, "resolve_config", lambda: config)
    monkeypatch.setattr(session_module, "notes_info", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(session_module, "render_card", lambda *args, **kwargs: None)
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: next(inputs))

    session_module.session_command()

    captured = capsys.readouterr()
    assert "Note id 123 not found." in captured.err


def test_session_update_missing_word_field_continues(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = _config()

    def fake_notes_info(_url: str, note_ids: list[int]) -> list[dict[str, Any]]:
        return [
            {
                "noteId": note_ids[0],
                "fields": {
                    "Context Sentence": {"value": "I run."},
                },
            }
        ]

    inputs = iter(["123", "q"])
    monkeypatch.setattr(session_module, "resolve_config", lambda: config)
    monkeypatch.setattr(session_module, "notes_info", fake_notes_info)
    monkeypatch.setattr(session_module, "render_card", lambda *args, **kwargs: None)
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: next(inputs))

    session_module.session_command()

    captured = capsys.readouterr()
    assert "Selected note is missing the word field." in captured.err
