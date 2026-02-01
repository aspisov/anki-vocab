import json
from functools import lru_cache
from importlib import resources

from jinja2 import Environment


@lru_cache(maxsize=2)
def system_prompt_template(source_language: str) -> str:
    template_name = "system_prompt_es.jinja" if source_language == "es" else "system_prompt.jinja"
    return resources.files("anki_vocab").joinpath(template_name).read_text(encoding="utf-8")


@lru_cache(maxsize=8)
def system_prompt(*, has_current_card: bool, has_user_prompt: bool, source_language: str) -> str:
    env = Environment(autoescape=False)
    template = env.from_string(system_prompt_template(source_language))
    return template.render(
        has_current_card=has_current_card,
        has_user_prompt=has_user_prompt,
        source_language=source_language,
    ).strip()


def build_user_content(
    sentence: str,
    word: str,
    *,
    current_card: dict[str, str] | None,
    user_prompt: str | None,
) -> str:
    sentence_value = sentence.strip() or "N/A"
    user_content = f'SENTENCE: {sentence_value}\nTARGET: "{word}"'
    if current_card is not None:
        current_payload = dict(current_card)
        current_payload.pop("context_source", None)
        current_payload_json = json.dumps(current_payload, ensure_ascii=False)
        user_content = f"{user_content}\nCURRENT_CARD_JSON:\n{current_payload_json}"
    if user_prompt:
        user_content = f"{user_content}\nUSER_PROMPT:\n{user_prompt}"
    return user_content
