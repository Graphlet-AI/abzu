"""Refine the knowledge graph by mapping relationships to resolved companies."""

from pyspark.sql import SparkSession

from abzu.config import config
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session

logger = get_logger(__name__)


def refine_knowledge_graph(
    input_paths: dict[str, str] = {"companies": config.get("process.kg.refine.input.companies")},
    output_paths: dict[str, str] = {
        "nodes": config.get("process.kg.refine.output.nodes"),
        "edges": config.get("process.kg.refine.output.edges"),
    },
    iteration: int = 4,
    local_mode: bool = True,
) -> None:
    """
    Refine the knowledge graph by mapping relationships to resolved companies.

    Args:
        input_path: Path to the raw knowledge graph parquet files
        output_path: Path to save the refined knowledge graph
        iteration: ER iteration number to use for resolved companies
        local_mode: Whether to run in local mode. Defaults to True.
    """
    # Create SparkSession with appropriate configuration
    spark: SparkSession = get_spark_session(
        app_name="refine_knowledge_graph",
        local_mode=local_mode,
    )
    companies_df = spark.read.parquet(input_paths["companies"])
    relationships_df = spark.read.parquet(input_paths["relationships"])
    output_paths, iteration, companies_df, relationships_df
