from __future__ import annotations

import pytest

from anki_vocab.core.config import Config, DEFAULT_FIELD_MAP
from anki_vocab.core.note_builder import build_add_note_payload
from anki_vocab.core.schema import Card


def _config(*, tts_enabled: bool = True) -> Config:
    return Config(
        deck="Test",
        note_model="English",
        field_map=dict(DEFAULT_FIELD_MAP),
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


def _card() -> Card:
    return Card(
        lemma="run",
        target_surface="run",
        pos="verb",
        meaning_ru="бежать",
        definition="to move swiftly",
        context_source="I run every morning.",
        context="I run every morning before work.",
        cloze="I [...] every morning before work.",
        context_ru="Я бегаю каждое утро перед работой.",
        pattern="run + adverbial",
        synonyms="jog, sprint",
        notes="Common everyday verb.",
        rarity="Common",
        cefr="A2",
    )


def test_build_add_note_payload_adds_tts_fields_and_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_build_audio_fields(
        url: str,
        *,
        lemma: str,
        context: str,
        voice: str,
        rate: str,
    ) -> tuple[str, str]:
        captured["audio_args"] = {
            "url": url,
            "lemma": lemma,
            "context": context,
            "voice": voice,
            "rate": rate,
        }
        return "[sound:lemma.mp3]", "[sound:context.mp3]"

    monkeypatch.setattr("anki_vocab.core.note_builder.build_audio_fields", fake_build_audio_fields)

    note = build_add_note_payload(_config(), _card())

    assert captured["audio_args"] == {
        "url": "http://anki.test",
        "lemma": "run",
        "context": "I run every morning before work.",
        "voice": "voice",
        "rate": "+0%",
    }
    assert note["fields"]["Audio Lemma"] == "[sound:lemma.mp3]"
    assert note["fields"]["Audio Context"] == "[sound:context.mp3]"
    assert note["tags"] == ["auto", "tts"]
