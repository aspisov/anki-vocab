from __future__ import annotations

from typing import Any

import pytest

from anki_vocab.core.config import Config, DEFAULT_FIELD_MAP
from anki_vocab.core.schema import Card
from anki_vocab.integrations import llm_client


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
        notes="N/A",
        rarity="common",
        cefr="A1",
    )


def _base_config(**overrides: Any) -> Config:
    data = dict(
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
        tts_enabled=False,
    )
    data.update(overrides)
    return Config(**data)


def test_llm_client_routes_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _base_config(llm_provider="openai")
    captured: dict[str, Any] = {}

    def fake_generate_card(sentence: str, word: str, **kwargs: Any) -> Card:
        captured["sentence"] = sentence
        captured["word"] = word
        captured["kwargs"] = kwargs
        return _sample_card()

    monkeypatch.setattr(llm_client.openai_client, "generate_card", fake_generate_card)

    card = llm_client.generate_card(config, "Sentence.", "word", user_prompt="prompt")

    assert card.lemma == "run"
    assert captured["sentence"] == "Sentence."
    assert captured["word"] == "word"
    assert captured["kwargs"]["model"] == "gpt-test"
    assert captured["kwargs"]["api_key"] == "sk-test"
    assert captured["kwargs"]["source_language"] == "en"


def test_llm_client_routes_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _base_config(llm_provider="ollama")
    captured: dict[str, Any] = {}

    def fake_generate_card(sentence: str, word: str, **kwargs: Any) -> Card:
        captured["sentence"] = sentence
        captured["word"] = word
        captured["kwargs"] = kwargs
        return _sample_card()

    monkeypatch.setattr(llm_client.ollama_client, "generate_card", fake_generate_card)

    card = llm_client.generate_card(config, "Sentence.", "word")

    assert card.lemma == "run"
    assert captured["kwargs"]["model"] == "gemma-test"
    assert captured["kwargs"]["base_url"] == "http://ollama.test"
    assert captured["kwargs"]["source_language"] == "en"


def test_llm_client_rejects_unknown_provider() -> None:
    config = _base_config(llm_provider="unknown")

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        llm_client.generate_card(config, "Sentence.", "word")
