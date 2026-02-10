# anki-vocab CLI Specification

Version: 0.1.3  
Status: Current implemented behavior contract

## 1. Purpose

`anki-vocab` is a CLI that creates and updates Anki vocabulary notes from:
- a target word or phrase
- an optional source context sentence
- LLM-generated card content
- optional generated audio (TTS)

Primary integrations:
- AnkiConnect HTTP API
- OpenAI Chat Completions API or local Ollama API
- `edge-tts` CLI for MP3 synthesis

## 2. Scope and Non-Goals

In scope:
- Command behavior for `session`, `update`, and `config`
- Configuration structure, defaults, and override precedence
- Card schema and mapping to Anki note fields
- Error and exit behavior currently implemented

Out of scope:
- UX redesign
- Backward-compatible aliases not present in code
- Batch import/export workflows
- Scheduling or background jobs

## 3. Runtime Requirements

- Python 3.11+
- Anki with AnkiConnect available at configured URL (default `http://127.0.0.1:8765`)
- One LLM provider:
  - OpenAI (`llm_provider=openai`)
  - Ollama (`llm_provider=ollama`)
- `edge-tts` executable available if TTS is enabled

## 4. Entrypoints

Supported entrypoints:
- `anki-vocab` (console script)
- `python -m anki_vocab`
- `python main.py`

## 5. Configuration

### 5.1 Config path

Config file path:
- `${XDG_CONFIG_HOME}/anki-vocab/config.json` when `XDG_CONFIG_HOME` is set
- otherwise `~/.config/anki-vocab/config.json`

### 5.2 Config defaults

Default config object:

```json
{
  "deck": "Reading",
  "note_model": "English",
  "field_map": {
    "lemma": "Word",
    "target_surface": "Target Surface",
    "pos": "Part of Speech",
    "meaning_ru": "Russian Meaning",
    "definition": "Definition",
    "context_source": "Context Sentence Source",
    "context": "Context Sentence",
    "cloze": "Cloze Sentence",
    "context_ru": "Sentence Translation",
    "pattern": "Pattern",
    "synonyms": "Synonyms",
    "notes": "Notes",
    "rarity": "Rarity",
    "cefr": "CEFR",
    "audio": "Audio"
  },
  "ankiconnect_url": "http://127.0.0.1:8765",
  "source_language": "en",
  "llm_provider": "openai",
  "openai_api_key": "",
  "openai_model": "gpt-5.2",
  "ollama_url": "http://127.0.0.1:11434",
  "ollama_model": "gemma2:2b",
  "tts": {
    "voice": "en-US-AvaNeural",
    "rate": "+0%",
    "lemma_field": "Audio Lemma",
    "context_field": "Audio Context",
    "enabled": true
  },
  "session": {}
}
```

### 5.3 Override precedence

Effective config precedence is:
1. hardcoded defaults
2. config file values
3. environment variables
4. command options (for supported flags)

### 5.4 Environment variables

Supported env overrides:
- `ANKI_VOCAB_DECK`
- `ANKI_VOCAB_NOTE_MODEL`
- `ANKI_VOCAB_ANKICONNECT_URL`
- `ANKI_VOCAB_SOURCE_LANGUAGE`
- `ANKI_VOCAB_LLM_PROVIDER`
- `ANKI_VOCAB_OPENAI_API_KEY`
- `ANKI_VOCAB_OPENAI_MODEL`
- `ANKI_VOCAB_OLLAMA_URL`
- `ANKI_VOCAB_OLLAMA_MODEL`
- `ANKI_VOCAB_TTS_VOICE`
- `ANKI_VOCAB_TTS_RATE`
- `ANKI_VOCAB_TTS_FIELD` (legacy fallback for both lemma/context audio fields)
- `ANKI_VOCAB_TTS_LEMMA_FIELD`
- `ANKI_VOCAB_TTS_CONTEXT_FIELD`
- `ANKI_VOCAB_TTS_ENABLED` (`1|true|yes|on` => `true`, otherwise `false`)

### 5.5 Validation rules

- `field_map` must be a JSON object; otherwise resolution fails.
- `llm_provider` is normalized to lowercase and must be `openai` or `ollama`; otherwise resolution fails.
- TTS field names resolve as:
  - `tts.lemma_field` and `tts.context_field` when present
  - else `tts.field` for both (legacy fallback)
  - else defaults

