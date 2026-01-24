import pytest

from anki_vocab.core.schema import parse_card


def test_parse_card_requires_fields() -> None:
    with pytest.raises(RuntimeError):
        parse_card({"word_base": "test"})


def test_parse_card_accepts_valid_payload() -> None:
    payload = {
        "lemma": "test",
        "target_surface": "test",
        "pos": "noun",
        "meaning_ru": "тест",
        "definition": "a simple test",
        "context_source": "This is a test.",
        "context": "This is a test.",
        "cloze": "This is a [...].",
        "context_ru": "Это тест.",
        "pattern": "N/A",
        "synonyms": "trial, exam",
        "notes": "Often used in education or QA contexts.",
        "rarity": "Common",
        "cefr": "B1",
        "tts_text": "test",
    }
    card = parse_card(payload)
    assert card.lemma == "test"
    assert card.tts_text == "test"
