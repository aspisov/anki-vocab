import re


_WHITESPACE_RE = re.compile(r"\s+")
_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:!?])")


def clean_context(text: str) -> str:
    cleaned = _WHITESPACE_RE.sub(" ", text.strip())
    return _SPACE_BEFORE_PUNCT_RE.sub(r"\1", cleaned)
