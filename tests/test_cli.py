from __future__ import annotations

from typer.testing import CliRunner

from anki_vocab import cli as cli_module
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


def test_removed_session_command_is_not_available() -> None:
    runner = CliRunner()

    result = runner.invoke(cli_module.app, ["session"])

    assert result.exit_code != 0
    assert "No such command 'session'" in result.output


def test_removed_update_command_is_not_available() -> None:
    runner = CliRunner()

    result = runner.invoke(cli_module.app, ["update"])

    assert result.exit_code != 0
    assert "No such command 'update'" in result.output
