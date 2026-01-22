from anki_vocab.integrations.openai_client import _system_prompt


def test_system_prompt_mentions_pattern_notes() -> None:
    prompt = _system_prompt(has_current_card=False, has_user_prompt=False)
    assert "Pattern:" in prompt
    assert "preposition" in prompt or "particle" in prompt
