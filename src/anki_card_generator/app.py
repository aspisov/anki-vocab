import base64
import hashlib
import json
import subprocess
import urllib.request
from importlib import resources
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

ANKI_CONNECT_URL = "http://127.0.0.1:8765"

DEFAULT_DECK_NAME = "Reading"
DEFAULT_NOTE_MODEL = "English"

DEFAULT_VOICE = "en-US-AvaNeural"
DEFAULT_OPENAI_MODEL = "gpt-5.2"


def _stable_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _read_system_prompt() -> str:
    return (
        resources.files("anki_card_generator")
        .joinpath("system_prompt.jinja")
        .read_text(encoding="utf-8")
        .strip()
    )


def anki_request(action: str, params: dict[str, Any] | None = None) -> Any:
    payload = json.dumps(
        {"action": action, "version": 6, "params": params or {}}
    ).encode("utf-8")
    req = urllib.request.Request(
        ANKI_CONNECT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if data.get("error") is not None:
        raise RuntimeError(f"AnkiConnect error for {action}: {data['error']}")
    return data["result"]


def store_media_file(local_path: str, filename_in_anki: str) -> str:
    b64 = base64.b64encode(Path(local_path).read_bytes()).decode("utf-8")
    return anki_request("storeMediaFile", {"filename": filename_in_anki, "data": b64})


def synthesize_tts_edge(
    text: str,
    out_mp3: str,
    *,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
) -> None:
    cmd = [
        "edge-tts",
        "--voice",
        voice,
        "--rate",
        rate,
        "--text",
        text,
        "--write-media",
        out_mp3,
    ]
    subprocess.run(cmd, check=True)


def openai_generate_card(
    sentence: str,
    word: str,
    *,
    model: str = DEFAULT_OPENAI_MODEL,
) -> dict[str, str]:
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

    card = json.loads(content)
    required_keys = [
        "Word",
        "Part of Speech",
        "Russian Meaning",
        "Definition",
        "Context Sentence",
        "Sentence Translation",
        "Rarity",
        "CEFR",
    ]
    for k in required_keys:
        if k not in card or not isinstance(card[k], str) or not card[k].strip():
            raise RuntimeError(
                f"OpenAI returned invalid card JSON: missing/empty {k!r}"
            )

    if "TTS Text" in card and not isinstance(card["TTS Text"], str):
        raise RuntimeError(
            'OpenAI returned invalid card JSON: "TTS Text" must be a string'
        )

    return {k: str(v) for k, v in card.items()}


def note_exists(model: str, word_base_form: str) -> bool:
    query = f'note:"{model}" Word:"{word_base_form}"'
    result = anki_request("findNotes", {"query": query})
    return len(result) > 0


def add_note_with_audio(
    card: dict[str, str],
    *,
    deck_name: str = DEFAULT_DECK_NAME,
    note_model: str = DEFAULT_NOTE_MODEL,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    tags: list[str] | None = None,
    allow_duplicate: bool = False,
) -> int:
    word = card["Word"].strip()
    tts_text = card.get("TTS Text", word).strip()
    tts_id = _stable_id(f"{voice}|{rate}|{tts_text}")

    tmp_mp3 = f"/tmp/anki_tts_{tts_id}.mp3"
    synthesize_tts_edge(tts_text, tmp_mp3, voice=voice, rate=rate)

    audio_filename = f"tts_{tts_id}.mp3"
    store_media_file(tmp_mp3, audio_filename)

    note = {
        "deckName": deck_name,
        "modelName": note_model,
        "fields": {
            "Word": card["Word"].strip(),
            "Part of Speech": card["Part of Speech"].strip(),
            "Russian Meaning": card["Russian Meaning"].strip(),
            "Definition": card["Definition"].strip(),
            "Context Sentence": card["Context Sentence"].strip(),
            "Sentence Translation": card["Sentence Translation"].strip(),
            "Rarity": card["Rarity"].strip(),
            "CEFR": card["CEFR"].strip(),
            "Audio": f"[sound:{audio_filename}]",
        },
        "options": {"allowDuplicate": allow_duplicate},
        "tags": tags or ["auto", "tts"],
    }

    return anki_request("addNote", {"note": note})


def run(
    *,
    sentence: str,
    word: str,
    deck: str = DEFAULT_DECK_NAME,
    note_model: str = DEFAULT_NOTE_MODEL,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    openai_model: str = DEFAULT_OPENAI_MODEL,
    skip_existing: bool = True,
    dry_run: bool = False,
) -> int | None:
    sentence = sentence.strip()
    word = word.strip()
    if not word:
        raise ValueError("word cannot be empty")

    card = openai_generate_card(sentence, word, model=openai_model)
    print(json.dumps(card, ensure_ascii=False, indent=2))
    if dry_run:
        return None

    try:
        choice = input("\nPress Enter to add to Anki (any other input cancels): ")
    except EOFError:
        print("Cancelled.")
        return None
    if choice.strip():
        print("Cancelled.")
        return None

    anki_request("version")

    if skip_existing and note_exists(note_model, card["Word"].strip()):
        print(f'Skipping: note already exists for Word="{card["Word"].strip()}"')
        return None

    new_id = add_note_with_audio(
        card,
        deck_name=deck,
        note_model=note_model,
        voice=voice,
        rate=rate,
    )
    print(f"Added note id: {new_id}")
    return new_id
