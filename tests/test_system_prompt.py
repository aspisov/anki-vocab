from anki_vocab.integrations import openai_client


RULE = 'Only cloze may contain the placeholder "[...]"; context and context_ru must not contain it.'


def test_system_prompt_includes_cloze_only_rule_en() -> None:
    prompt = openai_client._system_prompt(
        has_current_card=False,
        has_user_prompt=False,
        source_language="en",
    )
    assert RULE in prompt


def test_system_prompt_includes_cloze_only_rule_es() -> None:
    prompt = openai_client._system_prompt(
        has_current_card=False,
        has_user_prompt=False,
        source_language="es",
    )
    assert RULE in prompt
