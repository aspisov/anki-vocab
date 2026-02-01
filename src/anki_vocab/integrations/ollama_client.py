from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..core.schema import Card, parse_card
from .llm_prompts import build_user_content, system_prompt


def generate_card(
    sentence: str,
    word: str,
    *,
    model: str,
    base_url: str,
    source_language: str,
    current_card: dict[str, str] | None = None,
    user_prompt: str | None = None,
) -> Card:
    if not model or not model.strip():
        raise ValueError("Ollama model is not set.")
    if not base_url or not base_url.strip():
        raise ValueError("Ollama base URL is not set.")

    user_content = build_user_content(sentence, word, current_card=current_card, user_prompt=user_prompt)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt(
                    has_current_card=current_card is not None,
                    has_user_prompt=bool(user_prompt),
                    source_language=source_language,
                ),
            },
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }

    response = _post_json(f"{base_url.rstrip('/')}/api/chat", payload)
    content = _extract_message_content(response)
    if not content:
        raise RuntimeError("Ollama returned empty response")

    try:
        card_payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Ollama returned invalid JSON content") from exc

    source_context = sentence.strip() or "N/A"
    card_payload["context_source"] = source_context
    return parse_card(card_payload)


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request) as response:  # noqa: S310 - local API, configurable via config
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore").strip()
        message = f"Ollama request failed ({exc.code} {exc.reason})"
        if error_body:
            message = f"{message}: {error_body}"
        raise RuntimeError(message) from exc
    except URLError as exc:
        raise RuntimeError(f"Ollama request failed: {exc.reason}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Ollama returned invalid JSON response") from exc


def _extract_message_content(response: dict[str, Any]) -> str:
    message = response.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
    return ""
