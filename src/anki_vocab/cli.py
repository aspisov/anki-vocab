import sys

import typer

from .commands.add import add_card_command
from .commands.config import config_app
from .commands.session import session_command
from .core.config import config_path, resolve_config, update_config_value

app = typer.Typer(
    help="CLI for generating and maintaining Anki vocab cards.",
    invoke_without_command=True,
)
app.add_typer(config_app, name="config")
app.command("add")(add_card_command)


@app.callback()
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return

    config = resolve_config()
    if config.llm_provider == "openai" and not config.openai_api_key:
        if not sys.stdin.isatty():
            typer.echo(
                "OpenAI API key is not set. Use `anki-vocab config set openai_api_key ...` or set ANKI_VOCAB_OPENAI_API_KEY.",
                err=True,
            )
            raise typer.Exit(code=1)
        typer.echo("OpenAI API key is not set.")
        api_key = input("Enter OpenAI API key: ").strip()
        if not api_key:
            raise typer.Exit(code=1)
        update_config_value(config_path(), "openai_api_key", api_key)

    session_command()
