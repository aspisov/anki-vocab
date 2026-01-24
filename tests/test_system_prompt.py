from anki_vocab.integrations.openai_client import _system_prompt


def test_system_prompt_mentions_pattern_notes() -> None:
    prompt = _system_prompt(has_current_card=False, has_user_prompt=False, source_language="en")
    assert "pattern" in prompt
    assert "synonyms" in prompt
    assert "cloze_en" in prompt
    assert "target_surface" in prompt
    assert "register" in prompt
    assert "N/A" in prompt
    assert "Source language is English" in prompt
    assert "Prefer American English" in prompt
    assert "preposition" in prompt or "particle" in prompt
    assert "Source language is Spanish" not in prompt


def test_system_prompt_mentions_spanish_source_language() -> None:
    prompt = _system_prompt(has_current_card=False, has_user_prompt=False, source_language="es")
    assert "Source language is Spanish" in prompt
    assert "Prefer American English" not in prompt
    assert "Field names like context_en/cloze_en are legacy" in prompt
