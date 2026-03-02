-include .env
export

help:
	@echo "Makefile commands:"
	@echo "  run                 - Run the Anki Vocab application"
	@echo "  fmt                 - Format the code using pre-commit"
	@echo "  test                - Run the test suite"
	@echo "  build               - Build the package"
	@echo "  release-testpypi   - Release the package to TestPyPI"
	@echo "  release-pypi       - Release the package to PyPI"
add:
	uv run anki-vocab session
update:
	uv run anki-vocab update
fmt:
	uv run pre-commit run --all-files
test:
	uv run pytest tests
build:
	rm -rf dist/
	uv run python -m build
release-testpypi: build
	uv run python -m twine upload --repository testpypi dist/* --verbose
release-pypi: build
	uv run python -m twine upload dist/* --verbose
