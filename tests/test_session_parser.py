import pytest

from anki_vocab.commands.session import (
    DEFAULT_UPDATE_PROMPT,
    AddRequest,
    QuitRequest,
    UpdateRequest,
    _parse_session_line,
)


def test_parse_session_line_with_context() -> None:
    assert _parse_session_line("Some context | word") == AddRequest(context="Some context", word="word")


def test_parse_session_line_allows_word_only() -> None:
    assert _parse_session_line("word") == AddRequest(context="", word="word")


def test_parse_session_line_parses_bare_note_id_as_update() -> None:
    assert _parse_session_line("123") == UpdateRequest(note_id=123, prompt=DEFAULT_UPDATE_PROMPT)


def test_parse_session_line_parses_note_id_with_prompt() -> None:
    assert _parse_session_line("123 | Refine definition") == UpdateRequest(
        note_id=123,
        prompt="Refine definition",
    )


def test_parse_session_line_parses_quit() -> None:
    assert _parse_session_line("q") == QuitRequest()


def test_parse_session_line_missing_context_with_pipe_raises() -> None:
    with pytest.raises(ValueError, match="Context is missing"):
        _parse_session_line("| word")


def test_parse_session_line_missing_update_prompt_raises() -> None:
    with pytest.raises(ValueError, match="Prompt is missing"):
        _parse_session_line("123 |")