### 5.6 Config commands

- `anki-vocab config init [--force]`
  - creates default config
  - fails if config exists and `--force` is not provided
- `anki-vocab config show`
  - prints merged effective config as JSON
  - redacts non-empty `openai_api_key` as `********`
- `anki-vocab config set KEY VALUE`
  - sets nested key path (dot notation supported)
  - writes string values as provided (no type coercion at write time)
- `anki-vocab config path`
  - prints config file path

## 6. Top-level CLI behavior

If invoked without subcommand:
- loads config
- if provider is `openai` and API key is empty:
  - on non-TTY stdin: exits with code 1 and message
  - on TTY stdin: prompts for key and writes it to config; empty input exits code 1
- shows interactive menu:
  - `Session`
  - `Update`
  - `Config` (submenu: `Init`, `Show`, `Set`, `Path`, `Back`)
  - `Quit`

If a subcommand is provided, normal Typer command flow is used.

## 7. Card schema contract

LLM output must parse into a `Card` where all fields are non-empty strings:
- `lemma`
- `target_surface`
- `pos`
- `meaning_ru`
- `definition`
- `context_source`
- `context`
- `cloze`
- `context_ru`
- `pattern`
- `synonyms`
- `notes`
- `rarity`
- `cefr`

Behavioral constraints enforced by prompt + parser:
- output must be JSON object
- only `cloze` may contain `[...]`
- `context_source` is system-owned and overwritten by CLI (`source sentence` or `"N/A"`)

## 8. `session` command

Command:
- `anki-vocab session [options]`

Options:
- `--deck`
- `--note-model`
- `--openai-model`
- `--llm-provider`
- `--ollama-model`
- `--ollama-url`
- `--voice`
- `--rate`
- `--yes`
- `--no-tts`
- `--dry-run`

### 8.1 Input grammar

Prompt is `anki-vocab> `.

Accepted input forms per line:
- `context sentence | target`
- `target`
- `:quit` or `:q` (immediate exit)

Invalid input:
- `| target` => error ("Context is missing. Include it before '|'.")
- `context |` => error ("Provide a word/phrase after the separator.")

### 8.2 Processing flow

For each entered item:
1. Clean context (`strip`, collapse whitespace, remove spaces before `,.;:!?`).
2. Generate card via active LLM provider.
3. Render generated card to stderr.
4. If `--dry-run`, return to next input line without writes.
5. Find existing notes by lemma:
   - query format: `note:"<note_model>" <word_field>:"<lemma>"`
   - `<word_field>` from `field_map["lemma"]` fallback `"Word"`
6. Choose action:
   - `Add`
   - `Update`
   - `Skip`
   - `Regenerate`
   - `Quit`
   - default action:
     - `Add` when no existing notes
     - `Skip` when existing notes found
   - with `--yes`, default action is auto-selected
7. Execute action:
   - `Regenerate` asks optional feedback and reruns generation with `CURRENT_CARD_JSON` + `USER_PROMPT`.
   - `Add` creates note in configured deck/model, `allowDuplicate=false`, `tags=["auto"]` plus `"tts"` when any audio attached.
   - `Update` updates one existing note:
     - if one match, use it
     - if multiple, show picker with manual note-id fallback

### 8.3 TTS behavior in session

When TTS enabled:
- generate audio for lemma and context (if non-empty)
- upload media to Anki via `storeMediaFile`
- write sound tags to `tts.lemma_field` and `tts.context_field`

`--no-tts` disables audio for current command only.

## 9. `update` command

Command:
- `anki-vocab update [options]`

Options:
- `--note-id`
- `--prompt`
- `--note-model`
- `--openai-model`
- `--llm-provider`
- `--ollama-model`
- `--ollama-url`
- `--voice`
- `--rate`
- `--no-tts`
- `--dry-run`

### 9.1 Note id and prompt input

When `--note-id` is not provided, CLI loops with:
- `Note id (or 'q' to quit): `

Accepted manual forms:
- `<note_id>`
- `<note_id> | <prompt>`

