import click

from .app import (
    DEFAULT_DECK_NAME,
    DEFAULT_NOTE_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_VOICE,
    run,
)


@click.command()
@click.option("--sentence", type=str, required=True, help="Context sentence.")
@click.option(
    "--word", type=str, required=True, help="Target word/phrase from the sentence."
)
@click.option("--deck", type=str, default=DEFAULT_DECK_NAME, show_default=True)
@click.option("--note-model", type=str, default=DEFAULT_NOTE_MODEL, show_default=True)
@click.option("--voice", type=str, default=DEFAULT_VOICE, show_default=True)
@click.option("--rate", type=str, default="+0%", show_default=True)
@click.option(
    "--openai-model", type=str, default=DEFAULT_OPENAI_MODEL, show_default=True
)
@click.option("--skip-existing/--no-skip-existing", default=True, show_default=True)
@click.option("--dry-run/--no-dry-run", default=False, show_default=True)
def cli(
    sentence: str,
    word: str,
    deck: str,
    note_model: str,
    voice: str,
    rate: str,
    openai_model: str,
    skip_existing: bool,
    dry_run: bool,
) -> None:
    try:
        run(
            sentence=sentence,
            word=word,
            deck=deck,
            note_model=note_model,
            voice=voice,
            rate=rate,
            openai_model=openai_model,
            skip_existing=skip_existing,
            dry_run=dry_run,
        )
    except ValueError as e:
        raise click.ClickException(str(e)) from e
