#!/usr/bin/env python3
"""Entity resolution blocking strategies for company matching."""
import logging
import os
from typing import Any, Optional

import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.sql import DataFrame, SparkSession

from abzu.config import config
from abzu.er.acronyms import get_acronyms
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session
from abzu.spark.schemas import (
    get_company_fields_without_blocks,
    normalize_company_dataframe,
)

logger = get_logger(__name__)

MAX_BLOCK_SIZE = config.get("process.kg.er.max_block_size", 50)


@F.udf(T.StringType())
def get_first_word(name: str) -> str | None:
    """Extract first word if it's at least 1 character, removing domain suffixes."""
    if not name or not name.strip():
        return "UNKNOWN"  # Fallback for empty names
    # Remove domain suffix (everything after and including first ".")
    name_without_suffix = name.split(".")[0].strip()
    words = name_without_suffix.split()
    return words[0].upper() if words else "UNKNOWN"


@F.udf(T.StringType())
def get_acronym(name: str) -> str | None:
    """Generate acronyms from company names, fallback to first word if no acronym."""
    if not name or not name.strip():
        return "UNKNOWN"  # Fallback for empty names
    # Remove domain suffix (everything after and including first ".")
    name_without_suffix = name.split(".")[0].strip()
    acronym = get_acronyms(name_without_suffix)
    if acronym:
        return acronym
    # Fallback to first word if no acronym can be generated
    words = name_without_suffix.split()
    return words[0].upper() if words else "UNKNOWN"


