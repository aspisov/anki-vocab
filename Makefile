run:
	uv run anki-vocab
fmt:
	uv run pre-commit run --all-files
test:
	uv run pytest tests
