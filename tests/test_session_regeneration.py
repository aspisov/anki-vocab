from __future__ import annotations

from typing import Any, Iterator

import pytest

from anki_vocab.commands import session as session_module
from anki_vocab.core.config import Config, DEFAULT_FIELD_MAP
from anki_vocab.core.schema import Card


def _card_with_lemma(lemma: str) -> Card:
    return Card(
        lemma=lemma,
        target_surface=lemma,
        pos="verb",
        meaning_ru="значение",
        definition="definition",
        context_source="Book",
        context="Context sentence.",
        cloze="Cloze.",
        context_ru="Перевод.",
        pattern="pattern",
        synonyms="synonym",
        notes="",
        rarity="common",
        cefr="A1",
    )


def test_session_regeneration_refreshes_note_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
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
        tts_field="Audio",
        tts_enabled=False,
    )

    cards: Iterator[Card] = iter([_card_with_lemma("alpha"), _card_with_lemma("beta")])
    queries: list[str] = []

    def fake_input(_prompt: str = "") -> str:
        values = ["Context | word", "Regenerate feedback"]
        if fake_input.calls < len(values):
            value = values[fake_input.calls]
            fake_input.calls += 1
            return value
        raise EOFError()

    fake_input.calls = 0

    def fake_generate_card(*_args: Any, **_kwargs: Any) -> Card:
        return next(cards)

    def fake_find_notes(_url: str, query: str) -> list[int]:
        queries.append(query)
        return []

    menu_choices = [3, 2]  # Regenerate, then Skip

    def fake_select_menu(*_args: Any, **_kwargs: Any) -> int:
        return menu_choices.pop(0)

    monkeypatch.setattr(session_module, "resolve_config", lambda: config)
    monkeypatch.setattr(session_module, "generate_card", fake_generate_card)
    monkeypatch.setattr(session_module, "find_notes", fake_find_notes)
    monkeypatch.setattr(session_module, "select_menu", fake_select_menu)
    monkeypatch.setattr(session_module, "render_card", lambda *args, **kwargs: None)
    monkeypatch.setattr("builtins.input", fake_input)

    session_module.session_command(yes=False, no_tts=True, dry_run=False)

    assert len(queries) == 2
    assert '"alpha"' in queries[0]
    assert '"beta"' in queries[1]
