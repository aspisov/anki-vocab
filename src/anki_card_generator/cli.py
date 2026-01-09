import typer

from .commands.config import config_app
from .commands.session import session_command
from .commands.update import update_command

app = typer.Typer(help="CLI for generating and maintaining Anki vocab cards.")
app.command("session")(session_command)
app.command("update")(update_command)
app.add_typer(config_app, name="config")


def cli() -> None:
    app()
