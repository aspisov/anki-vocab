# Changelog

## Unreleased
- Added Typer-based CLI with `session`, `update`, and `config` commands.
- Added config file support, env overrides, and audio overwrite policies.
- Refactored core logic into modules and introduced schema validation.
- Added unit tests for parsing, cleaning, and schema handling.
- Added Rich-powered menu prompts with arrow-key selection.
- Removed overwrite-audio option; audio is added only when missing.
