# anki-vocab — an Anki card skill for AI agents

A small CLI that lets an AI agent (Claude Code, Codex, …) create and update **Anki vocabulary cards** with
TTS audio through AnkiConnect. The agent decides the card content — lemma, cloze sentence, Russian gloss,
definition, synonyms, CEFR level and more — and the CLI writes it into Anki deterministically.

`SKILL.md` is the agent-facing instruction file: it defines the 14-field card format and the rules the
agent must follow (cloze-first study sentences, context preserved verbatim, etc.).

## Install as a Claude Code skill

```bash
git clone https://github.com/aspisov/anki-vocab ~/.claude/skills/anki-card-generator
uv sync --project ~/.claude/skills/anki-card-generator
```

Requirements: [uv](https://docs.astral.sh/uv/), Anki desktop with the
[AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on (default URL `http://127.0.0.1:8765`),
network access for [edge-tts](https://github.com/rany2/edge-tts) voices.

Then just ask Claude Code: *"make a card: You will have all the vengeance you seek | vengeance"*.

## Manual usage

```bash
uv run --project ~/.claude/skills/anki-card-generator python -m anki_vocab --help
uv run --project ~/.claude/skills/anki-card-generator python -m anki_vocab show NOTE_ID
uv run --project ~/.claude/skills/anki-card-generator python -m anki_vocab add --lemma ... --target-surface ... # all 14 fields
uv run --project ~/.claude/skills/anki-card-generator python -m anki_vocab update NOTE_ID --lemma ...
uv run --project ~/.claude/skills/anki-card-generator python -m anki_vocab config show   # deck, field map, TTS
```

The deck name and the mapping from card fields to your Anki note type fields live in the config
(`config --help`). The full field reference and workflow are in [`SKILL.md`](SKILL.md).

## License

MIT
