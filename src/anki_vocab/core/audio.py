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


def build_audio_fields(
    ankiconnect_url: str,
    *,
    lemma: str,
    context: str,
    voice: str,
    rate: str,
) -> tuple[str | None, str | None]:
    lemma_audio = None
    context_audio = None
    if lemma.strip():
        lemma_audio = build_audio_field(ankiconnect_url, lemma, voice=voice, rate=rate)
    if context.strip():
        context_audio = build_audio_field(ankiconnect_url, context, voice=voice, rate=rate)
    return lemma_audio, context_audio
