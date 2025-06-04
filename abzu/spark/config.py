"""Spark configuration module for Abzu."""

import os
from typing import Optional

from pyspark.sql import SparkSession


def get_spark_session(
    app_name: str,
    local_mode: Optional[bool] = None,
    driver_memory: str = "4g",
    executor_memory: str = "2g",
) -> SparkSession:
    """
    Create a SparkSession with appropriate configuration for local or distributed mode.

    Args:
        app_name: Name of the Spark application
        local_mode: Whether to run in local mode. If None, will be determined by environment
        driver_memory: Memory for driver in local mode
        executor_memory: Memory for executor in local mode

    Returns:
        Configured SparkSession
    """
    # Determine if we should use local mode
    if local_mode is None:
        # Check if we're running in Docker with distributed setup
        spark_master: Optional[str] = os.getenv("SPARK_MASTER")
        local_mode = not (spark_master is not None and spark_master.startswith("spark://"))

    # Start building the SparkSession
    builder = SparkSession.builder.appName(app_name)

    # Common configurations for both modes
    builder = builder.config("spark.sql.execution.arrow.pyspark.enabled", "true").config(
        "spark.sql.caseSensitive", "true"
    )

    if local_mode:
        # Local mode configuration
        builder = (
            builder.config("spark.driver.memory", driver_memory)
            .config("spark.executor.memory", executor_memory)
            .master("local[*]")  # Use all available cores
        )
    else:
        # Distributed mode configuration
        builder = (
            builder.config("spark.driver.memory", driver_memory)
            .config("spark.executor.memory", executor_memory)
            .config("spark.dynamicAllocation.enabled", "true")
            .config("spark.shuffle.service.enabled", "true")
            .config("spark.dynamicAllocation.minExecutors", "1")
            .config("spark.dynamicAllocation.maxExecutors", "10")
            .config("spark.dynamicAllocation.initialExecutors", "2")
            .master(os.getenv("SPARK_MASTER", "spark://spark-master:7077"))
        )

    return builder.getOrCreate()
