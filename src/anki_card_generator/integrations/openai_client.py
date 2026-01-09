import json
from importlib import resources

from dotenv import load_dotenv
from openai import OpenAI

from ..core.schema import Card, parse_card


def _read_system_prompt() -> str:
    return resources.files("anki_card_generator").joinpath("system_prompt.jinja").read_text(encoding="utf-8").strip()


def generate_card(sentence: str, word: str, *, model: str) -> Card:
    load_dotenv()
    client = OpenAI()

    content = (
        client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _read_system_prompt()},
                {"role": "user", "content": f'SENTENCE: {sentence}\nTARGET: "{word}"'},
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