def build_blocks(
    input_path: str = config.get("process.kg.er.paths.input"),
    output_path: str = config.get("process.kg.er.paths.names.blocks_dir"),
    local_mode: Optional[bool] = None,
    stop_spark: bool = True,
    max_block_size: Optional[int] = None,
) -> None:
    """
    Analyze company blocking strategies by computing size distributions.

    Args:
        input_path: Path to the input companies parquet
        output_path: Path to save the output blocks
        local_mode: Whether to run in local mode. If None, will be determined by environment
        stop_spark: Whether to stop the Spark session after processing
        max_block_size: Maximum block size (blocks larger than this will be chunked). If None, uses config value
    """
    # Use provided max_block_size or fall back to config
    if max_block_size:
        logger.info(f"Using provided max block size of {max_block_size}")
        actual_max_block_size = max_block_size
    else:
        logger.info(f"Using default max block size of {MAX_BLOCK_SIZE}")
        actual_max_block_size = MAX_BLOCK_SIZE

    # If output_path has {format} placeholder, remove it (this should be a directory)
    if "{format}" in output_path:
        # Extract the directory path by removing the filename part with {format}
        raise ValueError(
            "There is an unsubstituted {format} in the output path. Remove {format} from the path."
        )

    # Check if input file exists
    if not os.path.exists(input_path):
        error_msg = (
            f"Companies file not found: {input_path}\n\n"
            f"The blocking step requires company data.\n"
            f"For iteration 1, please ensure you have run the KG raw processing step:\n"
            f"  abzu process kg raw\n\n"
            f"For iteration 2+, the previous iteration's resolved companies are used.\n"
            f"Please ensure the previous iteration completed successfully."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Create SparkSession with appropriate configuration
    spark: SparkSession = get_spark_session(
        app_name="build_er_blocks",
        local_mode=local_mode,
    )

    # Load companies (always in regular format after UUID resolution)
    logger.info(f"Loading companies from {input_path}")
    companies_df_raw: DataFrame = spark.read.json(input_path)

    # Normalize schema to ensure consistency across iterations
    logger.info("Normalizing company schema to match BAML definition...")
    companies_df = normalize_company_dataframe(companies_df_raw, preserve_extra_fields=False)

    total_companies = companies_df.count()
    logger.info(f"Loaded and normalized {total_companies:,} companies")

    # Show sample of the data
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Sample companies:")
        companies_df.show(5, truncate=False)

    # Apply blocking strategies
    logger.info("Computing blocking keys...")
    companies_with_block_keys_df = companies_df.select(
        "uuid",
        "name",
        get_first_word(F.col("name")).alias("first_word_block"),
        get_acronym(F.col("name")).alias("acronym_block"),
    )

    # Separate companies with UNKNOWN block keys
    companies_with_unknown_keys = companies_with_block_keys_df.filter(
        (F.col("first_word_block") == "UNKNOWN") & (F.col("acronym_block") == "UNKNOWN")  # type: ignore[call-arg]
    )

    unknown_count = companies_with_unknown_keys.count()
    if unknown_count > 0:
        logger.warning(
            f"Found {unknown_count} companies with UNKNOWN block keys - will create an UNBLOCKED block for them"
        )

    # For analysis, only use companies with valid block keys
    companies_with_valid_keys_df = companies_with_block_keys_df.filter(
        (F.col("first_word_block") != "UNKNOWN") | (F.col("acronym_block") != "UNKNOWN")  # type: ignore[call-arg]
    )

    # Continue with valid keys for analysis
    companies_with_block_keys_df = companies_with_valid_keys_df

    # Cache for multiple operations
    companies_with_block_keys_df = companies_with_block_keys_df.cache()

    # Show sample with blocking keys
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Sample companies with blocking keys:")
        companies_with_block_keys_df.show(10, truncate=False)

    # Compute first word blocking distribution
    logger.info("Computing first word blocking distribution...")
    first_word_dist_df = (
        companies_with_block_keys_df.filter(
            F.col("first_word_block").isNotNull() & (F.col("first_word_block") != "UNKNOWN")  # type: ignore
        )
        .groupBy("first_word_block")
        .agg(F.count("*").alias("block_size"))
        .orderBy(F.desc("block_size"))
    )

    first_word_blocks = first_word_dist_df.count()
    first_word_companies = companies_with_block_keys_df.filter(
        F.col("first_word_block").isNotNull()  # type: ignore[call-arg]
    ).count()

    logger.info(
        f"First word blocking: {first_word_blocks:,} blocks covering {first_word_companies:,} companies"
    )
    logger.info("Top 20 first word blocks:")
    first_word_dist_df.show(20, truncate=False)

    # Create histogram bins for first word block sizes
    logger.info("First word block size distribution histogram:")
    first_word_histogram_df = (
        first_word_dist_df.select(
            F.when(F.col("block_size") == 1, "1")
            .when(F.col("block_size") <= 5, "2-5")  # type: ignore
            .when(F.col("block_size") <= 10, "6-10")  # type: ignore
            .when(F.col("block_size") <= 20, "11-20")  # type: ignore
            .when(F.col("block_size") <= 50, "21-50")  # type: ignore
            .when(F.col("block_size") <= 100, "51-100")  # type: ignore
            .otherwise("100+")
            .alias("block_size_range"),
            F.col("block_size"),
        )
        .groupBy("block_size_range")
        .agg(F.count("*").alias("num_blocks"), F.sum("block_size").alias("companies_in_range"))
        .orderBy(
            F.when(F.col("block_size_range") == "1", 1)
            .when(F.col("block_size_range") == "2-5", 2)
            .when(F.col("block_size_range") == "6-10", 3)
            .when(F.col("block_size_range") == "11-20", 4)
            .when(F.col("block_size_range") == "21-50", 5)
            .when(F.col("block_size_range") == "51-100", 6)
            .otherwise(7)
        )
    )
    first_word_histogram_df.show(truncate=False)

    # Compute acronym blocking distribution
    logger.info("Computing acronym blocking distribution...")
    acronym_dist_df = (
        companies_with_block_keys_df.filter(
            F.col("acronym_block").isNotNull() & (F.col("acronym_block") != "UNKNOWN")  # type: ignore
        )
        .groupBy("acronym_block")
        .agg(F.count("*").alias("block_size"))
        .orderBy(F.desc("block_size"))
    )

    acronym_blocks = acronym_dist_df.count()
    acronym_companies = companies_with_block_keys_df.filter(
        F.col("acronym_block").isNotNull()  # type: ignore[call-arg]
    ).count()

    logger.info(
        f"Acronym blocking: {acronym_blocks:,} blocks covering {acronym_companies:,} companies"
    )
    logger.info("Top 20 acronym blocks:")
    acronym_dist_df.show(20, truncate=False)

    # Create histogram bins for acronym block sizes
    logger.info("Acronym block size distribution histogram:")
    acronym_histogram_df = (
        acronym_dist_df.select(
            F.when(F.col("block_size") == 1, "1")
            .when(F.col("block_size") <= 5, "2-5")  # type: ignore
            .when(F.col("block_size") <= 10, "6-10")  # type: ignore
            .when(F.col("block_size") <= 20, "11-20")  # type: ignore
            .when(F.col("block_size") <= 50, "21-50")  # type: ignore
            .when(F.col("block_size") <= 100, "51-100")  # type: ignore
            .otherwise("100+")
            .alias("block_size_range"),
            F.col("block_size"),
        )
        .groupBy("block_size_range")
        .agg(F.count("*").alias("num_blocks"), F.sum("block_size").alias("companies_in_range"))
        .orderBy(
            F.when(F.col("block_size_range") == "1", 1)
            .when(F.col("block_size_range") == "2-5", 2)
            .when(F.col("block_size_range") == "6-10", 3)
            .when(F.col("block_size_range") == "11-20", 4)
            .when(F.col("block_size_range") == "21-50", 5)
            .when(F.col("block_size_range") == "51-100", 6)
            .otherwise(7)
        )
    )
    acronym_histogram_df.show(truncate=False)

    # Print summary statistics
    logger.info("\n" + "=" * 60)
    logger.info("BLOCKING STRATEGY SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total companies: {total_companies:,}")
    logger.info("")
    logger.info("First Word Blocking:")
    logger.info(f"  - Blocks created: {first_word_blocks:,}")
    logger.info(
        f"  - Companies covered: {first_word_companies:,} ({first_word_companies / total_companies * 100:.1f}%)"
    )
    logger.info("")
    logger.info("Acronym Blocking:")
    logger.info(f"  - Blocks created: {acronym_blocks:,}")
    logger.info(
        f"  - Companies covered: {acronym_companies:,} ({acronym_companies / total_companies * 100:.1f}%)"
    )
    logger.info("=" * 60)

    # Keep ALL blocks (including single-record blocks)
    logger.info("Processing all blocks (including single-record blocks)...")

    # Get all first word blocks (including size = 1)
    first_word_multi_blocks = first_word_dist_df.select("first_word_block")

    # Get all acronym blocks (including size = 1)
    acronym_multi_blocks = acronym_dist_df.select("acronym_block")

    # Filter companies to only include those in multi-company blocks
    first_word_companies_filtered = companies_with_block_keys_df.join(
        first_word_multi_blocks,
        "first_word_block",
        "inner",
    ).select(
        "uuid",
        F.col("first_word_block").alias("block_key"),
        F.lit("first_word").alias("block_key_type"),
    )

    acronym_companies_filtered = companies_with_block_keys_df.join(
        acronym_multi_blocks,
        "acronym_block",
        "inner",
    ).select(
        "uuid",
        F.col("acronym_block").alias("block_key"),
        F.lit("acronym").alias("block_key_type"),
    )

    first_word_filtered_count = first_word_companies_filtered.count()
    acronym_filtered_count = acronym_companies_filtered.count()

    logger.info(f"First word blocks: {first_word_filtered_count:,} companies")
    logger.info(f"Acronym blocks: {acronym_filtered_count:,} companies")

    # Get complete company records and group by blocking keys
    logger.info("Grouping complete company records by blocking keys...")

    # Join filtered companies back with full company data
    full_companies_df_raw = spark.read.json(input_path)
    # Normalize again to ensure consistency
    full_companies_df = normalize_company_dataframe(
        full_companies_df_raw, preserve_extra_fields=False
    )

    # Identify overlapping block_keys between first_word and acronym strategies
    logger.info("Identifying overlapping block_keys for merging...")

    # Union first_word and acronym companies
    all_companies_with_blocks = first_word_companies_filtered.union(acronym_companies_filtered)

    # Find overlapping block_keys by counting distinct block_key_types per block_key
    overlapping_keys = (
        all_companies_with_blocks.groupBy("block_key")
        .agg(F.countDistinct("block_key_type").alias("strategy_count"))
        .filter(F.col("strategy_count") > 1)  # type: ignore
        .select("block_key")
    )

    overlapping_count = overlapping_keys.count()
    logger.info(f"Found {overlapping_count:,} overlapping block_keys between strategies")

    # Create combined blocks for overlapping keys
    combined_blocks_temp = (
        all_companies_with_blocks.join(
            overlapping_keys, "block_key", "inner"
        )  # Only overlapping keys
        .dropDuplicates(["block_key", "uuid"])  # Remove duplicate UUIDs within each block
        .join(full_companies_df, "uuid", "inner")
    )

    # Get company fields without block-related fields
    company_fields = get_company_fields_without_blocks()

    # Create struct with all company fields, using null for missing fields
    # This ensures the struct matches the UDTF return type schema exactly
    company_struct = F.struct(
        *[
            F.col(f) if f in combined_blocks_temp.columns else F.lit(None).alias(f)
            for f in company_fields
        ]
    )

    combined_blocks = (
        combined_blocks_temp.groupBy("block_key")
        .agg(
            F.collect_list(company_struct).alias("companies"),
            F.countDistinct("uuid").alias("block_size"),
        )
        .withColumn("block_key_type", F.lit("combined"))
        .select("block_key", "block_key_type", "companies", "block_size")
    )

    # Show top 20 overlapping block_keys by company count
    logger.info("Top 20 overlapping block_keys by company count:")
    combined_blocks.select("block_key", "block_size").orderBy(F.desc("block_size")).show(
        20, truncate=False
    )

    # Create separate blocks for non-overlapping keys
    first_word_blocks_temp = (
        all_companies_with_blocks.join(
            overlapping_keys, "block_key", "left_anti"
        )  # Exclude overlapping keys
        .filter(F.col("block_key_type") == "first_word")
        .dropDuplicates(["block_key", "uuid"])  # Remove any duplicate UUIDs
        .join(full_companies_df, "uuid", "inner")
    )

    # Create struct with only company fields (reuse from above)
    company_struct_first = F.struct(
        *[F.col(f) for f in company_fields if f in first_word_blocks_temp.columns]
    )

    first_word_only_blocks = first_word_blocks_temp.groupBy("block_key", "block_key_type").agg(
        F.collect_list(company_struct_first).alias("companies"),
        F.countDistinct("uuid").alias("block_size"),
    )

    acronym_blocks_temp = (
        all_companies_with_blocks.join(
            overlapping_keys, "block_key", "left_anti"
        )  # Exclude overlapping keys
        .filter(F.col("block_key_type") == "acronym")
        .dropDuplicates(["block_key", "uuid"])  # Remove any duplicate UUIDs
        .join(full_companies_df, "uuid", "inner")
    )

    # Create struct with only company fields (reuse from above)
    company_struct_acronym = F.struct(
        *[F.col(f) for f in company_fields if f in acronym_blocks_temp.columns]
    )

    acronym_only_blocks = acronym_blocks_temp.groupBy("block_key", "block_key_type").agg(
        F.collect_list(company_struct_acronym).alias("companies"),
        F.countDistinct("uuid").alias("block_size"),
    )

    if logger.isEnabledFor(logging.DEBUG):
        acronym_only_blocks.printSchema()

    # Split large blocks (> 50 companies) into smaller chunks
    logger.info(
        f"Splitting large blocks (> {actual_max_block_size} companies) into smaller chunks..."
    )

    # Build the UDTF returnType dynamically from the actual DataFrame schema
    # Get the companies array element type from the first non-empty block
    from pyspark.sql.types import ArrayType

    companies_field = combined_blocks.schema["companies"]
    companies_array_type = companies_field.dataType
    assert isinstance(companies_array_type, ArrayType), "companies must be an ArrayType"
    companies_schema = companies_array_type.elementType.simpleString()
    udtf_return_type = (
        f"block_key: string, block_key_type: string, "
        f"companies: array<{companies_schema}>, "
        f"block_size: long"
    )
    logger.debug(f"UDTF return type: {udtf_return_type}")

    @F.udtf(returnType=udtf_return_type)  # type: ignore
    class SplitLargeBlocks:
        def eval(
            self,
            block_key: str,
            block_key_type: str,
            companies: list[dict[str, Any]],
            block_size: int,
        ):  # type: ignore
            if block_size <= actual_max_block_size:
                yield (block_key, block_key_type, companies, block_size)
            else:
                chunk_num = 1
                for i in range(0, len(companies), actual_max_block_size):
                    chunk_companies = companies[i : i + actual_max_block_size]
                    chunk_key = f"{block_key}_chunk_{chunk_num}"
                    yield (chunk_key, block_key_type, chunk_companies, len(chunk_companies))
                    chunk_num += 1

    # 2) Register the UDTF for SQL use
    spark.udtf.register("split_large_blocks", SplitLargeBlocks)  # type: ignore

    # 3) Create temp views for the DataFrames
    combined_blocks.createOrReplaceTempView("combined_blocks_temp")
    first_word_only_blocks.createOrReplaceTempView("first_word_blocks_temp")
    acronym_only_blocks.createOrReplaceTempView("acronym_blocks_temp")

    # 4) Apply the UDTF using SQL with LATERAL syntax - only select UDTF output columns
    # Count blocks before splitting
    combined_blocks_before = combined_blocks.count()
    first_word_blocks_before = first_word_only_blocks.count()
    acronym_blocks_before = acronym_only_blocks.count()
    total_blocks_before = combined_blocks_before + first_word_blocks_before + acronym_blocks_before

    combined_blocks_final = (
        spark.sql(
            """
            SELECT udtf_output.* FROM combined_blocks_temp,
            LATERAL split_large_blocks(block_key, block_key_type, companies, block_size) AS udtf_output
            """
        )
        .orderBy(F.col("block_size"))
        .cache()
    )

    first_word_blocks_final = (
        spark.sql(
            """
            SELECT udtf_output.* FROM first_word_blocks_temp,
            LATERAL split_large_blocks(block_key, block_key_type, companies, block_size) AS udtf_output
            """
        )
        .orderBy(F.col("block_size"))
        .cache()
    )

    acronym_blocks_final = (
        spark.sql(
            """
            SELECT udtf_output.* FROM acronym_blocks_temp,
            LATERAL split_large_blocks(block_key, block_key_type, companies, block_size) AS udtf_output
         """
        )
        .orderBy(F.col("block_size"))
        .cache()
    )

    # Count blocks after splitting
    combined_blocks_after = combined_blocks_final.count()
    first_word_blocks_after = first_word_blocks_final.count()
    acronym_blocks_after = acronym_blocks_final.count()
    total_blocks_after = combined_blocks_after + first_word_blocks_after + acronym_blocks_after

    # Report on block splitting
    total_sub_blocks_created = total_blocks_after - total_blocks_before
    if total_sub_blocks_created > 0:
        logger.info(
            f"Block splitting created {total_sub_blocks_created:,} additional sub-blocks "
            f"({total_blocks_before:,} → {total_blocks_after:,})"
        )
        logger.info(
            f"  Combined blocks: {combined_blocks_before:,} → {combined_blocks_after:,} "
            f"(+{combined_blocks_after - combined_blocks_before:,})"
        )
        logger.info(
            f"  First-word blocks: {first_word_blocks_before:,} → {first_word_blocks_after:,} "
            f"(+{first_word_blocks_after - first_word_blocks_before:,})"
        )
        logger.info(
            f"  Acronym blocks: {acronym_blocks_before:,} → {acronym_blocks_after:,} "
            f"(+{acronym_blocks_after - acronym_blocks_before:,})"
        )
    else:
        logger.info(f"No blocks exceeded max size of {actual_max_block_size}, no splitting needed")

    # Save combined blocks separately
    combined_blocks_json_path = os.path.join(output_path, "combined_blocks.json")
    logger.info(f"Persisting combined blocks to {combined_blocks_json_path}")
    combined_blocks_final.repartition(1).write.mode("overwrite").json(combined_blocks_json_path)

    # Save first_word_only blocks separately
    first_word_json_path = os.path.join(output_path, "first_word_blocks.json")
    logger.info(f"Persisting first word blocks to {first_word_json_path}")
    first_word_blocks_final.repartition(1).write.mode("overwrite").json(first_word_json_path)

    # Save acronym_only blocks separately
    acronym_json_path = os.path.join(output_path, "acronym_blocks.json")
    logger.info(f"Persisting acronym blocks to {acronym_json_path}")
    acronym_blocks_final.repartition(1).write.mode("overwrite").json(acronym_json_path)

    # Handle companies with UNKNOWN block keys - create singleton blocks for them
    unblocked_blocks_df = None
    if unknown_count > 0:
        logger.info(
            f"Creating singleton blocks for {unknown_count} companies with UNKNOWN block keys..."
        )

        # Get the full company data for companies with UNKNOWN keys
        unknown_uuids = companies_with_unknown_keys.select("uuid")
        unknown_companies_full = full_companies_df.join(unknown_uuids, "uuid", "inner")

        # Create singleton blocks for each unknown company using DataFrame operations
        # Each company becomes its own block with block_size=1
        unblocked_blocks_df = unknown_companies_full.select(
            F.concat(F.lit("UNBLOCKED_"), F.col("uuid")).alias("block_key"),
            F.lit("unblocked").alias("block_key_type"),
            F.array(F.struct(*[F.col(c) for c in unknown_companies_full.columns])).alias(
                "companies"
            ),
            F.lit(1).alias("block_size"),
        )

        logger.info(f"Created {unblocked_blocks_df.count()} singleton blocks for UNKNOWN companies")

    # Create unified all_blocks output by combining all block types
    logger.info("Creating unified all_blocks output...")
    if unblocked_blocks_df is not None:
        all_blocks_df = (
            combined_blocks_final.unionByName(first_word_blocks_final)
            .unionByName(acronym_blocks_final)
            .unionByName(unblocked_blocks_df)
        )
    else:
        all_blocks_df = combined_blocks_final.unionByName(first_word_blocks_final).unionByName(
            acronym_blocks_final
        )

    # Save all_blocks to both JSON and Parquet formats
    all_blocks_json_path = os.path.join(output_path, "all_blocks.json")

    logger.info(f"Persisting all blocks to {all_blocks_json_path}")
    all_blocks_df.repartition(1).write.mode("overwrite").json(all_blocks_json_path)

    # Count total blocks and companies in unified output
    all_blocks_count = all_blocks_df.count()
    all_blocks_companies = all_blocks_df.agg(
        F.coalesce(F.sum("block_size"), F.lit(0)).alias("total")
    ).collect()[0]["total"]

    logger.info(f"Unified all_blocks: {all_blocks_count} blocks, {all_blocks_companies} companies")

    # Count blocks by type (after filtering and splitting)
    combined_block_count = combined_blocks_final.count()
    first_word_only_count = first_word_blocks_final.count()
    acronym_only_count = acronym_blocks_final.count()
    unblocked_count = unblocked_blocks_df.count() if unblocked_blocks_df is not None else 0
    total_blocks = (
        combined_block_count + first_word_only_count + acronym_only_count + unblocked_count
    )

    # Debug: Show schema and sample data for verification
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Combined blocks final schema:")
        combined_blocks_final.printSchema()
        logger.debug("Sample combined blocks:")
        combined_blocks_final.select("block_key", "block_size").show(5)

    # Count companies in each block type (after filtering and splitting)
    # Use coalesce to handle nulls properly
    combined_sum_result = combined_blocks_final.agg(
        F.coalesce(F.sum("block_size"), F.lit(0)).alias("total")
    ).collect()
    combined_companies_count = combined_sum_result[0]["total"]

    first_word_sum_result = first_word_blocks_final.agg(
        F.coalesce(F.sum("block_size"), F.lit(0)).alias("total")
    ).collect()
    first_word_only_companies_count = first_word_sum_result[0]["total"]

    acronym_sum_result = acronym_blocks_final.agg(
        F.coalesce(F.sum("block_size"), F.lit(0)).alias("total")
    ).collect()
    acronym_only_companies_count = acronym_sum_result[0]["total"]

    # Get original counts before splitting for comparison
    original_combined_count = combined_blocks.count()
    original_first_word_count = first_word_only_blocks.count()
    original_acronym_count = acronym_only_blocks.count()

    # Calculate additional metrics for summary
    total_company_instances = (
        combined_companies_count
        + first_word_only_companies_count
        + acronym_only_companies_count
        + (unblocked_count if unblocked_count > 0 else 0)
    )
    duplication_factor = total_company_instances / total_companies if total_companies > 0 else 0

    # Count singleton blocks accurately
    singleton_blocks = 0
    multi_company_blocks = 0
    for block_type_df in [combined_blocks_final, first_word_blocks_final, acronym_blocks_final]:
        if block_type_df is not None:
            singleton_blocks += block_type_df.filter(F.col("block_size") == F.lit(1)).count()
            multi_company_blocks += block_type_df.filter(
                F.col("block_size") > F.lit(1)  # type: ignore[call-arg,operator]
            ).count()

    logger.info("\n" + "=" * 60)
    logger.info("ENTITY RESOLUTION BLOCKING SUMMARY")
    logger.info("=" * 60)
    logger.info("WHAT IS BLOCKING?")
    logger.info("  Groups similar companies together to reduce comparisons")
    logger.info(
        f"  Without blocking: {total_companies:,} × {total_companies:,} = {total_companies * total_companies:,} comparisons"
    )
    logger.info(f"  With blocking: Only compare within {total_blocks:,} small blocks")
    logger.info("")
    logger.info("INPUT DATA:")
    logger.info(f"  Total unique companies: {total_companies:,}")
    logger.info("")
    logger.info("BLOCKING STRATEGY RESULTS:")
    logger.info(
        f"  Combined Blocks (both strategies agree): {combined_block_count:,} blocks, {combined_companies_count:,} companies"
    )
    if combined_block_count != original_combined_count:
        logger.info(
            f"    └─ Split from {original_combined_count:,} original blocks (chunks > {actual_max_block_size})"
        )
    logger.info(
        f"  First Word Only Blocks: {first_word_only_count:,} blocks, {first_word_only_companies_count:,} companies"
    )
    if first_word_only_count != original_first_word_count:
        logger.info(f"    └─ Split from {original_first_word_count:,} original blocks")
    logger.info(
        f"  Acronym Only Blocks: {acronym_only_count:,} blocks, {acronym_only_companies_count:,} companies"
    )
    if acronym_only_count != original_acronym_count:
        logger.info(f"    └─ Split from {original_acronym_count:,} original blocks")
    if unblocked_count > 0:
        logger.info(
            f"  Unblocked (no valid keys): {unblocked_count:,} singleton blocks, {unblocked_count:,} companies"
        )
    logger.info("")
    logger.info("BLOCK STATISTICS:")
    logger.info(f"  Total blocks created: {total_blocks:,}")
    logger.info(
        f"  Singleton blocks (no match possible): {singleton_blocks:,} ({singleton_blocks / total_blocks * 100:.1f}%)"
    )
    logger.info(
        f"  Multi-company blocks (matchable): {multi_company_blocks:,} ({multi_company_blocks / total_blocks * 100:.1f}%)"
    )
    logger.info(f"  Maximum block size: {actual_max_block_size} companies")
    logger.info(f"  Company instances across blocks: {total_company_instances:,}")
    logger.info(
        f"  Duplication factor: {duplication_factor:.2f}x (companies appear in multiple blocks)"
    )
    logger.info("")
    logger.info("OUTPUT FILES:")
    logger.info(f"  Combined blocks: {combined_blocks_json_path}")
    logger.info(f"  First word blocks: {first_word_json_path}")
    logger.info(f"  Acronym blocks: {acronym_json_path}")
    logger.info(f"  All blocks unified: {all_blocks_json_path}")
    logger.info("=" * 60)

    # Clean up
    companies_with_block_keys_df.unpersist()
    if stop_spark:
        spark.stop()


if __name__ == "__main__":
    build_blocks()
