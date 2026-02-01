from __future__ import annotations

import json

import pytest

from anki_vocab.integrations import ollama_client


def _sample_payload() -> dict[str, str]:
    return {
        "lemma": "run",
        "target_surface": "run",
        "pos": "verb",
        "meaning_ru": "бежать",
        "definition": "to move swiftly",
        "context_source": "Book",
        "context": "I run.",
        "cloze": "I ____.",
        "context_ru": "Я бегу.",
        "pattern": "run fast",
        "synonyms": "sprint",
        "notes": "N/A",
        "rarity": "common",
        "cefr": "A1",
    }


def test_ollama_client_parses_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _sample_payload()
    payload["context_source"] = "ignored"

    def fake_post_json(_url: str, _payload: dict[str, object]) -> dict[str, object]:
        return {"message": {"content": json.dumps(payload)}}

    monkeypatch.setattr(ollama_client, "_post_json", fake_post_json)

    card = ollama_client.generate_card(
        "Sentence source.",
        "run",
        model="gemma-test",
        base_url="http://ollama.test",
        source_language="en",
    )

    assert card.lemma == "run"
    assert card.context_source == "Sentence source."


def test_ollama_client_errors_on_empty_content(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post_json(_url: str, _payload: dict[str, object]) -> dict[str, object]:
        return {"message": {"content": ""}}

    monkeypatch.setattr(ollama_client, "_post_json", fake_post_json)

    with pytest.raises(RuntimeError, match="Ollama returned empty response"):
        ollama_client.generate_card(
            "Sentence source.",
            "run",
            model="gemma-test",
            base_url="http://ollama.test",
            source_language="en",
        )


def test_ollama_client_errors_on_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post_json(_url: str, _payload: dict[str, object]) -> dict[str, object]:
        return {"message": {"content": "not json"}}

    monkeypatch.setattr(ollama_client, "_post_json", fake_post_json)

    with pytest.raises(RuntimeError, match="Ollama returned invalid JSON content"):
        ollama_client.generate_card(
            "Sentence source.",
            "run",
            model="gemma-test",
            base_url="http://ollama.test",
            source_language="en",
        )
