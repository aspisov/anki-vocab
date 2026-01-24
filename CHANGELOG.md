# Changelog

## Unreleased
- Added Typer-based CLI with `session`, `update`, and `config` commands.
- Added config file support, env overrides, and audio overwrite policies.
- Refactored core logic into modules and introduced schema validation.
- Added unit tests for parsing, cleaning, and schema handling.
- Added Rich-powered menu prompts with arrow-key selection.
- Removed overwrite-audio option; audio is added only when missing.
- Set max line length to 120 in Ruff configuration.
- Added regeneration feedback flow with prior attempts passed to the model and updated prompt guidance for synonyms and Russian input handling.
- Prefer American English in prompt guidance.
- Removed session `:context` support, cached the system prompt and `.env` loading, kept note lookup stable during regeneration, and cleaned up temp TTS files.
- Renamed the Python package to `anki_vocab` and bumped version to 0.1.3 for TestPyPI.
- Load `.env` in `Makefile` so release tasks can use TestPyPI credentials.
- Update command now prompts for note id, passes current note content to the model, and supports custom update prompts.
- Simplified regeneration to use the same current-card and prompt context as updates, with system prompts rendered via Jinja.
- Added pattern and synonyms fields to cards, with prompt guidance for fixed preposition/particle usage.
- Tightened synonym guidance to require same POS/register and allow "N/A" when uncertain.
- Added target surface, source context, and cloze fields to the card schema and config mapping.
- Added configurable source language to drive prompt behavior for Spanish input.
- Adjusted prompt language rules to be conditional on source language.
- Updated prompt to produce card fields in the source language (non-Russian fields).
- Added a dedicated Spanish system prompt template.
- Renamed internal JSON fields to language-neutral keys (e.g., context/cloze/lemma).
- Update command now only accepts `--note-id`, respects field-map keys for word/context, and keeps note lookup fresh after regenerations.
- `config show` now redacts the OpenAI API key and the CLI avoids prompting for it in non-interactive sessions.
