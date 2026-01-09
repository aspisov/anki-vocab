run:
	uv run anki-card-generator
fmt:
	uv run pre-commit run --all-files
test:
	uv run pytest tests