"""Refine the knowledge graph by mapping relationships to resolved companies."""

import pyspark.sql.functions as F
from pyspark.sql import SparkSession

from abzu.config import config
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session

logger = get_logger(__name__)


def refine_knowledge_graph(
    input_paths: dict[str, str] = {
        # A hack to persist the iteration parameter in the path
        "companies": config.get("process.kg.refine.input.companies").format(
            format="parquet", iteration="{iteration}"
        ),
        "relationships": config.get("process.kg.refine.input.relationships").format(
            format="parquet", iteration="{iteration}"
        ),
    },
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
    companies_df = spark.read.parquet(input_paths["companies"].format(iteration=iteration))
    print(f"Read total companies: {companies_df.count():,}")

    company_stats_df = companies_df.select(
        "name",
        "id",
        F.substring("uuid", 0, 8).alias("uuid"),
        F.size("source_ids").alias("source_id_count"),
        F.size("source_uuids").alias("source_uuid_count"),
        F.round((F.col("source_uuid_count") / F.col("source_id_count")), 2).alias("id_to_uuid_pct"),
    )
    company_stats_df.show(20, False)

    company_stats_df.select(
        F.round(F.avg(F.col("source_uuid_count") / F.col("source_id_count")), 2).alias(
            "avg_id_to_uuid_pct"
        ),
        F.round(F.median(F.col("source_uuid_count") / F.col("source_id_count")), 2).alias(
            "median_id_to_uuid_pct"
        ),
    ).show()

    relationships_df = spark.read.parquet(input_paths["relationships"].format(iteration=iteration))
    print(f"Read total relationships: {relationships_df.count():,}")
