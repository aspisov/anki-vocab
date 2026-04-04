---
name: anki-direct-add
description: Use when all Anki card fields are already known and the note should be added directly through `anki-vocab add`, with the existing TTS and AnkiConnect pipeline, without asking the CLI to generate fields with an LLM.
---

# anki-vocab add

Use this when you already know every card field and want to create the note directly.

Do not use the interactive session for this workflow.
Do not ask the CLI to infer fields.
Fill every field explicitly and call the command once.

## Preconditions

- Anki is running with AnkiConnect at the configured URL.
- `edge-tts` is installed and available.
- `tts.enabled` is `true` in config if audio should be attached.

## Rules

- Every option is required.
- Every value must be a non-empty string.
- Use `N/A` instead of empty strings for fields like `pattern`, `synonyms`, or `notes`.
- Only `cloze` may contain `[...]`.
- `context_source` should be the original source sentence, or `N/A` if there is none.
- `context` should be the final study sentence that TTS should read.

## Command

```bash
uv run anki-vocab add \
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

- Success prints the new Anki note id to stdout.
- Validation, TTS, or AnkiConnect failures exit non-zero and print the error to stderr.
