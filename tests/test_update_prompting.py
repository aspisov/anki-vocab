from anki_vocab.core.ankimapping import note_to_card_payload
from anki_vocab.integrations.openai_client import _build_user_content


def test_note_to_card_payload_includes_mapped_fields_with_blanks() -> None:
    note = {
        "fields": {
            "Word": {"value": "run"},
            "Definition": {"value": "to move swiftly"},
        }
    }
    field_map = {
        "word_base": "Word",
        "definition": "Definition",
        "context_en": "Context Sentence",
        "pos": "Part of Speech",
    }

    payload = note_to_card_payload(note, field_map)

    assert payload["word_base"] == "run"
    assert payload["definition"] == "to move swiftly"
    assert payload["context_en"] == ""
    assert payload["pos"] == ""
    assert "ru_meaning" not in payload


def test_build_user_content_handles_optional_sections() -> None:
    content = _build_user_content(
        "A test sentence.",
        "test",
        current_card={"word_base": "test", "definition": "a check"},
        user_prompt="Focus on informal usage.",
    )

    assert 'SENTENCE: A test sentence.' in content
    assert 'TARGET: "test"' in content
    assert "CURRENT_CARD_JSON" in content
    assert "USER_PROMPT" in content


def test_build_user_content_omits_prompt_when_missing() -> None:
    content = _build_user_content(
        "Another sentence.",
        "another",
        current_card=None,
        user_prompt=None,
    )

    assert "USER_PROMPT" not in content
    assert "CURRENT_CARD_JSON" not in content
