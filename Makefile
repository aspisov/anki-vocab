run:
	uv run anki-vocab
fmt:
	uv run pre-commit run --all-files
test:
	uv run pytest tests
build:
	uv run python -m build
release-testpypi: build
	uv run python -m twine upload --repository testpypi dist/*
release-pypi: build
	uv run python -m twine upload dist/*
