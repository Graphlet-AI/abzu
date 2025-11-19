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
            format="json", iteration="{iteration}"
        ),
        "relationships": config.get("process.kg.refine.input.relationships").format(
            format="json", iteration="{iteration}"
        ),
    },
    output_paths: dict[str, str] = {
        "nodes": config.get("process.kg.refine.output.nodes"),
        "edges": config.get("process.kg.refine.output.edges"),
    },
    iteration: int = 3,
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

    # Load the entity resolved companies
    companies_path = input_paths["companies"].format(iteration=iteration, format="json")
    print(f"Loading companies from: {companies_path}")
    companies_df = spark.read.json(companies_path)
    print(f"Read total companies: {companies_df.count():,}")

    company_stats_df = companies_df.select(
        "uuid",
        "name",
        F.size("source_uuids").alias("source_uuid_count"),
        "source_uuids",
    )
    company_stats_df.show(20, False)

    relationships_df = spark.read.parquet(input_paths["relationships"].format(iteration=iteration))
    print(f"Read total relationships: {relationships_df.count():,}")

    # Now flatten the companies source_uuids for joining to the company relationships
    exploded_companies_df = companies_df.select(
        "uuid",
        F.explode("source_uuids").alias("source_uuid"),
    )
    print(f"Exploded companies count: {exploded_companies_df.count():,}")

    # Join relationships to companies on source_uuid to get resolved UUIDs
    src_companies = exploded_companies_df.alias("src_company")
    dst_companies = exploded_companies_df.alias("dst_company")

    refined_edges_df = (
        relationships_df.join(
            src_companies,
            relationships_df.src == src_companies.source_uuid,
            how="inner",
        )
        .withColumnRenamed("uuid", "resolved_src")
        .drop("source_uuid", "src")
        .join(
            dst_companies,
            relationships_df.dst == dst_companies.source_uuid,
            how="inner",
        )
        .withColumnRenamed("uuid", "resolved_dst")
        .drop("source_uuid", "dst")
        .withColumnRenamed("resolved_src", "src")
        .withColumnRenamed("resolved_dst", "dst")
    )

    refined_edges_df.show(20, False)
    print(f"Refined edges count: {refined_edges_df.count():,}")

    # Save the refined edges
    output_edges_path = output_paths["edges"]
    print(f"Saving edges to: {output_edges_path}")
    refined_edges_df.write.mode("overwrite").parquet(output_edges_path)
    logger.info(f"Refined knowledge graph edges saved to: {output_edges_path}")

    # Filter out companies with degree zero (no edges)
    connected_src_nodes = refined_edges_df.select("src").distinct()
    connected_dst_nodes = refined_edges_df.select(F.col("dst").alias("src")).distinct()
    connected_nodes = connected_src_nodes.union(connected_dst_nodes).distinct()

    print(f"Total companies before filtering: {companies_df.count():,}")
    filtered_companies_df = companies_df.join(
        connected_nodes, companies_df.uuid == connected_nodes.src, how="inner"
    ).drop("src")
    print(f"Total companies after filtering (degree > 0): {filtered_companies_df.count():,}")

    # Save the nodes (companies with edges only)
    output_nodes_path = output_paths["nodes"]
    print(f"Saving nodes to: {output_nodes_path}")
    filtered_companies_df.write.mode("overwrite").parquet(output_nodes_path)
    logger.info(f"Refined knowledge graph nodes saved to: {output_nodes_path}")
