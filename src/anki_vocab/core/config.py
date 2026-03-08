from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_FIELD_MAP = {
    "lemma": "Word",
    "target_surface": "Target Surface",
    "pos": "Part of Speech",
    "meaning_ru": "Russian Meaning",
    "definition": "Definition",
    "context_source": "Context Sentence Source",
    "context": "Context Sentence",
    "cloze": "Cloze Sentence",
    "context_ru": "Sentence Translation",
    "pattern": "Pattern",
    "synonyms": "Synonyms",
    "notes": "Notes",
    "rarity": "Rarity",
    "cefr": "CEFR",
    "audio": "Audio",
}


@dataclass(frozen=True)
class Config:
    deck: str
    note_model: str
    field_map: dict[str, str]
    ankiconnect_url: str
    source_language: str
    llm_provider: str
    openai_api_key: str
    openai_model: str
    ollama_url: str
    ollama_model: str
    tts_voice: str
    tts_rate: str
    tts_lemma_field: str
    tts_context_field: str
    tts_enabled: bool


DEFAULT_CONFIG = Config(
    deck="Reading",
    note_model="English",
    field_map=DEFAULT_FIELD_MAP,
    ankiconnect_url="http://127.0.0.1:8765",
    source_language="en",
    llm_provider="openai",
    openai_api_key="",
    openai_model="gpt-5.2",
    ollama_url="http://127.0.0.1:11434",
    ollama_model="gemma2:2b",
    tts_voice="en-US-AvaNeural",
    tts_rate="+0%",
    tts_lemma_field="Audio Lemma",
    tts_context_field="Audio Context",
    tts_enabled=True,
)

DEFAULT_CONFIG_DICT = {
    "deck": DEFAULT_CONFIG.deck,
    "note_model": DEFAULT_CONFIG.note_model,
    "field_map": DEFAULT_FIELD_MAP,
    "ankiconnect_url": DEFAULT_CONFIG.ankiconnect_url,
    "source_language": DEFAULT_CONFIG.source_language,
    "llm_provider": DEFAULT_CONFIG.llm_provider,
    "openai_api_key": DEFAULT_CONFIG.openai_api_key,
    "openai_model": DEFAULT_CONFIG.openai_model,
    "ollama_url": DEFAULT_CONFIG.ollama_url,
    "ollama_model": DEFAULT_CONFIG.ollama_model,
    "tts": {
        "voice": DEFAULT_CONFIG.tts_voice,
        "rate": DEFAULT_CONFIG.tts_rate,
        "lemma_field": DEFAULT_CONFIG.tts_lemma_field,
        "context_field": DEFAULT_CONFIG.tts_context_field,
        "enabled": DEFAULT_CONFIG.tts_enabled,
    },
}


def config_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "anki-vocab" / "config.json"


def _read_file_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _env_override(name: str) -> str | None:
    return os.environ.get(name)


