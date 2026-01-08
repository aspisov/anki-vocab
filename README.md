## anki-card-generator

CLI that generates an Anki note from **SENTENCE + WORD**, asks **GPT‑5.2** for a strict JSON payload, generates **Edge TTS** audio, and adds the note via **AnkiConnect**.

### Setup

- Put `OPENAI_API_KEY=...` in `.env` (project root) or export it in your shell.
- Ensure AnkiConnect is running at `http://127.0.0.1:8765`.

### Run (uv)

- Dry run (prints the JSON card only):

```bash
uv run anki-card-generator --sentence "I finally gave up smoking last year." --word "gave up" --dry-run
```

- Generate + add to Anki:

```bash
uv run anki-card-generator --sentence "I finally gave up smoking last year." --word "gave up"
```

### Alternative entrypoints

```bash
uv run python -m anki_card_generator --sentence "..." --word "..."
uv run python main.py --sentence "..." --word "..."
```
