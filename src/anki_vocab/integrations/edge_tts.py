import subprocess


def synthesize_tts(text: str, out_mp3: str, *, voice: str, rate: str) -> None:
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
