"""CLI command for displaying pipeline steps."""

import click


@click.command(context_settings={"show_default": True})
def steps():
    """Print the steps required to run the complete data pipeline."""
    from abzu.steps import print_pipeline_steps

    print_pipeline_steps()
    return 0
