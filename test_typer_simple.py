"""Test simple para debuggear Typer"""
import typer
from typing import Optional

app = typer.Typer()

@app.command()
def test_cmd(
    arg1: str = typer.Argument(...),
    arg2: str = typer.Argument(...),
    arg3: int = typer.Argument(...),
):
    """Test simple con Argument."""
    typer.echo(f"arg1: {arg1}")
    typer.echo(f"arg2: {arg2}")
    typer.echo(f"arg3: {arg3}")

if __name__ == "__main__":
    app()
