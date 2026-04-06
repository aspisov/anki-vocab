from __future__ import annotations

import json

from typer.testing import CliRunner

from anki_vocab import cli as cli_module
from anki_vocab.commands import show as show_module
from anki_vocab.core.config import Config, DEFAULT_FIELD_MAP


def _config() -> Config:
    return Config(
        deck="Test",
        note_model="English",
        field_map=dict(DEFAULT_FIELD_MAP),
        ankiconnect_url="http://anki.test",
        source_language="en",
        llm_provider="ollama",
        openai_api_key="",
        openai_model="gpt-test",
        ollama_url="http://ollama.test",
        ollama_model="gemma-test",
        tts_voice="voice",
        tts_rate="+0%",
        tts_lemma_field="Audio Lemma",
        tts_context_field="Audio Context",
        tts_enabled=True,
    )


def test_show_command_prints_card_payload(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(show_module, "resolve_config", _config)
    monkeypatch.setattr(
        show_module,
        "notes_info",
        lambda *_args, **_kwargs: [
            {
                "noteId": 123,
                "modelName": "English",
                "tags": ["auto", "tts"],
                "fields": {
                    "Word": {"value": "run"},
                    "Target Surface": {"value": "run"},
                    "Part of Speech": {"value": "verb"},
                    "Russian Meaning": {"value": "бежать"},
                    "Definition": {"value": "to move swiftly"},
                    "Context Sentence Source": {"value": "I run every morning."},
                    "Context Sentence": {"value": "I run every morning before work."},
                    "Cloze Sentence": {"value": "I [...] every morning before work."},
                    "Sentence Translation": {"value": "Я бегаю каждое утро перед работой."},
                    "Pattern": {"value": "run + adverbial"},
                    "Synonyms": {"value": "jog, sprint"},
                    "Notes": {"value": "Common everyday verb."},
                    "Rarity": {"value": "Common"},
                    "CEFR": {"value": "A2"},
                },
            }
        ],
    )

    result = runner.invoke(cli_module.app, ["show", "123"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["note_id"] == 123
    assert payload["card"]["lemma"] == "run"
    assert payload["card"]["context"] == "I run every morning before work."


def test_show_command_errors_for_missing_note(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(show_module, "resolve_config", _config)
    monkeypatch.setattr(show_module, "notes_info", lambda *_args, **_kwargs: [])

    result = runner.invoke(cli_module.app, ["show", "123"])

    assert result.exit_code == 1
    assert "Note id 123 not found." in result.output
