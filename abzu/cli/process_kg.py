"""Process articles into a knowledge graph."""

import importlib.util
import logging
import os
import subprocess
import sys
from pathlib import Path


# Check if PySpark is installed
def is_pyspark_installed():
    return importlib.util.find_spec("pyspark") is not None


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def process_kg_main(  # noqa: C901
    input_file: str = "data/processed_articles.jsonl",
    output_dir: str = "data/knowledge_graph",
    partitions: int = 4,
) -> int:
    """Process articles into a knowledge graph.

    This function is a wrapper around the scripts/build_graph.py script
    which uses PySpark to build a knowledge graph from the processed articles.

    Args:
        input_file: Path to the input JSONL file with processed articles
        output_dir: Directory to store the knowledge graph
        partitions: Number of Spark partitions to use
    """
    # Check if PySpark is installed
    if not is_pyspark_installed():
        logger.error("PySpark is not installed. Please install it with:")
        logger.error("  pip install pyspark")
        logger.error("  or")
        logger.error("  poetry add pyspark")
        return 1

    # Check if the input file exists
    if not Path(input_file).exists():
        logger.error(f"Input file not found: {input_file}")
        return 1

    # Construct the command to run the build_graph.py script
    script_path = str(Path(__file__).parents[2] / "scripts" / "build_graph.py")

    # Ensure the script exists
    if not Path(script_path).exists():
        logger.error(f"Build graph script not found: {script_path}")
        return 1

    # Ensure the script is executable
    Path(script_path).chmod(0o755)

    # Build the command - try to use python directly to avoid path issues
    cmd = [
        sys.executable,  # Use the same Python interpreter
        script_path,
        "--input",
        input_file,
        "--output",
        output_dir,
        "--partitions",
        str(partitions),
    ]

    # Log the command
    logger.info(f"Running command: {' '.join(cmd)}")

    try:
        # Set up environment variables for subprocess
        env = dict(os.environ)

        # Try to find PySpark by getting the poetry environment path
        try:
            poetry_env = subprocess.check_output(
                ["poetry", "env", "info", "-p"], universal_newlines=True
            ).strip()

            # Add poetry environment's site-packages to PYTHONPATH
            site_packages = str(
                Path(poetry_env)
                / "lib"
                / f"python{sys.version_info.major}.{sys.version_info.minor}"
                / "site-packages"
            )

            if "PYTHONPATH" in env:
                env["PYTHONPATH"] = f"{site_packages}:{env['PYTHONPATH']}"
            else:
                env["PYTHONPATH"] = site_packages

            logger.info(f"Using Poetry environment: {poetry_env}")
            logger.info(f"Added to PYTHONPATH: {site_packages}")
        except Exception as e:
            logger.warning(f"Failed to get Poetry environment path: {e}")
            logger.warning("Will use system Python environment")

        # Run the command and capture output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            env=env,
        )

        # Stream output in real-time
        for line in iter(process.stdout.readline, ""):  # type: ignore
            sys.stdout.write(line)
            sys.stdout.flush()

        # Wait for process to complete
        return_code = process.wait()

        if return_code == 0:
            logger.info(f"Knowledge graph successfully built and saved to {output_dir}")
            return 0
        else:
            logger.error(f"Knowledge graph build failed with exit code {return_code}")

            # Provide more helpful information
            logger.error("\nTroubleshooting steps:")
            logger.error("1. Ensure PySpark is installed: pip install pyspark")
            logger.error("2. Check if Java is installed: java -version")
            logger.error("3. Try running the script directly: python scripts/build_graph.py")
            logger.error("4. Ensure you have at least 4GB of RAM available")
            logger.error("5. Check for any network issues if using distributed Spark")

            return return_code

    except Exception as e:
        logger.error(f"Failed to run build_graph.py: {e}")
        return 1


def main() -> int:
    """Command line interface for process_kg."""
    return process_kg_main()


if __name__ == "__main__":
    sys.exit(main())
