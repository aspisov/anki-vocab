from pathlib import Path

from anki_card_generator.core import audio


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
