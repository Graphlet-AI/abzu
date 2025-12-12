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
    print(f"Refined edges count (before deduplication): {refined_edges_df.count():,}")

    # Deduplicate edges by grouping on (src, dst, relationship) and aggregating other fields
    # This prevents duplicate relationships from appearing multiple times when the same
    # relationship is mentioned in multiple articles with different URLs
    edge_agg_exprs = [
        # Keep the first non-null description
        F.first("description", ignorenulls=True).alias("description"),
        # Collect all unique URLs as source references
        F.array_distinct(F.collect_list("url")).alias("urls"),
        # Keep first non-null for scalar fields
        F.first("posted_at", ignorenulls=True).alias("posted_at"),
        F.first("amount", ignorenulls=True).alias("amount"),
        F.first("country", ignorenulls=True).alias("country"),
        F.first("currency", ignorenulls=True).alias("currency"),
        F.first("date", ignorenulls=True).alias("date"),
        F.first("percentage", ignorenulls=True).alias("percentage"),
        F.first("quarter", ignorenulls=True).alias("quarter"),
        # Merge all products and technologies arrays, then deduplicate
        F.array_distinct(F.flatten(F.collect_list("products"))).alias("products"),
        F.array_distinct(F.flatten(F.collect_list("technologies"))).alias("technologies"),
    ]

    refined_edges_df = refined_edges_df.groupBy("src", "dst", "relationship").agg(*edge_agg_exprs)
    print(f"Refined edges count (after deduplication): {refined_edges_df.count():,}")

    # Normalize products and technologies to title case for consistency
    # This turns ["Russell", "russell", "RUSSell"] into ["Russell", "Russell", "Russell"]
    refined_edges_df = refined_edges_df.withColumn(
        "products",
        F.array_distinct(F.transform("products", F.initcap)),
    )
    refined_edges_df = refined_edges_df.withColumn(
        "technologies",
        F.array_distinct(F.transform("technologies", F.initcap)),
    )

    # Save the refined edges
    output_edges_path = output_paths["edges"]
    print(f"Saving edges to: {output_edges_path}")
    refined_edges_df.write.mode("overwrite").parquet(output_edges_path)
    logger.info(f"Refined knowledge graph edges saved to: {output_edges_path}")

    # Also save edges as single JSON file for inspection with jq
    output_edges_json = output_edges_path.replace(".parquet", ".jsonl")
    print(f"Saving edges to JSON: {output_edges_json}")
    refined_edges_df.coalesce(1).write.mode("overwrite").option("ignoreNullFields", "false").json(
        output_edges_json
    )
    logger.info(f"Refined knowledge graph edges (JSON) saved to: {output_edges_json}")

    # Filter out companies with degree zero (no edges)
    connected_src_nodes = refined_edges_df.select("src")
    connected_dst_nodes = refined_edges_df.select(F.col("dst").alias("src"))
    connected_nodes = connected_src_nodes.union(connected_dst_nodes).distinct()

    print(f"Total companies before filtering: {companies_df.count():,}")
    filtered_companies_df = companies_df.join(
        connected_nodes, companies_df.uuid == connected_nodes.src, how="inner"
    ).drop("src")
    print(f"Total companies after filtering (degree > 0): {filtered_companies_df.count():,}")

    # Deduplicate nodes - companies appear in multiple blocks with same UUID
    print(f"Nodes before deduplication: {filtered_companies_df.count():,}")

    # Build aggregation expressions dynamically based on available columns
    # This handles cases where some columns (like cik) may be missing from older data
    available_columns = set(filtered_companies_df.columns)
    agg_exprs = []

    # Scalar fields to aggregate with first()
    scalar_fields = [
        "name",
        "cik",
        "description",
        "ceo",
        "employees",
        "founded_year",
        "headquarters_location",
        "jurisdiction",
        "linkedin_url",
        "revenue_usd",
        "website_url",
        "ticker",
    ]
    for field in scalar_fields:
        if field in available_columns:
            agg_exprs.append(F.first(field, ignorenulls=True).alias(field))

    # Array fields to aggregate with collect_set + flatten
    if "source_uuids" in available_columns:
        agg_exprs.append(
            F.array_distinct(F.flatten(F.collect_set("source_uuids"))).alias("source_uuids")
        )
    if "match_skip_history" in available_columns:
        agg_exprs.append(
            F.array_distinct(F.flatten(F.collect_set("match_skip_history"))).alias(
                "match_skip_history"
            )
        )

    # Boolean field - prefer false (matched) over true (skipped)
    if "match_skip" in available_columns:
        agg_exprs.append(F.min("match_skip").alias("match_skip"))

    deduplicated_nodes_df = filtered_companies_df.groupBy("uuid").agg(*agg_exprs)
    print(f"Nodes after deduplication: {deduplicated_nodes_df.count():,}")

    # Save the deduplicated nodes (companies with edges only)
    output_nodes_path = output_paths["nodes"]
    print(f"Saving nodes to: {output_nodes_path}")
    deduplicated_nodes_df.write.mode("overwrite").parquet(output_nodes_path)
    logger.info(f"Refined knowledge graph nodes saved to: {output_nodes_path}")

    # Also save nodes as single JSON file for inspection with jq
    output_nodes_json = output_nodes_path.replace(".parquet", ".jsonl")
    print(f"Saving nodes to JSON: {output_nodes_json}")
    deduplicated_nodes_df.coalesce(1).write.mode("overwrite").option(
        "ignoreNullFields", "false"
    ).json(output_nodes_json)
    logger.info(f"Refined knowledge graph nodes (JSON) saved to: {output_nodes_json}")
