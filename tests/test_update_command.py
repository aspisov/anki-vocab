from __future__ import annotations

from typer.testing import CliRunner

from anki_vocab import cli as cli_module
from anki_vocab.commands import update as update_module
from anki_vocab.core.config import Config, DEFAULT_FIELD_MAP


def _config(*, tts_enabled: bool = True) -> Config:
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
        tts_enabled=tts_enabled,
    )


def _update_args(**overrides: str) -> list[str]:
    values = {
        "lemma": "run",
        "target_surface": "run",
        "pos": "verb",
        "meaning_ru": "бежать",
        "definition": "to move swiftly",
        "context_source": "I run every morning.",
        "context": "I run every morning before work.",
        "cloze": "I [...] every morning before work.",
        "context_ru": "Я бегаю каждое утро перед работой.",
        "pattern": "run + adverbial",
        "synonyms": "jog, sprint",
        "notes": "Common everyday verb.",
        "rarity": "Common",
        "cefr": "A2",
    }
    values.update(overrides)

    args = ["update", "123"]
    for key, value in values.items():
        args.extend([f"--{key.replace('_', '-')}", value])
    return args


def test_update_command_updates_note_from_explicit_fields(monkeypatch) -> None:
    runner = CliRunner()
    captured: dict[str, object] = {}

    def fake_update_card_note(config: Config, note_id: int, card) -> None:
        captured["config"] = config
        captured["note_id"] = note_id
        captured["card"] = card

    monkeypatch.setattr(update_module, "resolve_config", lambda: _config())
    monkeypatch.setattr(update_module, "update_card_note", fake_update_card_note)

    result = runner.invoke(cli_module.app, _update_args())

    assert result.exit_code == 0
    assert result.stdout.strip() == "123"
    assert captured["config"].deck == "Test"
    assert captured["note_id"] == 123
    assert captured["card"].lemma == "run"
    assert captured["card"].context == "I run every morning before work."


def test_update_command_rejects_empty_fields(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(update_module, "resolve_config", lambda: _config())

    result = runner.invoke(cli_module.app, _update_args(notes=""))

    assert result.exit_code == 1
    assert "Invalid card fields:" in result.output
    assert "must be a non-empty string" in result.output
