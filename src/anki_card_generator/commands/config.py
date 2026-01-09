import json

import typer

from ..core.config import (
    config_as_dict,
    config_path,
    resolve_config,
    update_config_value,
    write_default_config,
)


config_app = typer.Typer(help="Manage configuration.")


@config_app.command("init")
def config_init(force: bool = typer.Option(False, "--force", help="Overwrite config.")) -> None:
    path = config_path()
    if path.exists() and not force:
        raise typer.BadParameter("Config file already exists. Use --force to overwrite.")
    write_default_config(path)
    typer.echo(f"Created config at {path}", err=True)


@config_app.command("show")
def config_show() -> None:
    config = resolve_config()
    typer.echo(json.dumps(config_as_dict(config), indent=2, sort_keys=True))


@config_app.command("set")
def config_set(key: str, value: str) -> None:
    update_config_value(config_path(), key, value)
    typer.echo("Config updated.", err=True)


@config_app.command("path")
def config_show_path() -> None:
    typer.echo(str(config_path()))
