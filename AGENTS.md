# Repository Guidelines

## Core Principles

- **KISS over charades.** No elaborate orchestration. Discuss → decide → build.
- **Minimize blast radius.** Prefer many small safe changes over one giant rewrite.
- **Context is expensive.** Read what you need, avoid noisy tooling, avoid pointless docs.
- **Close the loop.** Every change must be verifiable via CLI/tests.
- **Iterate, don’t perfect.** Ship a first version, then refine.

## Build Commands

- I use `uv` for dependency management.
- I use `make` for build orchestration, you can find more helpful commands in the `Makefile`.

## Git

- Use `git` adn `gh` CLI tools for all operations.

## Security & Configuration Tips

- Never commit tokens, client secrets, or `.env` files.

## Core Architecture

### Runtime core (`src/anki_vocab/`)

- `src/anki_vocab/commands/`: contains CLI commands.
- `src/anki_vocab/core/`: contains the core
- `src/anki_vocab/integrations/`: contains AnkiConnect, Edge TTS and OpenAI integrations.

## Important development notes (filled by agent)

- Always run tests after making changes.
- After every atomic change make a commit with a clear message.
- Always log your changes in `CHANGELOG.md`.
