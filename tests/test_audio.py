from pathlib import Path

from anki_vocab.core import audio


def test_build_audio_field_cleans_temp_file(monkeypatch) -> None:
    recorded: dict[str, str] = {}

    def fake_synthesize(text: str, out_mp3: str, *, voice: str, rate: str) -> None:
        recorded["path"] = out_mp3
        Path(out_mp3).write_bytes(b"dummy-audio")

    def fake_store(url: str, local_path: str, filename_in_anki: str) -> str:
        assert local_path == recorded["path"]
        return "ok"

    monkeypatch.setattr(audio, "synthesize_tts", fake_synthesize)
    monkeypatch.setattr(audio, "store_media_file", fake_store)

    result = audio.build_audio_field("http://localhost:8765", "hello", voice="voice", rate="+0%")

    assert result.startswith("[sound:tts_")
    assert "path" in recorded
    assert not Path(recorded["path"]).exists()


def test_audio_tag_count_counts_sound_tags() -> None:
    assert audio.audio_tag_count(None) == 0
    assert audio.audio_tag_count("") == 0
    assert audio.audio_tag_count("[sound:a.mp3] [sound:b.mp3]") == 2


def test_build_audio_bundle_joins_audio_tags(monkeypatch) -> None:
    def fake_build_audio_field(url: str, text: str, *, voice: str, rate: str) -> str:
        return f"[sound:{text}]"

    monkeypatch.setattr(audio, "build_audio_field", fake_build_audio_field)

    result = audio.build_audio_bundle(
        "http://localhost:8765",
        lemma="run",
        context="I run.",
        voice="voice",
        rate="+0%",
    )

    assert result == "[sound:run] [sound:I run.]"