def _coerce_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _merge_config(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged


def resolve_config() -> Config:
    file_config = _read_file_config(config_path())
    merged = _merge_config(DEFAULT_CONFIG_DICT, file_config)

    env_map = {
        "ANKI_VOCAB_DECK": ("deck", str),
        "ANKI_VOCAB_NOTE_MODEL": ("note_model", str),
        "ANKI_VOCAB_ANKICONNECT_URL": ("ankiconnect_url", str),
        "ANKI_VOCAB_SOURCE_LANGUAGE": ("source_language", str),
        "ANKI_VOCAB_LLM_PROVIDER": ("llm_provider", str),
        "ANKI_VOCAB_OPENAI_API_KEY": ("openai_api_key", str),
        "ANKI_VOCAB_OPENAI_MODEL": ("openai_model", str),
        "ANKI_VOCAB_OLLAMA_URL": ("ollama_url", str),
        "ANKI_VOCAB_OLLAMA_MODEL": ("ollama_model", str),
        "ANKI_VOCAB_TTS_VOICE": ("tts.voice", str),
        "ANKI_VOCAB_TTS_RATE": ("tts.rate", str),
        "ANKI_VOCAB_TTS_FIELD": ("tts.field", str),
        "ANKI_VOCAB_TTS_LEMMA_FIELD": ("tts.lemma_field", str),
        "ANKI_VOCAB_TTS_CONTEXT_FIELD": ("tts.context_field", str),
        "ANKI_VOCAB_TTS_ENABLED": ("tts.enabled", _coerce_bool),
    }

    for env_name, (key, caster) in env_map.items():
        value = _env_override(env_name)
        if value is None:
            continue
        target = merged
        parts = key.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = caster(value)

    field_map = merged.get("field_map", {})
    if not isinstance(field_map, dict):
        raise ValueError("field_map must be a mapping in config")

    tts_config = merged.get("tts", {})
    tts_enabled = tts_config.get("enabled", True)
    if isinstance(tts_enabled, str):
        tts_enabled = _coerce_bool(tts_enabled)

    fallback_field = tts_config.get("field", "")
    tts_lemma_field = str(
        tts_config.get("lemma_field", fallback_field or DEFAULT_CONFIG.tts_lemma_field)
    )
    tts_context_field = str(
        tts_config.get("context_field", fallback_field or DEFAULT_CONFIG.tts_context_field)
    )

    provider = str(merged.get("llm_provider", DEFAULT_CONFIG.llm_provider)).strip().lower()
    if provider not in {"openai", "ollama"}:
        raise ValueError("llm_provider must be 'openai' or 'ollama'")

    return Config(
        deck=str(merged.get("deck", DEFAULT_CONFIG.deck)),
        note_model=str(merged.get("note_model", DEFAULT_CONFIG.note_model)),
        field_map={str(k): str(v) for k, v in field_map.items()},
        ankiconnect_url=str(merged.get("ankiconnect_url", DEFAULT_CONFIG.ankiconnect_url)),
        source_language=str(merged.get("source_language", DEFAULT_CONFIG.source_language)),
        llm_provider=provider,
        openai_api_key=str(merged.get("openai_api_key", DEFAULT_CONFIG.openai_api_key)),
        openai_model=str(merged.get("openai_model", DEFAULT_CONFIG.openai_model)),
        ollama_url=str(merged.get("ollama_url", DEFAULT_CONFIG.ollama_url)),
        ollama_model=str(merged.get("ollama_model", DEFAULT_CONFIG.ollama_model)),
        tts_voice=str(tts_config.get("voice", DEFAULT_CONFIG.tts_voice)),
        tts_rate=str(tts_config.get("rate", DEFAULT_CONFIG.tts_rate)),
        tts_lemma_field=tts_lemma_field,
        tts_context_field=tts_context_field,
        tts_enabled=bool(tts_enabled),
    )


def write_default_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(DEFAULT_CONFIG_DICT, indent=2, sort_keys=True), encoding="utf-8")


def update_config_value(path: Path, key: str, value: str) -> None:
    config = _read_file_config(path)
    if not config:
        config = json.loads(json.dumps(DEFAULT_CONFIG_DICT))

    parts = key.split(".")
    current: dict[str, Any] = config
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")


def config_as_dict(config: Config) -> dict[str, Any]:
    return {
        "deck": config.deck,
        "note_model": config.note_model,
        "field_map": dict(config.field_map),
        "ankiconnect_url": config.ankiconnect_url,
        "source_language": config.source_language,
        "llm_provider": config.llm_provider,
        "openai_api_key": config.openai_api_key,
        "openai_model": config.openai_model,
        "ollama_url": config.ollama_url,
        "ollama_model": config.ollama_model,
        "tts": {
            "voice": config.tts_voice,
            "rate": config.tts_rate,
            "lemma_field": config.tts_lemma_field,
            "context_field": config.tts_context_field,
            "enabled": config.tts_enabled,
        },
    }
