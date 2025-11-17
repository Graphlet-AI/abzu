"""Clear zuban and Python cache files."""

import subprocess

import click


@click.command(context_settings={"show_default": True})
def clear() -> None:
    """Clear zuban cache and Python cache files."""
    commands = [
        ("rm -rf .zuban_cache 2>/dev/null", "Removing .zuban_cache directory"),
        (
            'find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null',
            "Removing __pycache__ directories",
        ),
        ('find . -name "*.pyc" -delete', "Removing .pyc files"),
    ]

    for cmd, description in commands:
        click.echo(f"{description}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0 and "2>/dev/null" not in cmd:
            click.echo(f"  Warning: {result.stderr}", err=True)

    click.echo("Cache cleared successfully!")
