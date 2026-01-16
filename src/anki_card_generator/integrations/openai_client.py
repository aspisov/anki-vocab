import json
from importlib import resources

from dotenv import load_dotenv
from openai import OpenAI

from ..core.schema import Card, parse_card


def _read_system_prompt() -> str:
    return resources.files("anki_card_generator").joinpath("system_prompt.jinja").read_text(encoding="utf-8").strip()


def generate_card(
    sentence: str,
    word: str,
    *,
    model: str,
    api_key: str | None,
    attempts: list[dict[str, object]] | None = None,
) -> Card:
    load_dotenv()
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
                {"role": "system", "content": _read_system_prompt()},
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
