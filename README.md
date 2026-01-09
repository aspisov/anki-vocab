## anki-card-generator

CLI for generating and maintaining Anki English vocabulary cards from a context sentence and target word, with GPT-5.2 + Edge TTS + AnkiConnect.

### Setup

- Put `OPENAI_API_KEY=...` in `.env` (project root) or export it in your shell.
- Ensure AnkiConnect is running at `http://127.0.0.1:8765`.
- Optional: initialize config with `uv run anki-vocab config init`.

### Run (uv)

- Interactive session (single-line capture):

```bash
uv run anki-vocab session
```
Use `context sentence | word`, `:context ...`, or `:quit`.

- Update an existing card (pick duplicates if needed):

```bash
uv run anki-vocab update --word "gave up" --sentence "I finally gave up smoking last year."
```

- Dry run:

```bash
uv run anki-vocab session --dry-run
```

### Alternative entrypoints

```bash
uv run python -m anki_card_generator
uv run python main.py
```
