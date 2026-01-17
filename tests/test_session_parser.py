import pytest

from anki_vocab.commands.session import _parse_session_line


def test_parse_session_line_with_context() -> None:
    context, word = _parse_session_line("Some context | word")
    assert context == "Some context"
    assert word == "word"


def test_parse_session_line_allows_word_only() -> None:
    context, word = _parse_session_line("word")
    assert context == ""
    assert word == "word"


def test_parse_session_line_missing_context_raises() -> None:
    context, word = _parse_session_line("word")
    assert context == ""
    assert word == "word"


def test_parse_session_line_missing_context_with_pipe_raises() -> None:
    with pytest.raises(ValueError):
        _parse_session_line("| word")
