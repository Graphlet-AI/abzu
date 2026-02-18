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
    use_edge_er: bool = False,
    edge_er_batch_size: int = 5,
    edge_er_min_block_size: int = 2,
) -> None:
    """
    Refine the knowledge graph by mapping relationships to resolved companies.

    Args:
        input_paths: Paths to input data (companies and relationships)
        output_paths: Paths to output data (nodes and edges)
        iteration: ER iteration number to use for resolved companies
        local_mode: Whether to run in local mode. Defaults to True.
        use_edge_er: Whether to use LLM-based edge resolution instead of simple dedup.
        edge_er_batch_size: Batch size for concurrent edge ER API calls.
        edge_er_min_block_size: Minimum edges per (src, dst) pair to trigger edge ER.
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

    if use_edge_er:
        # LLM-based edge resolution: merge duplicate relationships using BAML
        logger.info("Using LLM-based edge resolution...")

        # Add company names for LLM context
        uuid_name_df = companies_df.select(
            F.col("uuid").alias("_uuid"),
            F.col("name").alias("_name"),
        )

        edges_with_names = (
            refined_edges_df.join(uuid_name_df, F.col("src") == F.col("_uuid"), how="left")
            .withColumn("src_name", F.col("_name"))
            .drop("_uuid", "_name")
        )
        edges_with_names = (
            edges_with_names.join(uuid_name_df, F.col("dst") == F.col("_uuid"), how="left")
            .withColumn("dst_name", F.col("_name"))
            .drop("_uuid", "_name")
        )

        # Group by (src, dst) to form edge blocks
        edge_blocks_df = edges_with_names.groupBy("src", "dst").agg(
            F.first("src_name").alias("src_name"),
            F.first("dst_name").alias("dst_name"),
            F.collect_list(
                F.struct(
                    "relationship",
                    "description",
                    "amount",
                    "currency",
                    "date",
                    "percentage",
                    "quarter",
                    "url",
                )
            ).alias("relationships"),
            F.count("*").alias("block_size"),
            F.first("posted_at", ignorenulls=True).alias("posted_at"),
            F.first("country", ignorenulls=True).alias("country"),
            F.array_distinct(F.flatten(F.collect_list("products"))).alias("products"),
            F.array_distinct(F.flatten(F.collect_list("technologies"))).alias("technologies"),
            F.array_distinct(F.collect_list("url")).alias("urls"),
        )

        total_blocks = edge_blocks_df.count()
        multi_blocks_df = edge_blocks_df.filter(F.col("block_size") >= edge_er_min_block_size)
        single_blocks_df = edge_blocks_df.filter(F.col("block_size") < edge_er_min_block_size)
        multi_count = multi_blocks_df.count()
        single_count = single_blocks_df.count()

        print(f"Edge blocks total: {total_blocks:,}")
        print(f"  Multi-edge blocks (>= {edge_er_min_block_size}): {multi_count:,}")
        print(f"  Single-edge blocks: {single_count:,}")

        all_edge_rows: list[dict] = []

        # Process multi-edge blocks through BAML
        if multi_count > 0:
            from abzu.er.edge_match import run_edge_resolution

            blocks_data = [row.asDict(recursive=True) for row in multi_blocks_df.collect()]
            resolved = run_edge_resolution(blocks_data, edge_er_batch_size)

            total_original = sum(r.get("original_count", 0) for r in resolved)
            total_merged = sum(r.get("resolved_count", 0) for r in resolved)
            print(
                f"Edge ER: {total_original:,} relationships -> {total_merged:,} "
                f"({total_original - total_merged:,} merged)"
            )

            for result in resolved:
                orig_block = next(
                    (
                        b
                        for b in blocks_data
                        if b["src"] == result["src"] and b["dst"] == result["dst"]
                    ),
                    {},
                )
                for merged_rel in result.get("merged_relationships", []):
                    all_edge_rows.append(
                        {
                            "src": result["src"],
                            "dst": result["dst"],
                            "relationship": merged_rel.get("relationship", "Unknown"),
                            "description": merged_rel.get("description", ""),
                            "urls": result.get("urls", []),
                            "posted_at": orig_block.get("posted_at"),
                            "amount": merged_rel.get("amount"),
                            "country": orig_block.get("country"),
                            "currency": merged_rel.get("currency"),
                            "date": merged_rel.get("date"),
                            "percentage": merged_rel.get("percentage"),
                            "quarter": merged_rel.get("quarter"),
                            "products": orig_block.get("products", []),
                            "technologies": orig_block.get("technologies", []),
                        }
                    )

        # Flatten single-edge blocks (no BAML needed)
        if single_count > 0:
            for row in single_blocks_df.collect():
                row_dict = row.asDict(recursive=True)
                for rel in row_dict.get("relationships", []):
                    all_edge_rows.append(
                        {
                            "src": row_dict["src"],
                            "dst": row_dict["dst"],
                            "relationship": rel.get("relationship", "Unknown"),
                            "description": rel.get("description", ""),
                            "urls": row_dict.get("urls", []),
                            "posted_at": row_dict.get("posted_at"),
                            "amount": rel.get("amount"),
                            "country": row_dict.get("country"),
                            "currency": rel.get("currency"),
                            "date": rel.get("date"),
                            "percentage": rel.get("percentage"),
                            "quarter": rel.get("quarter"),
                            "products": row_dict.get("products", []),
                            "technologies": row_dict.get("technologies", []),
                        }
                    )

        import pandas as pd

        if all_edge_rows:
            refined_edges_pd = pd.DataFrame(all_edge_rows)
            refined_edges_df = spark.createDataFrame(refined_edges_pd)
        else:
            logger.warning("No edges after edge resolution!")
            return

        print(f"Refined edges count (after edge ER): {refined_edges_df.count():,}")
    else:
        # Simple groupBy deduplication (no LLM)
        edge_agg_exprs = [
            F.first("description", ignorenulls=True).alias("description"),
            F.array_distinct(F.collect_list("url")).alias("urls"),
            F.first("posted_at", ignorenulls=True).alias("posted_at"),
            F.first("amount", ignorenulls=True).alias("amount"),
            F.first("country", ignorenulls=True).alias("country"),
            F.first("currency", ignorenulls=True).alias("currency"),
            F.first("date", ignorenulls=True).alias("date"),
            F.first("percentage", ignorenulls=True).alias("percentage"),
            F.first("quarter", ignorenulls=True).alias("quarter"),
            F.array_distinct(F.flatten(F.collect_list("products"))).alias("products"),
            F.array_distinct(F.flatten(F.collect_list("technologies"))).alias("technologies"),
        ]

        refined_edges_df = refined_edges_df.groupBy("src", "dst", "relationship").agg(
            *edge_agg_exprs
        )
        print(f"Refined edges count (after deduplication): {refined_edges_df.count():,}")

    # Normalize products and technologies for consistency
    # Strategy: Preserve all-uppercase terms (likely acronyms like IBM, AWS, API)
    # and use title case for everything else
    # Examples:
    #   - "IBM", "ibm", "Ibm" -> "IBM" (all-uppercase preserved)
    #   - "Russell", "russell", "RUSSell" -> "Russell" (title case)
    #   - "API", "api" -> "API" (all-uppercase preserved)
    # Note: This doesn't handle mixed-case brand names like "iPhone" or "PostgreSQL"
    # which would become "Iphone" and "Postgresql". A more sophisticated solution
    # would require a dictionary of known terms.
    refined_edges_df = refined_edges_df.withColumn(
        "products",
        F.array_distinct(
            F.transform(
                "products",
                lambda x: F.when((F.upper(x) == x) & (F.length(x) > 1), F.upper(x)).otherwise(
                    F.initcap(x)
                ),
            )
        ),
    )
    refined_edges_df = refined_edges_df.withColumn(
        "technologies",
        F.array_distinct(
            F.transform(
                "technologies",
                lambda x: F.when((F.upper(x) == x) & (F.length(x) > 1), F.upper(x)).otherwise(
                    F.initcap(x)
                ),
            )
        ),
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
