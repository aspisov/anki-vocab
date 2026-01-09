import hashlib

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
    tmp_mp3 = f"/tmp/anki_tts_{tts_id}.mp3"
    synthesize_tts(text, tmp_mp3, voice=voice, rate=rate)
    audio_filename = f"tts_{tts_id}.mp3"
    store_media_file(ankiconnect_url, tmp_mp3, audio_filename)
    return f"[sound:{audio_filename}]"
