#!/usr/bin/env python3
"""Refine the knowledge graph by creating bidirectional relationships and a unified edge list."""

from pyspark.sql import SparkSession

from abzu.config import config
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session

logger = get_logger(__name__)


def refine_knowledge_graph(
    input_path: str = config.get("process.kg.refine.input"),
    output_path: str = config.get("process.kg.refine.output"),
    local_mode: bool = True,
) -> None:
    """
    Refine the knowledge graph by creating bidirectional relationships and a unified edge list.

    Args:
        input_path: Path to the raw knowledge graph parquet files
        output_path: Path to save the refined knowledge graph
        local_mode: Whether to run in local mode. Defaults to True.
    """
    # Create SparkSession with appropriate configuration
    spark: SparkSession = get_spark_session(
        app_name="refine_knowledge_graph",
        local_mode=local_mode,
    )
    spark
