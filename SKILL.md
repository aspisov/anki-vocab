---
name: anki-card-agent
description: Use when an agent should create a new Anki card or update an existing one directly through this repo's CLI, using `anki-vocab show`, `anki-vocab add`, and `anki-vocab update` so AnkiConnect and TTS are handled without the interactive session.
---

# anki card agent

Use this when the user asks you to create or update a card yourself.

Do not use the interactive session.
Do not ask the CLI to infer fields with the LLM path unless the user explicitly wants that.
Read the current card first for updates, then write the full field set explicitly.

## Preconditions

- Anki is running with AnkiConnect at the configured URL.
- `edge-tts` is installed and available.
- `tts.enabled` is `true` in config if audio should be attached.

## Tools

- Inspect a note:
  - `uv run anki-vocab show NOTE_ID`
- Create a note from explicit fields:
  - `uv run anki-vocab add ...`
- Update a note from explicit fields:
  - `uv run anki-vocab update NOTE_ID ...`
- Inspect active mapping and TTS config if needed:
  - `uv run anki-vocab config show`

## Rules

- Every card field is required for `add` and `update`.
- Every value must be a non-empty string.
- Use `N/A` instead of empty strings for fields like `pattern`, `synonyms`, or `notes`.
- Only `cloze` may contain `[...]`.
- `context_source` should preserve the original source sentence, or `N/A` if there is none.
- `context` should be the final study sentence that TTS should read.
- For updates, rewrite only what improves the card. Keep the sense, lemma, and provenance stable unless the current note is wrong.

## Workflow

### Update an existing note

1. Run `uv run anki-vocab show NOTE_ID`.
2. Read the current card fields from the JSON output.
3. Decide the full replacement field set.
4. Run `uv run anki-vocab update NOTE_ID ...` with every field filled explicitly.
5. Read back with `show` if you need to verify the stored result.

### Create a new note

1. Decide the full field set.
2. Run `uv run anki-vocab add ...` with every field filled explicitly.
3. Keep the printed note id for later updates.

## Example update

```bash
uv run anki-vocab update 1772881185545 \
  --lemma "run" \
  --target-surface "run" \
  --pos "verb" \
  --meaning-ru "бежать" \
  --definition "to move swiftly" \
  --context-source "I run every morning." \
  --context "I run every morning before work." \
  --cloze "I [...] every morning before work." \
  --context-ru "Я бегаю каждое утро перед работой." \
  --pattern "run + adverbial" \
  --synonyms "jog, sprint" \
  --notes "Common everyday verb." \
  --rarity "Common" \
  --cefr "A2"
```

## Expected result

- `show` prints JSON to stdout.
- `add` prints the new note id to stdout.
- `update` prints the updated note id to stdout.
- Validation, TTS, or AnkiConnect failures exit non-zero and print the error to stderr.
