# anki-vocab CLI — Design Doc (v0)

Goal: fast capture + maintenance tool for generating Anki English vocab notes from `context | word` using GPT-5.2 + Edge TTS + AnkiConnect.

Non-goals (v0): GUI, PDF integration, auto word selection, frequency/difficulty ranking, complex TUI.

---

## 1. Commands (v0)

### 1) `anki-vocab session`
Interactive loop for reading sessions. Single-line capture.

**Input format**
- `context sentence | word`
- `word` (empty context)
- `:quit` exits.

**Loop (per item)**
1. Parse input → `(context, target)` (validate).
2. Normalize target (base form) and clean context (PDF artifacts, spacing).
3. Check if note exists in Anki.
4. Generate candidate card via GPT-5.2 (strict schema).
5. Generate TTS audio and attach (policy below).
6. Preview card in terminal.
7. Prompt user for action:
   - `a` add (new note)
   - `u` update existing note (only if exists)
   - `s` skip
   - `r` regen (same inputs)
   - `q` quit

**Defaults**
- If note does NOT exist: default action = `a`.
- If note exists: default action = `s` (safe) and show `u` option.

**Output**
- Human preview to stderr (preferred), minimal confirmations to stderr.

**Flags**
- `--yes` (auto-accept defaults; when exists, obey `update_policy`)
- `--update-policy ask|never|always` (default `ask`)
- Audio is only added when the audio field is empty.
- `--no-tts` (force disable TTS)
- `--dry-run` (never writes to Anki; still generates + previews)

---

### 2) `anki-vocab config`
Manage config used by other commands.

**Subcommands**
- `anki-vocab config init` (create config file with defaults)
- `anki-vocab config show` (print resolved config)
- `anki-vocab config set key value` (edit config)
- `anki-vocab config path` (print config path)

**Config keys**
- `deck`: default target deck
- `note_model`: Anki model name
- `field_map`: mapping from internal schema → Anki fields
- `ankiconnect_url`: default `http://127.0.0.1:8765`
- `openai_model`: default `gpt-5.2` (exact string configurable)
- `tts.voice`: Edge voice name (e.g. `en-US-JennyNeural`)
- `tts.field`: field name to store `[sound:...]` reference
- `tts.enabled`: bool
- `session.update_policy` (future)

**Sources / precedence**
CLI flags > env vars > config file > hardcoded defaults.

---

## 2. Note Schema (internal contract)

Internal `Card` object (canonical):
- `word_base` (string)
- `pos` (noun/verb/adj/idiom/phrasal verb)
- `ru_meaning` (short gloss)
- `definition` (<= 20 words, simple English)
- `context_en` (cleaned English sentence)
- `context_ru` (natural Russian translation)
- `rarity`,
- `cerf`,
- `audio_filename` (optional, e.g. `presumably_en-US-JennyNeural.mp3`)

Anki fields are defined by `field_map` in config.

---

## 3. AnkiConnect Integration

**Existence check**
- `findNotes` query uses configured field(s), default:
  - `"<WordField>:{word_base}" AND note:"<note_model>"`
- If multiple matches: treat as conflict, prompt user, and log.

**Add**
- `addNote` with `deckName`, `modelName`, `fields`, `tags`

**Update**
- `updateNoteFields` on note id
- Tag updates via `addTags`/`removeTags` if needed

**Audio**
- Generate mp3 via Edge TTS → base64 → `storeMediaFile`
- Insert into configured audio field as `[sound:<filename>]`
- Overwrite policy controlled by flags/config

---

## 4. OpenAI Prompting (GPT-5.2)

Single call returns strict JSON matching internal schema fields (except audio).
Rules enforced in prompt:
- normalize target to base form
- translate based strictly on context
- definition <= 20 words
- no extra keys, no extra commentary

Validation:
- JSON parse + schema validate
- enforce length constraints (truncate with warning or regen)

---

## 5. UX + Performance

- Session startup must be instant (no network checks at startup).
- Lazy-check OpenAI only when generating.
- Lazy-check AnkiConnect only when writing.
- Cache last context in session.

---

## 6. Errors + Exit Codes

- `0` success
- `2` usage/validation error
- `3` integration error (AnkiConnect unreachable, model/field mismatch)
- `4` OpenAI/TTS error
- `5` partial failure (batch update: some succeeded, some failed)

All errors go to stderr; JSON mode still outputs valid JSON for processed items.

---

## 7. Testing (minimum)

Unit tests (no network):
- parser for `word | context`
- normalization + cleaning
- JSON schema validation
- Anki payload mapping

Integration tests (opt-in):
- require local Anki + AnkiConnect
- optionally network for OpenAI/TTS (marked separately)

---

## 8. File Layout (suggested)

- `src/anki_vocab_cli/cli.py` (Typer app)
- `src/anki_vocab_cli/commands/session.py`
- `src/anki_vocab_cli/commands/update.py`
- `src/anki_vocab_cli/commands/config.py`
- `src/anki_vocab_cli/core/schema.py`
- `src/anki_vocab_cli/core/prompting.py`
- `src/anki_vocab_cli/core/cleaning.py`
- `src/anki_vocab_cli/integrations/ankiconnect.py`
- `src/anki_vocab_cli/integrations/openai_client.py`
- `src/anki_vocab_cli/integrations/edge_tts.py`
- `tests/...`

---

## Future Plan (backlog)

- Add `anki-vocab add` for one-off captures and scripted usage.
- Support multiple named profiles (e.g., `reading`, `work`) with `--profile`.
- Add batch capture from `--stdin`/`--file` for fast imports.
