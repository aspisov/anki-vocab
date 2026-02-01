from __future__ import annotations

from ..core.config import Config
from ..core.schema import Card
from . import ollama_client, openai_client


def generate_card(
    config: Config,
    sentence: str,
    word: str,
    *,
    current_card: dict[str, str] | None = None,
    user_prompt: str | None = None,
) -> Card:
    provider = config.llm_provider.strip().lower()
    if provider == "openai":
        return openai_client.generate_card(
            sentence,
            word,
            model=config.openai_model,
            api_key=config.openai_api_key,
            source_language=config.source_language,
            current_card=current_card,
            user_prompt=user_prompt,
        )
    if provider == "ollama":
        return ollama_client.generate_card(
            sentence,
            word,
            model=config.ollama_model,
            base_url=config.ollama_url,
            source_language=config.source_language,
            current_card=current_card,
            user_prompt=user_prompt,
        )
    raise ValueError(f"Unsupported LLM provider: {config.llm_provider!r}")
