from __future__ import annotations

from typer.testing import CliRunner

from anki_vocab import cli as cli_module
from anki_vocab.commands import add as add_module
from anki_vocab.commands import show as show_module
from anki_vocab.commands import update as update_module
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


def test_root_command_starts_session(monkeypatch) -> None:
    runner = CliRunner()
    called: list[bool] = []

    monkeypatch.setattr(cli_module, "resolve_config", _config)
    monkeypatch.setattr(cli_module, "session_command", lambda: called.append(True))

    result = runner.invoke(cli_module.app, [])

    assert result.exit_code == 0
    assert called == [True]


def test_config_command_does_not_start_session(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(cli_module, "session_command", lambda: (_ for _ in ()).throw(AssertionError("should not run")))

    result = runner.invoke(cli_module.app, ["config", "path"])

    assert result.exit_code == 0


def test_add_command_does_not_start_session(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(cli_module, "session_command", lambda: (_ for _ in ()).throw(AssertionError("should not run")))
    monkeypatch.setattr(add_module, "resolve_config", _config)
    monkeypatch.setattr(add_module, "add_card_note", lambda *_args, **_kwargs: 42)

    result = runner.invoke(
        cli_module.app,
        [
            "add",
            "--lemma",
            "run",
            "--target-surface",
            "run",
            "--pos",
            "verb",
            "--meaning-ru",
            "бежать",
            "--definition",
            "to move swiftly",
            "--context-source",
            "I run every morning.",
            "--context",
            "I run every morning before work.",
            "--cloze",
            "I [...] every morning before work.",
            "--context-ru",
            "Я бегаю каждое утро перед работой.",
            "--pattern",
            "run + adverbial",
            "--synonyms",
            "jog, sprint",
            "--notes",
            "Common everyday verb.",
            "--rarity",
            "Common",
            "--cefr",
            "A2",
        ],
    )

    assert result.exit_code == 0
    assert result.output.strip() == "42"


def test_show_command_does_not_start_session(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(cli_module, "session_command", lambda: (_ for _ in ()).throw(AssertionError("should not run")))
    monkeypatch.setattr(show_module, "resolve_config", _config)
    monkeypatch.setattr(
        show_module,
        "notes_info",
        lambda *_args, **_kwargs: [
            {
                "noteId": 42,
                "modelName": "English",
                "tags": ["auto"],
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

    result = runner.invoke(cli_module.app, ["show", "42"])

    assert result.exit_code == 0
    assert '"note_id": 42' in result.output


def test_removed_session_command_is_not_available() -> None:
    runner = CliRunner()

    result = runner.invoke(cli_module.app, ["session"])

    assert result.exit_code != 0
    assert "No such command 'session'" in result.output


def test_update_command_does_not_start_session(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(cli_module, "session_command", lambda: (_ for _ in ()).throw(AssertionError("should not run")))
    monkeypatch.setattr(update_module, "resolve_config", _config)
    monkeypatch.setattr(update_module, "update_card_note", lambda *_args, **_kwargs: None)

    result = runner.invoke(
        cli_module.app,
        [
            "update",
            "42",
            "--lemma",
            "run",
            "--target-surface",
            "run",
            "--pos",
            "verb",
            "--meaning-ru",
            "бежать",
            "--definition",
            "to move swiftly",
            "--context-source",
            "I run every morning.",
            "--context",
            "I run every morning before work.",
            "--cloze",
            "I [...] every morning before work.",
            "--context-ru",
            "Я бегаю каждое утро перед работой.",
            "--pattern",
            "run + adverbial",
            "--synonyms",
            "jog, sprint",
            "--notes",
            "Common everyday verb.",
            "--rarity",
            "Common",
            "--cefr",
            "A2",
        ],
    )

    assert result.exit_code == 0
    assert result.output.strip() == "42"
