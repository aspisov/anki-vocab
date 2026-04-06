# anki-card-generator

CLI for AI agents to create and maintain Anki English vocabulary cards with Edge TTS audio via AnkiConnect.

The repo-local workflow should use module execution:

```bash
uv run python -m anki_vocab --help
```

This is slightly longer than `uv run anki-vocab`, but it is deterministic inside the repo. If the console-script shim is missing from `.venv/bin`, `uv run anki-vocab` can silently fall through to some other `anki-vocab` on your `PATH`.

## Install

Published package:

```bash
pipx install anki-vocab
```

Or:

```bash
uv pip install anki-vocab
```

Local development:

```bash
uv pip install -e .
```

## Prerequisites

- Anki with AnkiConnect running at `http://127.0.0.1:8765`.
- `edge-tts` installed as a dependency.

## Config

Initialize config:

```bash
uv run python -m anki_vocab config init
```

Show config:

```bash
uv run python -m anki_vocab config show
```

Set a value:

```bash
uv run python -m anki_vocab config set deck "My Deck"
uv run python -m anki_vocab config set tts.voice "en-US-GuyNeural"
```

## Card Tools

Inspect a note:

```bash
uv run python -m anki_vocab show 1772881185545
```

Create a note:

```bash
uv run python -m anki_vocab add \
  --lemma run \
  --target-surface run \
  --pos verb \
  --meaning-ru "бежать" \
  --definition "to move swiftly" \
  --context-source "I run every morning." \
  --context "I run every morning before work." \
  --cloze "I [...] every morning before work." \
  --context-ru "Я бегаю каждое утро перед работой." \
  --pattern "run + adverbial" \
  --synonyms "jog, sprint" \
  --notes "Common everyday verb." \
  --rarity Common \
  --cefr A2
```

Update a note:

```bash
uv run python -m anki_vocab update 1772881185545 \
  --lemma accomplice \
  --target-surface accomplice \
  --pos noun \
  --meaning-ru "сообщник" \
  --definition "someone who helps another commit a crime" \
  --context-source "You're gonna be an accomplice." \
  --context "By helping the thief escape, you became an accomplice to the crime." \
  --cloze "By helping the thief escape, you became an [...] to the crime." \
  --context-ru "Помогая вору скрыться, ты стал сообщником преступления." \
  --pattern "accomplice to + crime | accomplice in + act" \
  --synonyms "accessory, collaborator, confederate" \
  --notes "Criminal/legal context." \
  --rarity Common \
  --cefr C1
```

## Development

```bash
uv pip install -e ".[dev]"
uv run python -m pytest
```
