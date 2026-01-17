import typer

from .commands.config import (
    config_app,
    config_init,
    config_set,
    config_show,
    config_show_path,
)
from .commands.session import session_command
from .commands.update import update_command
from .commands.utils import select_menu
from .core.config import config_path, resolve_config, update_config_value

app = typer.Typer(
    help="CLI for generating and maintaining Anki vocab cards.",
    invoke_without_command=True,
)
app.command("session")(session_command)
app.command("update")(update_command)
app.add_typer(config_app, name="config")


@app.callback()
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return

    config = resolve_config()
    if not config.openai_api_key:
        typer.echo("OpenAI API key is not set.")
        api_key = input("Enter OpenAI API key: ").strip()
        if not api_key:
            raise typer.Exit(code=1)
        update_config_value(config_path(), "openai_api_key", api_key)

    choice = select_menu(
        "Choose a command",
        ["Session", "Update", "Config", "Quit"],
        hint="Use ↑/↓ and Enter.",
        default_index=0,
    )
    if choice == 0:
        ctx.invoke(session_command)
        return
    if choice == 1:
        ctx.invoke(update_command)
        return
    if choice == 2:
        config_choice = select_menu(
            "Config",
            ["Init", "Show", "Set", "Path", "Back"],
            hint="Use ↑/↓ and Enter.",
            default_index=1,
        )
        if config_choice == 0:
            ctx.invoke(config_init)
        elif config_choice == 1:
            ctx.invoke(config_show)
        elif config_choice == 2:
            key = input("Key (e.g. tts.voice): ").strip()
            value = input("Value: ").strip()
            if key:
                ctx.invoke(config_set, key=key, value=value)
        elif config_choice == 3:
            ctx.invoke(config_show_path)
        return
    raise typer.Exit()


def cli() -> None:
    app()
