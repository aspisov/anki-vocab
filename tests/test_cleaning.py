from anki_card_generator.core.cleaning import clean_context


def test_clean_context_collapses_whitespace() -> None:
    assert clean_context("Hello   world") == "Hello world"


def test_clean_context_removes_space_before_punct() -> None:
    assert clean_context("Hello , world !") == "Hello, world!"
