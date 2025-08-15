#!/usr/bin/env python3
"""Build a knowledge graph from pre-processed articles."""
from typing import Optional

from pyspark.sql import SparkSession

from abzu.config import config
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session

logger = get_logger(__name__)


def build_knowledge_graph(
    input_path: list[str] = config.get("process.kg.raw.input"),
    output_path: str = config.get("process.kg.raw.output"),
    local_mode: Optional[bool] = None,
) -> None:
    """
    Build a knowledge graph from pre-processed articles.

    Args:
        input_path: Path(s) to the input JSON files
        output_path: Path to save the output parquet files
        local_mode: Whether to run in local mode. If None, will be determined by environment
    """
    # Create SparkSession with appropriate configuration
    spark: SparkSession = get_spark_session(
        app_name="build_graph",
        local_mode=local_mode,
    )
    # TODO: Implement knowledge graph building logic
    _ = spark  # Placeholder to mark spark as used
