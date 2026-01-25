from __future__ import annotations

from anki_vocab.commands import config as config_module
from anki_vocab.core.config import Config, DEFAULT_FIELD_MAP


def test_config_show_redacts_openai_key(monkeypatch, capsys) -> None:
    config = Config(
        deck="Test",
        note_model="English",
        field_map=dict(DEFAULT_FIELD_MAP),
        ankiconnect_url="http://anki.test",
        source_language="en",
        openai_api_key="sk-test",
        openai_model="gpt-test",
        tts_voice="voice",
        tts_rate="+0%",
        tts_lemma_field="Audio Lemma",
        tts_context_field="Audio Context",
        tts_enabled=True,
    )

    monkeypatch.setattr(config_module, "resolve_config", lambda: config)

    config_module.config_show()
    output = capsys.readouterr().out

    assert "sk-test" not in output
    assert '"openai_api_key": "********"' in output
