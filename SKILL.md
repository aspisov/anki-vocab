---
name: anki-card-generator
description: >
  Create and update Anki vocabulary cards with TTS audio via AnkiConnect.
  Use when asked to create flashcards, vocabulary cards, or Anki notes for English words.
---

# Anki Card Generator

Use this skill when the user asks you to create or update an Anki vocabulary card.

## Preconditions

- Anki is running with AnkiConnect at the configured URL.
- `edge-tts` is installed and available.
- `tts.enabled` is `true` in config if audio should be attached.

## Tools

```bash
# Inspect a note
uv run anki-vocab show NOTE_ID

# Create a note from explicit fields
uv run anki-vocab add --lemma ... --target-surface ... ...

# Update a note from explicit fields
uv run anki-vocab update NOTE_ID --lemma ... --target-surface ... ...

# Inspect active mapping and TTS config
uv run anki-vocab config show
```

## Card Fields Reference

Every card has 14 required fields. All values must be non-empty strings.

| Field | Description |
|---|---|
| `--lemma` | English lemma / canonical dictionary form. For idioms or phrasal verbs use the canonical form (e.g. "kick the bucket", "run out of"). |
| `--target-surface` | Exact substring from the source sentence (or from `context` if no source) to cloze out. Start from the target word. If the target is part of a longer idiom/collocation present in the text, extend to the full expression. |
| `--pos` | One of: `noun`, `verb`, `adjective`, `adverb`, `phrasal_verb`, `idiom`, `collocation`, `proper_noun`, `other`. `phrasal_verb` = verb + particle(s) as a unit; `idiom` = meaning not predictable from parts; `collocation` = common fixed pairing. |
| `--meaning-ru` | Short Russian gloss (2-6 words), not a sentence, matching the context sense. |
| `--definition` | Simple English definition (max 16 words), must match the context sense. |
| `--context-source` | Original source sentence verbatim, or `N/A` if there is none. |
| `--context` | Final Anki study sentence (10-18 words). Optimized so a single-blank cloze is unambiguous. Prefer American English. If no source sentence, invent a natural, non-generic sentence that clearly disambiguates the meaning. This is what TTS reads. |
| `--cloze` | Derived from `context` by replacing `target_surface` with `[...]`. Exactly one `[...]` per card. Only this field may contain `[...]`. |
| `--context-ru` | Natural Russian translation of `context` (preserve the same disambiguating cues). |
| `--pattern` | Stable preposition/particle/argument pattern if one applies (e.g. "adhere to + noun"). Otherwise `N/A`. |
| `--synonyms` | 2-4 synonyms matching POS and register that could replace the target in context. If not confident: `N/A`. |
| `--notes` | Max 2 short lines. At most one of: register note, common collocation, or "don't confuse with X". Otherwise `N/A`. |
| `--rarity` | One of: `Very common`, `Common`, `Uncommon`, `Rare`, `Literary/Academic`, `Unknown`. |
| `--cefr` | One of: `A2`, `B1`, `B2`, `C1`, `C2`, `Unknown`. |

## Rules

- Every field is required for both `add` and `update`.
- Use `N/A` instead of empty strings for optional-looking fields (`pattern`, `synonyms`, `notes`, `context_source`).
- Only `cloze` may contain `[...]`.
- `context_source` preserves the original source sentence verbatim, or `N/A`.
- `context` is the final study sentence — optimize it for cloze recall and TTS.
- Cloze-first: the context/cloze pair must make the target unambiguously predictable from context alone.
- For updates: rewrite only what improves the card. Keep the sense, lemma, and provenance stable unless the current note is wrong.

## Workflow

### Create a new note

1. Decide the full field set following the card fields reference above.
2. Run `uv run anki-vocab add ...` with every field filled explicitly.
3. Keep the printed note id for later updates.

### Update an existing note

1. Run `uv run anki-vocab show NOTE_ID`.
2. Read the current card fields from the JSON output.
3. Decide the full replacement field set.
4. Run `uv run anki-vocab update NOTE_ID ...` with every field filled explicitly.
5. Read back with `show` if you need to verify the stored result.

## Example

```bash
uv run anki-vocab add \
  --lemma "run" \
  --target-surface "run" \
  --pos "verb" \
  --meaning-ru "бежать" \
  --definition "to move swiftly on foot" \
  --context-source "I run every morning." \
  --context "I run every morning before work." \
  --cloze "I [...] every morning before work." \
  --context-ru "Я бегаю каждое утро перед работой." \
  --pattern "run + adverbial" \
  --synonyms "jog, sprint" \
  --notes "Common everyday verb." \
  --rarity "Very common" \
  --cefr "A2"
```

## Expected Result

- `show` prints JSON to stdout: `{note_id, model_name, tags, card}`.
- `add` prints the new note id to stdout.
- `update` prints the updated note id to stdout.
- Validation, TTS, or AnkiConnect failures exit non-zero with the error on stderr.
