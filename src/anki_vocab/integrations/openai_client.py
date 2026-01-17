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
) -> Card:
    _ensure_env_loaded()
    resolved_key = api_key.strip() if api_key else ""
    client = OpenAI(api_key=resolved_key or None)

    user_content = f'SENTENCE: {sentence}\nTARGET: "{word}"'
    if attempts:
        attempts_payload = json.dumps(attempts, ensure_ascii=False)
        user_content = f"{user_content}\nPREVIOUS_ATTEMPTS_JSON:\n{attempts_payload}"

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