Invalid manual forms:
- non-numeric id => error ("Invalid note id.")
- missing prompt after pipe => error ("Prompt is missing after '|'.")

Prompt precedence:
- if `--prompt` is provided, it overrides inline prompt
- otherwise inline prompt is used

### 9.2 Update flow

For each resolved note id:
1. Fetch note via `notesInfo`.
2. If missing, print "Note id <id> not found." and continue.
3. Read lemma field (`field_map["lemma"]` fallback `Word`); if missing, skip with error.
4. Source sentence selection:
   - use `field_map["context_source"]` value when present
   - else fallback to `field_map["context"]`
5. Build `CURRENT_CARD_JSON` from mapped fields.
6. If prompt equals `tts` (case-insensitive, trimmed), skip LLM and perform TTS-only update.
7. Else generate and render updated card.
8. If `--dry-run`, skip writes and continue loop.
9. Ask confirmation (`Update this note?`, default yes).
10. Update note fields, optionally including regenerated TTS fields.

### 9.3 TTS-only mode

`--prompt "tts"` (or inline `| tts`) means:
- do not call LLM
- regenerate audio using existing lemma and cleaned existing context
- update only configured audio fields

## 10. LLM provider contract

### 10.1 Provider routing

- `openai` => OpenAI client
- `ollama` => Ollama client
- unknown provider => failure

### 10.2 OpenAI behavior

- Loads `.env` once per process via `python-dotenv`.
- Uses Chat Completions JSON mode (`response_format={"type":"json_object"}`).
- Empty response content => failure.
- Parsed payload is validated by schema parser.
- `context_source` is overwritten from input sentence or `"N/A"`.

### 10.3 Ollama behavior

- Requires non-empty model and base URL.
- Calls `<ollama_url>/api/chat` with `stream=false`, `format=json`, temperature `0.2`.
- HTTP and URL errors are converted to runtime failures with details.
- Invalid or empty JSON content fails.
- Parsed payload is validated by schema parser.
- `context_source` is overwritten from input sentence or `"N/A"`.

## 11. AnkiConnect contract

Used actions:
- `findNotes`
- `notesInfo`
- `addNote`
- `updateNoteFields`
- `storeMediaFile`
- `addTags` helper exists but is not used in current command flows

All AnkiConnect calls:
- send `{"action": ..., "version": 6, "params": ...}`
- fail when response contains non-null `error`

## 12. TTS contract

- audio filename is deterministic: `tts_<sha1(voice|rate|text)[:16]>.mp3`
- temporary local file is always removed after upload attempt
- audio field values use Anki sound syntax: `[sound:<filename>.mp3]`
- lemma/context audio generation is independent; empty text skips that side

## 13. Error handling and exit codes

Explicitly defined exits:
- top-level openai missing key on non-TTY: exit code `1`
- top-level openai key prompt with empty input: exit code `1`
- `update` LLM generation failure: exit code `4`

Other failures:
- config validation failures, AnkiConnect failures, network failures, subprocess failures, and uncaught runtime exceptions surface as command errors (fail-fast behavior; no silent fallback).

## 14. Design decisions and tradeoffs

### 14.1 Current-state spec first

Decision:
- This spec documents implemented behavior as the source of truth.

Tradeoff:
- Pros: avoids drift between docs and code.
- Cons: preserves some rough edges as "specified" until intentionally changed.

Rejected alternative:
- Writing a future-state aspirational spec first. Rejected because it would immediately contradict current behavior and break change tracking.

### 14.2 Strict fail-fast over fallback logic

Decision:
- Errors propagate or abort command paths instead of auto-retrying with hidden fallback paths.

Tradeoff:
- Pros: transparent failures, easier debugging, deterministic behavior.
- Cons: less forgiving UX when dependencies are misconfigured.

Rejected alternative:
- Silent fallback between providers or auto-rewriting invalid payloads. Rejected to preserve correctness and observability.

### 14.3 Deterministic audio naming

Decision:
- Audio filenames are deterministic by content hash.

Tradeoff:
- Pros: predictable media naming, dedup-friendly behavior.
- Cons: same text with different intended prosody but identical `(voice, rate, text)` cannot be distinguished by filename.

Rejected alternative:
- Random UUID-based filenames. Rejected because it creates avoidable media duplication.
