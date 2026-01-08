import base64
import json
import urllib.request
from pathlib import Path
from typing import Any


def ankiconnect_request(url: str, action: str, params: dict[str, Any] | None = None) -> Any:
    payload = json.dumps(
        {"action": action, "version": 6, "params": params or {}}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if data.get("error") is not None:
        raise RuntimeError(f"AnkiConnect error for {action}: {data['error']}")
    return data["result"]


def store_media_file(url: str, local_path: str, filename_in_anki: str) -> str:
    b64 = base64.b64encode(Path(local_path).read_bytes()).decode("utf-8")
    return ankiconnect_request(
        url, "storeMediaFile", {"filename": filename_in_anki, "data": b64}
    )


def find_notes(url: str, query: str) -> list[int]:
    result = ankiconnect_request(url, "findNotes", {"query": query})
    return [int(item) for item in result]


def notes_info(url: str, note_ids: list[int]) -> list[dict[str, Any]]:
    if not note_ids:
        return []
    return ankiconnect_request(url, "notesInfo", {"notes": note_ids})


def add_note(url: str, note: dict[str, Any]) -> int:
    return int(ankiconnect_request(url, "addNote", {"note": note}))


def update_note_fields(url: str, note_id: int, fields: dict[str, str]) -> None:
    ankiconnect_request(url, "updateNoteFields", {"note": {"id": note_id, "fields": fields}})


def add_tags(url: str, note_id: int, tags: list[str]) -> None:
    if tags:
        ankiconnect_request(url, "addTags", {"notes": [note_id], "tags": " ".join(tags)})
