"""CLI commands for configuration management."""

import sys
from typing import Any

import click
import yaml

from abzu.config import config as abzu_config


@click.group()
def config():
    """Manage and inspect Abzu configuration."""
    pass


def format_value_as_yaml(key: str, value: Any) -> str:
    """Format a configuration value as YAML.

    Parameters
    ----------
    key : str
        The configuration key
    value : Any
        The configuration value

    Returns
    -------
    str
        The formatted YAML string
    """
    # Create a dictionary with the key structure
    parts = key.split(".")
    result: dict[str, Any] = {}
    current = result

    # Build nested dictionary structure
    for i, part in enumerate(parts[:-1]):
        current[part] = {}
        current = current[part]

    # Set the final value
    current[parts[-1]] = value

    # Convert to YAML
    yaml_str: str = yaml.dump(result, default_flow_style=False, sort_keys=False)
    return yaml_str.rstrip()


@config.command()
@click.argument("key")
@click.option(
    "--raw",
    "-r",
    is_flag=True,
    help="Output raw value without YAML formatting",
)
def get(key: str, raw: bool) -> None:
    """Get a configuration value by key.

    KEY is a dot-separated path to the configuration value (e.g., 'process.kg.paths.vertices').
    """
    try:
        value = abzu_config.get(key)

        if value is None:
            click.echo(f"Configuration key '{key}' not found", err=True)
            sys.exit(1)

        if raw:
            # Output raw value
            if isinstance(value, (dict, list)):
                # For complex types, still use YAML but without the key structure
                output = yaml.dump(value, default_flow_style=False, sort_keys=False)
                click.echo(output.rstrip())
            else:
                click.echo(value)
        else:
            # Format as YAML with key structure
            output = format_value_as_yaml(key, value)
            click.echo(output)

    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error retrieving configuration: {e}", err=True)
        sys.exit(1)


@config.command(name="list")
@click.option(
    "--depth",
    "-d",
    type=int,
    default=None,
    help="Maximum depth to display (default: all)",
)
def list_keys(depth: int | None) -> None:
    """List all available configuration keys."""
    try:

        def _list_keys_recursive(
            config_dict: dict[str, Any], prefix: str = "", current_depth: int = 0
        ) -> list[str]:
            """Recursively list all keys in the configuration.

            Parameters
            ----------
            config_dict : dict
                The configuration dictionary
            prefix : str
                The current key prefix
            current_depth : int
                The current depth level

            Returns
            -------
            list[str]
                List of all configuration keys
            """
            keys = []

            # Check if we've reached the depth limit
            if depth is not None and current_depth >= depth:
                if config_dict:
                    # Just show that there are more keys
                    keys.append(f"{prefix}...")
                return keys

            for key, value in config_dict.items():
                full_key = f"{prefix}{key}" if prefix else key

                if isinstance(value, dict):
                    # Add the key itself to show it's a section
                    keys.append(f"{full_key}:")
                    # Recursively add sub-keys
                    sub_keys = _list_keys_recursive(value, f"{full_key}.", current_depth + 1)
                    keys.extend(sub_keys)
                else:
                    # Add leaf keys
                    keys.append(full_key)

            return keys

        # Get all configuration as a dict
        all_config = abzu_config._config

        if not all_config:
            click.echo("No configuration loaded", err=True)
            sys.exit(1)

        # List all keys
        all_keys = _list_keys_recursive(all_config)

        if not all_keys:
            click.echo("No configuration keys found")
        else:
            for key in sorted(all_keys):
                click.echo(key)

    except Exception as e:
        click.echo(f"Error listing configuration: {e}", err=True)
        sys.exit(1)


@config.command()
def path():
    """Show the path to the configuration file."""
    click.echo(abzu_config.config_file)


@config.command()
def reload():
    """Reload the configuration file."""
    try:
        abzu_config.reload()
        click.echo("Configuration reloaded successfully")
    except Exception as e:
        click.echo(f"Error reloading configuration: {e}", err=True)
        sys.exit(1)
