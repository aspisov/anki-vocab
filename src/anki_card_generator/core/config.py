from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_FIELD_MAP = {
    "word_base": "Word",
    "pos": "Part of Speech",
    "ru_meaning": "Russian Meaning",
    "definition": "Definition",
    "context_en": "Context Sentence",
    "context_ru": "Sentence Translation",
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
    openai_model: str
    tts_voice: str
    tts_rate: str
    tts_field: str
    tts_enabled: bool


DEFAULT_CONFIG = Config(
    deck="Reading",
    note_model="English",
    field_map=DEFAULT_FIELD_MAP,
    ankiconnect_url="http://127.0.0.1:8765",
    openai_model="gpt-5.2",
    tts_voice="en-US-AvaNeural",
    tts_rate="+0%",
    tts_field="Audio",
    tts_enabled=True,
)

DEFAULT_CONFIG_DICT = {
    "deck": DEFAULT_CONFIG.deck,
    "note_model": DEFAULT_CONFIG.note_model,
    "field_map": DEFAULT_FIELD_MAP,
    "ankiconnect_url": DEFAULT_CONFIG.ankiconnect_url,
    "openai_model": DEFAULT_CONFIG.openai_model,
    "tts": {
        "voice": DEFAULT_CONFIG.tts_voice,
        "rate": DEFAULT_CONFIG.tts_rate,
        "field": DEFAULT_CONFIG.tts_field,
        "enabled": DEFAULT_CONFIG.tts_enabled,
    },
    "session": {},
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
        "ANKI_VOCAB_OPENAI_MODEL": ("openai_model", str),
        "ANKI_VOCAB_TTS_VOICE": ("tts.voice", str),
        "ANKI_VOCAB_TTS_RATE": ("tts.rate", str),
        "ANKI_VOCAB_TTS_FIELD": ("tts.field", str),
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

    return Config(
        deck=str(merged.get("deck", DEFAULT_CONFIG.deck)),
        note_model=str(merged.get("note_model", DEFAULT_CONFIG.note_model)),
        field_map={str(k): str(v) for k, v in field_map.items()},
        ankiconnect_url=str(merged.get("ankiconnect_url", DEFAULT_CONFIG.ankiconnect_url)),
        openai_model=str(merged.get("openai_model", DEFAULT_CONFIG.openai_model)),
        tts_voice=str(tts_config.get("voice", DEFAULT_CONFIG.tts_voice)),
        tts_rate=str(tts_config.get("rate", DEFAULT_CONFIG.tts_rate)),
        tts_field=str(tts_config.get("field", DEFAULT_CONFIG.tts_field)),
        tts_enabled=bool(tts_enabled),
    )


def write_default_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(DEFAULT_CONFIG_DICT, indent=2, sort_keys=True), encoding="utf-8"
    )


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
        "openai_model": config.openai_model,
        "tts": {
            "voice": config.tts_voice,
            "rate": config.tts_rate,
            "field": config.tts_field,
            "enabled": config.tts_enabled,
        },
        "session": {},
    }
