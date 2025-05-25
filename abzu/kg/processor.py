"""Process articles into a knowledge graph."""

import importlib.util
import logging
import os
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Check if PySpark is installed
def is_pyspark_installed() -> bool:
    """Check if PySpark is installed.

    Returns:
        True if PySpark is installed, False otherwise
    """
    return importlib.util.find_spec("pyspark") is not None


def run_spark_script(
    script_path: str,
    args: list,
    description: str,
) -> int:
    """Run a PySpark script with the given arguments.

    Args:
        script_path: Path to the PySpark script
        args: List of arguments to pass to the script
        description: Description of the script for logging

    Returns:
        0 on success, 1 on failure
    """
    # Check if PySpark is installed
    if not is_pyspark_installed():
        logger.error("PySpark is not installed. Please install it with poetry:")
        logger.error("  poetry add pyspark")
        return 1

    # Check if the script exists
    if not Path(script_path).exists():
        logger.error(f"Script not found: {script_path}")
        return 1

    # Ensure the script is executable
    Path(script_path).chmod(0o755)

    # Build the command - try to use python directly to avoid path issues
    cmd = [sys.executable, script_path] + args

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
            logger.info(f"{description} completed successfully")
            return 0
        else:
            logger.error(f"{description} failed with exit code {return_code}")

            # Provide more helpful information
            logger.error("\nTroubleshooting steps:")
            logger.error("1. Ensure PySpark is installed: poetry add pyspark")
            logger.error("2. Check if Java is installed: java -version")
            logger.error("3. Try running the script directly: python " + script_path)
            logger.error("4. Ensure you have at least 4GB of RAM available")
            logger.error("5. Check for any network issues if using distributed Spark")

            return return_code

    except Exception as e:
        logger.error(f"Failed to run script: {e}")
        return 1


def process_raw_kg(
    input_file: str = ("data/processed_semianalysis.jsonl,data/processed_theinformation.jsonl"),
    output_dir: str = "data/knowledge_graph",
    partitions: int = 4,
) -> int:
    """Process articles into a raw knowledge graph.

    This function is a wrapper around the abzu/spark/build_graph.py script
    which uses PySpark to build a knowledge graph from the processed articles.

    Args:
        input_file: Comma-separated paths to the input JSONL files with processed articles
        output_dir: Directory to store the knowledge graph
        partitions: Number of Spark partitions to use

    Returns:
        0 on success, 1 on failure
    """
    # Construct the command to run the build_graph.py script
    script_path = str(Path(__file__).parents[1] / "spark" / "build_graph.py")

    # Build the args list
    args = [
        "--input",
        input_file,
        "--output",
        output_dir,
        "--partitions",
        str(partitions),
    ]

    return run_spark_script(script_path, args, "Knowledge graph build")


def process_refine_kg(
    input_dir: str = "data/knowledge_graph",
    output_dir: str = "data/refined_knowledge_graph",
    partitions: int = 4,
) -> int:
    """Refine the knowledge graph by creating bidirectional relationships.

    This function is a wrapper around the abzu/spark/refine_kg.py script
    which uses PySpark to refine the knowledge graph by creating bidirectional
    relationships and a unified edge list.

    Args:
        input_dir: Path to the directory with raw knowledge graph
        output_dir: Directory to store the refined knowledge graph
        partitions: Number of Spark partitions to use

    Returns:
        0 on success, 1 on failure
    """
    # Construct the path to the refine_kg.py script
    script_path = str(Path(__file__).parents[1] / "spark" / "refine_kg.py")

    # Build the args list
    args = [
        "--input",
        input_dir,
        "--output",
        output_dir,
        "--partitions",
        str(partitions),
    ]

    return run_spark_script(script_path, args, "Knowledge graph refinement")
