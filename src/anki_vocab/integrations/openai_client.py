import json
from functools import lru_cache
from importlib import resources

from dotenv import load_dotenv
from openai import OpenAI

from ..core.schema import Card, parse_card

_ENV_LOADED = False


@lru_cache(maxsize=1)
def _system_prompt() -> str:
    return resources.files("anki_vocab").joinpath("system_prompt.jinja").read_text(encoding="utf-8").strip()


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
    attempts: list[dict[str, object]] | None = None,
    current_card: dict[str, str] | None = None,
    user_prompt: str | None = None,
) -> Card:
    _ensure_env_loaded()
    resolved_key = api_key.strip() if api_key else ""
    client = OpenAI(api_key=resolved_key or None)

    user_content = _build_user_content(
        sentence,
        word,
        attempts=attempts,
        current_card=current_card,
        user_prompt=user_prompt,
    )

    content = (
        client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _system_prompt()},
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
    return parse_card(payload)


def _build_user_content(
    sentence: str,
    word: str,
    *,
    attempts: list[dict[str, object]] | None,
    current_card: dict[str, str] | None,
    user_prompt: str | None,
) -> str:
    user_content = f'SENTENCE: {sentence}\nTARGET: "{word}"'
    if current_card is not None:
        current_payload = json.dumps(current_card, ensure_ascii=False)
        user_content = f"{user_content}\nCURRENT_CARD_JSON:\n{current_payload}"
    if user_prompt:
        user_content = f"{user_content}\nUSER_PROMPT:\n{user_prompt}"
    if attempts:
        attempts_payload = json.dumps(attempts, ensure_ascii=False)
        user_content = f"{user_content}\nPREVIOUS_ATTEMPTS_JSON:\n{attempts_payload}"
    return user_content
