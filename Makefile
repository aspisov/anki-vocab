help:
	@echo "Makefile commands:"
	@echo "  run                 - Run the Anki Vocab application"
	@echo "  fmt                 - Format the code using pre-commit"
	@echo "  test                - Run the test suite"
	@echo "  build               - Build the package"
	@echo "  release-testpypi   - Release the package to TestPyPI"
	@echo "  release-pypi       - Release the package to PyPI"
run:
	uv run anki-vocab
fmt:
	uv run pre-commit run --all-files
test:
	uv run pytest tests
build:
	uv run python -m build
release-testpypi: build
	uv run python -m twine upload --repository testpypi dist/* --verbose
release-pypi: build
	uv run python -m twine upload dist/*
