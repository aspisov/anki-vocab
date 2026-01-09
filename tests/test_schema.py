import pytest

from anki_card_generator.core.schema import parse_card


def test_parse_card_requires_fields() -> None:
    with pytest.raises(RuntimeError):
        parse_card({"word_base": "test"})


def test_parse_card_accepts_valid_payload() -> None:
    payload = {
        "word_base": "test",
        "pos": "noun",
        "ru_meaning": "тест",
        "definition": "a simple test",
        "context_en": "This is a test.",
        "context_ru": "Это тест.",
        "rarity": "Common",
        "cefr": "B1",
        "tts_text": "test",
    }
    card = parse_card(payload)
    assert card.word_base == "test"
    assert card.tts_text == "test"
