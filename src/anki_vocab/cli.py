import typer

from .commands.add import add_card_command
from .commands.config import config_app
from .commands.show import show_card_command
from .commands.update import update_card_command

app = typer.Typer(help="CLI for creating and maintaining Anki vocab cards with TTS audio.")
app.add_typer(config_app, name="config")
app.command("add")(add_card_command)
app.command("show")(show_card_command)
app.command("update")(update_card_command)
