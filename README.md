## anki-card-generator

CLI for generating and maintaining Anki English vocabulary cards from a context sentence and target word, with OpenAI (GPT-5.2) or local Ollama (Gemma) + Edge TTS + AnkiConnect.

### Install (PyPI)

```bash
pipx install anki-vocab 
```

Or:

```bash
pipx install -i https://test.pypi.org/simple/ anki-vocab --pip-args="--extra-index-url
  https://pypi.org/simple" --force
```

### Setup

- If you use OpenAI, put `OPENAI_API_KEY=...` in `.env` (project root) or export it in your shell.
- Or set in config: `uv run anki-vocab config set openai_api_key YOUR_KEY`.
- Ensure AnkiConnect is running at `http://127.0.0.1:8765`.
- Optional: initialize config with `uv run anki-vocab config init`.

### Ollama (local Gemma)

- Ensure Ollama is running locally (default `http://127.0.0.1:11434`).
- Pull your model (example): `ollama pull gemma2:2b`.
- Configure the CLI:

```bash
uv run anki-vocab config set llm_provider ollama
uv run anki-vocab config set ollama_model gemma2:2b
uv run anki-vocab config set ollama_url http://127.0.0.1:11434
```

You can also override per command:

```bash
uv run anki-vocab session --llm-provider ollama --ollama-model gemma2:2b
```

### Run (uv)

- Interactive session (single-line capture):

```bash
uv run anki-vocab session
```
Use `context sentence | word`, `word`, or `:quit`.

- Update existing cards (loops for more note ids):

```bash
uv run anki-vocab update --note-id 123456 --prompt "Refine the definition for academic usage."
```

- Dry run:

```bash
uv run anki-vocab session --dry-run
```

### Alternative entrypoints

```bash
uv run python -m anki_vocab
uv run python main.py
```

### Release (PyPI)

Checklist:

- Bump version in `pyproject.toml`.
- Run `make test`.
- Build: `make build`.
- Upload to TestPyPI and verify install.
- Upload to PyPI.

Commands:

```bash
make build
make release-testpypi
pipx install -i https://test.pypi.org/simple/ anki-vocab
make release-pypi
```
