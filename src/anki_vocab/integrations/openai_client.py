import json

from dotenv import load_dotenv
from openai import OpenAI

from ..core.schema import Card, parse_card
from .llm_prompts import build_user_content as _build_user_content
from .llm_prompts import system_prompt as _system_prompt

_ENV_LOADED = False


def _ensure_env_loaded() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    load_dotenv()
    _ENV_LOADED = True


def generate_card(
    sentence: str,
    word: str,
    *,
    model: str,
    api_key: str | None,
    source_language: str,
    current_card: dict[str, str] | None = None,
    user_prompt: str | None = None,
) -> Card:
    _ensure_env_loaded()
    resolved_key = api_key.strip() if api_key else ""
    client = OpenAI(api_key=resolved_key or None)

    user_content = _build_user_content(sentence, word, current_card=current_card, user_prompt=user_prompt)

    content = (
        client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": _system_prompt(
                        has_current_card=current_card is not None,
                        has_user_prompt=bool(user_prompt),
                        source_language=source_language,
                    ),
                },
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        .choices[0]
        .message.content
    )

    if not content:
        raise RuntimeError("OpenAI returned empty response")

    payload = json.loads(content)
    source_context = sentence.strip() or "N/A"
    payload["context_source"] = source_context
    return parse_card(payload)
