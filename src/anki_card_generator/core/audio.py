import hashlib
import os
import tempfile

from ..integrations.ankiconnect import store_media_file
from ..integrations.edge_tts import synthesize_tts


def _stable_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def build_audio_field(
    ankiconnect_url: str,
    text: str,
    *,
    voice: str,
    rate: str,
) -> str:
    tts_id = _stable_id(f"{voice}|{rate}|{text}")
    audio_filename = f"tts_{tts_id}.mp3"
    with tempfile.NamedTemporaryFile(prefix=f"anki_tts_{tts_id}_", suffix=".mp3", delete=False) as tmp:
        tmp_mp3 = tmp.name
    try:
        synthesize_tts(text, tmp_mp3, voice=voice, rate=rate)
        store_media_file(ankiconnect_url, tmp_mp3, audio_filename)
    finally:
        try:
            os.remove(tmp_mp3)
        except FileNotFoundError:
            pass
    return f"[sound:{audio_filename}]"
