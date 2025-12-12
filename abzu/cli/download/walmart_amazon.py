"""CLI for downloading and processing the Walmart-Amazon dataset."""

import tempfile
import zipfile
from pathlib import Path

import click
import pandas as pd
import requests

from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.command(context_settings={"show_default": True})
@click.option(
    "--output-dir",
    "-o",
    default=config.get("download.walmart_amazon.output_dir"),
    type=click.Path(file_okay=False, dir_okay=True),
    help="Output directory for Parquet files",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force re-download even if files exist",
)
def walmart_amazon(output_dir: str, force: bool) -> None:
    """Download and convert Walmart-Amazon dataset to Parquet format.

    Downloads the Dn4.zip dataset from Zenodo (8164151) which contains product
    matching data between Walmart and Amazon. Converts CSV files to Parquet format
    for efficient processing.
    """
    url = "https://zenodo.org/records/8164151/files/Dn4.zip?download=1"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Check if files already exist
    parquet_files = list(output_path.glob("*.parquet"))
    if parquet_files and not force:
        click.echo(f"Found {len(parquet_files)} Parquet files in {output_dir}")
        click.echo("Use --force to re-download")
        return

    click.echo("Downloading Walmart-Amazon dataset from Zenodo...")
    click.echo(f"URL: {url}")
    click.echo()

    try:
        # Download the ZIP file
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "Dn4.zip"

            click.echo("Downloading ZIP file...")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            with open(zip_path, "wb") as f:
                if total_size:
                    with click.progressbar(length=total_size, label="Downloading") as bar:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            bar.update(len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

            click.echo(f"Downloaded to {zip_path}")
            click.echo()

            # Extract ZIP file
            click.echo("Extracting ZIP file...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find all CSV files
            csv_files = list(Path(temp_dir).rglob("*.csv"))
            click.echo(f"Found {len(csv_files)} CSV files")
            click.echo()

            if not csv_files:
                click.echo("✗ No CSV files found in the archive", err=True)
                return

            # Convert each CSV to Parquet
            converted = 0
            for csv_file in csv_files:
                try:
                    click.echo(f"Converting {csv_file.name}...")

                    # Read CSV
                    df = pd.read_csv(csv_file)

                    # Create output filename
                    parquet_name = csv_file.stem + ".parquet"
                    parquet_path = output_path / parquet_name

                    # Save as Parquet
                    df.to_parquet(parquet_path, index=False, engine="pyarrow")

                    # Try to show relative path, fallback to absolute if outside CWD
                    try:
                        display_path = parquet_path.relative_to(Path.cwd())
                    except ValueError:
                        display_path = parquet_path

                    click.echo(f"  ✓ Saved {len(df):,} rows to {display_path}")
                    converted += 1

                except Exception as e:
                    click.echo(f"  ✗ Failed to convert {csv_file.name}: {e}", err=True)

            click.echo()
            click.echo(f"✓ Converted {converted}/{len(csv_files)} files to Parquet")
            click.echo(f"Output directory: {output_path}")

    except requests.exceptions.RequestException as e:
        click.echo(f"✗ Download failed: {e}", err=True)
        raise
    except Exception as e:
        click.echo(f"✗ Processing failed: {e}", err=True)
        raise
