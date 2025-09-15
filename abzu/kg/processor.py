"""Process articles into a knowledge graph."""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

from abzu.config import config
from abzu.logs import get_logger
from abzu.spark.build_graph import build_knowledge_graph
from abzu.spark.refine_kg import refine_knowledge_graph

logger = get_logger(__name__)


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
    input_file: list[str] = config.get("process.kg.raw.input"),
    output_dir: str = config.get("process.kg.raw.output"),
) -> int:
    """Process articles into a raw knowledge graph.

    This function calls the build_knowledge_graph function directly.

    Args:
        input_file: List of paths to the input JSONL files with processed articles
        output_dir: Directory to store the knowledge graph

    Returns:
        0 on success, 1 on failure
    """
    # Check if PySpark is installed
    if not is_pyspark_installed():
        logger.error("PySpark is not installed. Please install it with poetry:")
        logger.error("  poetry add pyspark")
        return 1

    try:
        logger.info("Building knowledge graph...")
        build_knowledge_graph(input_file, output_dir)
        logger.info("Knowledge graph build completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Knowledge graph build failed: {e}")
        logger.error("\nTroubleshooting steps:")
        logger.error("1. Ensure PySpark is installed: poetry add pyspark")
        logger.error("2. Check if Java is installed: java -version")
        logger.error("3. Ensure you have at least 4GB of RAM available")
        logger.error("4. Check for any network issues if using distributed Spark")
        return 1


def process_refine_kg(
    input_paths: dict[str, str] = {
        "companies": config.get("process.kg.refine.input.companies"),
        "relationships": config.get("process.kg.refine.input.relationships"),
    },
    output_paths: dict[str, str] = {
        "nodes": config.get("process.kg.refine.output.nodes"),
        "edges": config.get("process.kg.refine.output.edges"),
    },
    iteration: int = 4,
) -> int:
    """Refine the knowledge graph by mapping relationships to resolved companies.

    This function calls the refine_knowledge_graph function directly.

    Args:
        input_dir: Path to the directory with raw knowledge graph
        output_dir: Directory to store the refined knowledge graph
        iteration: ER iteration number to use for resolved companies

    Returns:
        0 on success, 1 on failure
    """
    # Check if PySpark is installed
    if not is_pyspark_installed():
        logger.error("PySpark is not installed. Please install it with poetry:")
        logger.error("  poetry add pyspark")
        return 1

    try:
        logger.info(f"Refining knowledge graph using ER iteration {iteration}...")
        refine_knowledge_graph(
            input_paths=input_paths, output_paths=output_paths, iteration=iteration
        )
        logger.info("Knowledge graph refinement completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Knowledge graph refinement failed: {e}")
        logger.error("\nTroubleshooting steps:")
        logger.error("1. Ensure PySpark is installed: poetry add pyspark")
        logger.error("2. Check if Java is installed: java -version")
        logger.error("3. Ensure you have at least 4GB of RAM available")
        logger.error("4. Check for any network issues if using distributed Spark")
        return 1
