from __future__ import annotations

from typer.testing import CliRunner

from anki_vocab import cli as cli_module
from anki_vocab.commands import add as add_module
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


def _add_args(**overrides: str) -> list[str]:
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

    args = ["add"]
    for key, value in values.items():
        args.extend([f"--{key.replace('_', '-')}", value])
    return args


def test_add_command_adds_note_from_explicit_fields(monkeypatch) -> None:
    runner = CliRunner()
    captured: dict[str, object] = {}

    def fake_add_card_note(config: Config, card) -> int:
        captured["config"] = config
        captured["card"] = card
        return 321

    monkeypatch.setattr(add_module, "resolve_config", lambda: _config())
    monkeypatch.setattr(add_module, "add_card_note", fake_add_card_note)

    result = runner.invoke(cli_module.app, _add_args())

    assert result.exit_code == 0
    assert result.stdout.strip() == "321"
    assert captured["config"].deck == "Test"
    assert captured["card"].lemma == "run"
    assert captured["card"].context_source == "I run every morning."
    assert captured["card"].notes == "Common everyday verb."


def test_add_command_rejects_empty_fields(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(add_module, "resolve_config", lambda: _config())

    result = runner.invoke(cli_module.app, _add_args(notes=""))

    assert result.exit_code == 1
    assert "Invalid card fields:" in result.output
    assert "must be a non-empty string" in result.output
