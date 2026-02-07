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
    args: list[str],
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
    iteration: int = 3,
    enrich_wiki: bool = False,
    wiki_batch_size: int = 5,
    wiki_limit: int | None = None,
    use_edge_er: bool = False,
    edge_er_batch_size: int = 5,
    edge_er_min_block_size: int = 2,
) -> int:
    """Refine the knowledge graph by mapping relationships to resolved companies.

    This function calls the refine_knowledge_graph function directly,
    and optionally enriches companies with Wikipedia data.

    Args:
        input_paths: Paths to input data (companies and relationships)
        output_paths: Paths to output data (nodes and edges)
        iteration: ER iteration number to use for resolved companies
        enrich_wiki: Whether to enrich companies with Wikipedia data
        wiki_batch_size: Number of concurrent Wikipedia requests
        wiki_limit: Maximum number of companies to enrich (for testing)
        use_edge_er: Whether to use LLM-based edge resolution
        edge_er_batch_size: Batch size for concurrent edge ER API calls
        edge_er_min_block_size: Minimum edges per (src, dst) pair to trigger edge ER

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
            input_paths=input_paths,
            output_paths=output_paths,
            iteration=iteration,
            use_edge_er=use_edge_er,
            edge_er_batch_size=edge_er_batch_size,
            edge_er_min_block_size=edge_er_min_block_size,
        )
        logger.info("Knowledge graph refinement completed successfully")

        # Optionally enrich with Wikipedia data
        if enrich_wiki:
            logger.info("Enriching companies with Wikipedia data...")
            from abzu.kg.wiki import process_wiki

            # The nodes are saved as JSONL - use that path
            nodes_jsonl = output_paths["nodes"].replace(".parquet", ".jsonl")
            enriched_output = nodes_jsonl.replace(".jsonl", "_enriched.jsonl")

            result = process_wiki(
                companies_path=nodes_jsonl,
                output_path=enriched_output,
                limit=wiki_limit,
                tickers_only=False,  # Enrich all companies, not just those with tickers
                batch_size=wiki_batch_size,
            )
            if result != 0:
                logger.warning("Wikipedia enrichment had issues but continuing")

        return 0

    except Exception as e:
        logger.error(f"Knowledge graph refinement failed: {e}")
        logger.error("\nTroubleshooting steps:")
        logger.error("1. Ensure PySpark is installed: poetry add pyspark")
        logger.error("2. Check if Java is installed: java -version")
        logger.error("3. Ensure you have at least 4GB of RAM available")
        logger.error("4. Check for any network issues if using distributed Spark")
        return 1
