import pytest

from anki_card_generator.commands.session import _parse_session_line


def test_parse_session_line_with_context() -> None:
    context, word, last = _parse_session_line("Some context | word", None)
    assert context == "Some context"
    assert word == "word"
    assert last == "Some context"


def test_parse_session_line_reuses_last_context() -> None:
    context, word, last = _parse_session_line("word", "Cached context")
    assert context == "Cached context"
    assert word == "word"
    assert last == "Cached context"


def test_parse_session_line_missing_context_raises() -> None:
    context, word, last = _parse_session_line("word", None)
    assert context == ""
    assert word == "word"
    assert last is None


def test_parse_session_line_missing_context_with_pipe_raises() -> None:
    with pytest.raises(ValueError):
        _parse_session_line("| word", None)
