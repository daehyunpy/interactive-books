import typer

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
) -> None:
    if version:
        typer.echo("interactive-books 0.1.0")
        raise typer.Exit()
