#!/usr/bin/env python3
"""Entity resolution blocking strategies for company matching."""
import logging
import os
from typing import Optional

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
from abzu.spark.utils import create_split_large_blocks_udtf

logger = get_logger(__name__)

MAX_BLOCK_SIZE = config.get("process.kg.er.max_block_size", 50)

# Known domain suffixes to remove from company names
# Sorted by length (longest first) for efficient matching
DOMAIN_SUFFIXES = tuple(
    sorted(
        {
            ".com",
            ".org",
            ".net",
            ".edu",
            ".gov",
            ".mil",
            ".int",
            ".io",
            ".ai",
            ".co",
            ".uk",
            ".us",
            ".ca",
            ".au",
            ".de",
            ".fr",
            ".jp",
            ".cn",
            ".in",
            ".br",
            ".ru",
            ".it",
            ".es",
            ".nl",
            ".se",
            ".no",
            ".dk",
            ".fi",
            ".pl",
            ".mx",
            ".kr",
            ".tw",
            ".sg",
            ".hk",
            ".nz",
            ".ie",
            ".be",
            ".ch",
            ".at",
            ".cz",
            ".za",
            ".il",
            ".ae",
            ".sa",
            ".th",
            ".vn",
            ".ph",
            ".id",
            ".my",
            ".pk",
            ".bd",
            ".ng",
            ".ke",
            ".ug",
            ".tz",
            ".gh",
            ".zm",
            ".zw",
            ".biz",
            ".info",
            ".name",
            ".pro",
            ".museum",
            ".coop",
            ".aero",
            ".xxx",
            ".travel",
            ".mobi",
            ".tel",
            ".asia",
            ".cat",
            ".jobs",
            ".post",
        },
        key=len,
        reverse=True,
    )
)


def remove_domain_suffix(name: str) -> str:
    """
    Remove known domain suffixes from a company name.

    This function only removes recognized domain suffixes (e.g., .com, .org, .net)
    to avoid incorrectly removing legitimate periods in company names like
    "St. Jude Medical" or "Dr. Pepper".

    Args:
        name: The company name to process

    Returns:
        The name with domain suffix removed if present, otherwise the original name
    """
    if not name:
        return name

    name_lower = name.lower()
    for suffix in DOMAIN_SUFFIXES:
        if name_lower.endswith(suffix):
            # Remove the suffix and return
            return name[: -len(suffix)].strip()

    return name


@F.udf(T.StringType())
def get_first_word(name: str) -> str | None:
    """Extract first word if it's at least 1 character, removing domain suffixes."""
    if not name or not name.strip():
        return "UNKNOWN"  # Fallback for empty names
    # Remove domain suffix (only known TLDs like .com, .org, etc.)
    name_without_suffix = remove_domain_suffix(name.strip())
    words = name_without_suffix.split()
    return words[0].upper() if words else "UNKNOWN"


@F.udf(T.StringType())
def get_acronym(name: str) -> str | None:
    """Generate acronyms from company names, fallback to first word if no acronym."""
    if not name or not name.strip():
        return "UNKNOWN"  # Fallback for empty names

    # Remove domain suffix (only known TLDs like .com, .org, etc.)
    name_without_suffix = remove_domain_suffix(name.strip())
    acronym = get_acronyms(name_without_suffix)
    if acronym:
        return acronym
    # Fallback to first word if no acronym can be generated
    words = name_without_suffix.split()
    return words[0].upper() if words else "UNKNOWN"


def build_blocks(
    input_path: str = config.get("process.kg.er.paths.input"),
    output_path: str = config.get("process.kg.er.paths.names.blocks_dir"),
    strategy: str = "combined",
    local_mode: Optional[bool] = None,
    stop_spark: bool = True,
    max_block_size: Optional[int] = None,
) -> None:
    """
    Build entity resolution blocks using a single blocking strategy.

    Each strategy produces blocks where each company appears in exactly ONE block,
    eliminating duplicate processing paths across iterations.

    Strategies:
    - first_word: Block by first word of company name (e.g., "Apple Inc" -> "APPLE")
    - acronym: Block by acronym/initials (e.g., "International Business Machines" -> "IBM")
    - combined: Block by companies matching BOTH first_word AND acronym (highest precision)

    Args:
        input_path: Path to the input companies parquet
        output_path: Path to save the output blocks
        strategy: Blocking strategy to use (first_word, acronym, or combined)
        local_mode: Whether to run in local mode. If None, will be determined by environment
        stop_spark: Whether to stop the Spark session after processing
        max_block_size: Maximum block size (blocks larger than this will be chunked). If None, uses config value
    """
    # Validate strategy
    valid_strategies = ["first_word", "acronym", "combined"]
    if strategy not in valid_strategies:
        raise ValueError(f"Invalid strategy '{strategy}'. Must be one of: {valid_strategies}")
    logger.info(f"Using blocking strategy: {strategy}")

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
    if input_path.endswith(".parquet") or input_path.endswith(".parquet/"):
        companies_df_raw: DataFrame = spark.read.parquet(input_path)
    else:
        companies_df_raw = spark.read.json(input_path)

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

    # Build blocks for the selected strategy only
    logger.info(f"Building blocks using '{strategy}' strategy...")

    # Get complete company records
    if input_path.endswith(".parquet") or input_path.endswith(".parquet/"):
        full_companies_df_raw = spark.read.parquet(input_path)
    else:
        full_companies_df_raw = spark.read.json(input_path)
    full_companies_df = normalize_company_dataframe(
        full_companies_df_raw, preserve_extra_fields=False
    )

    # Get company fields without block-related fields
    company_fields = get_company_fields_without_blocks()

    if strategy == "first_word":
        # Block ALL companies by first_word - each company in exactly ONE block
        logger.info("Creating first_word blocks (each company in exactly one block)...")

        blocks_with_companies = (
            companies_with_block_keys_df.filter(
                F.col("first_word_block").isNotNull() & (F.col("first_word_block") != "UNKNOWN")
            )
            .select("uuid", F.col("first_word_block").alias("block_key"))
            .join(full_companies_df, "uuid", how="inner")
        )

        company_struct = F.struct(
            *[
                F.col(f) if f in blocks_with_companies.columns else F.lit(None).alias(f)
                for f in company_fields
            ]
        )

        strategy_blocks = (
            blocks_with_companies.groupBy("block_key")
            .agg(
                F.collect_list(company_struct).alias("companies"),
                F.countDistinct("uuid").alias("block_size"),
            )
            .withColumn("block_key_type", F.lit("first_word"))
            .select("block_key", "block_key_type", "companies", "block_size")
        )

    elif strategy == "acronym":
        # Block ALL companies by acronym - each company in exactly ONE block
        logger.info("Creating acronym blocks (each company in exactly one block)...")

        blocks_with_companies = (
            companies_with_block_keys_df.filter(
                F.col("acronym_block").isNotNull() & (F.col("acronym_block") != "UNKNOWN")
            )
            .select("uuid", F.col("acronym_block").alias("block_key"))
            .join(full_companies_df, "uuid", how="inner")
        )

        company_struct = F.struct(
            *[
                F.col(f) if f in blocks_with_companies.columns else F.lit(None).alias(f)
                for f in company_fields
            ]
        )

        strategy_blocks = (
            blocks_with_companies.groupBy("block_key")
            .agg(
                F.collect_list(company_struct).alias("companies"),
                F.countDistinct("uuid").alias("block_size"),
            )
            .withColumn("block_key_type", F.lit("acronym"))
            .select("block_key", "block_key_type", "companies", "block_size")
        )

    else:  # strategy == "combined"
        # Block only companies where BOTH first_word AND acronym agree (intersection)
        logger.info("Creating combined blocks (only companies where both strategies agree)...")

        # Get companies with their block keys for both strategies
        first_word_companies_df = (
            companies_with_block_keys_df.filter(
                F.col("first_word_block").isNotNull() & (F.col("first_word_block") != "UNKNOWN")
            )
            .select("uuid", F.col("first_word_block").alias("block_key"))
            .withColumn("strategy", F.lit("first_word"))
        )

        acronym_companies_df = (
            companies_with_block_keys_df.filter(
                F.col("acronym_block").isNotNull() & (F.col("acronym_block") != "UNKNOWN")
            )
            .select("uuid", F.col("acronym_block").alias("block_key"))
            .withColumn("strategy", F.lit("acronym"))
        )

        # Union and find overlapping block_keys (appear in both strategies)
        all_companies_with_blocks = first_word_companies_df.union(acronym_companies_df)

        overlapping_keys = (
            all_companies_with_blocks.groupBy("block_key")
            .agg(F.countDistinct("strategy").alias("strategy_count"))
            .filter(F.col("strategy_count") > 1)
            .select("block_key")
        )

        overlapping_count = overlapping_keys.count()
        logger.info(f"Found {overlapping_count:,} overlapping block_keys between strategies")

        # Create blocks only for overlapping keys
        blocks_with_companies = (
            all_companies_with_blocks.join(overlapping_keys, "block_key", how="inner")
            .dropDuplicates(["block_key", "uuid"])
            .join(full_companies_df, "uuid", how="inner")
        )

        company_struct = F.struct(
            *[
                F.col(f) if f in blocks_with_companies.columns else F.lit(None).alias(f)
                for f in company_fields
            ]
        )

        strategy_blocks = (
            blocks_with_companies.groupBy("block_key")
            .agg(
                F.collect_list(company_struct).alias("companies"),
                F.countDistinct("uuid").alias("block_size"),
            )
            .withColumn("block_key_type", F.lit("combined"))
            .select("block_key", "block_key_type", "companies", "block_size")
        )

    # Show top 20 blocks by company count
    logger.info(f"Top 20 {strategy} blocks by company count:")
    strategy_blocks.select("block_key", "block_size").orderBy(F.desc("block_size")).show(
        20, truncate=False
    )

    # Split large blocks (> max_block_size companies) into smaller chunks
    logger.info(
        f"Splitting large blocks (> {actual_max_block_size} companies) into smaller chunks..."
    )

    # Build the UDTF returnType dynamically from the actual DataFrame schema
    from pyspark.sql.types import ArrayType

    companies_field = strategy_blocks.schema["companies"]
    companies_array_type = companies_field.dataType
    assert isinstance(companies_array_type, ArrayType), "companies must be an ArrayType"
    companies_schema = companies_array_type.elementType.simpleString()
    udtf_return_type = (
        f"block_key: string, block_key_type: string, "
        f"companies: array<{companies_schema}>, "
        f"block_size: long"
    )
    logger.debug(f"UDTF return type: {udtf_return_type}")

    # Use shared UDTF factory from utils.py
    SplitLargeBlocks = create_split_large_blocks_udtf(udtf_return_type, actual_max_block_size)
    spark.udtf.register("split_large_blocks", SplitLargeBlocks)  # type: ignore[arg-type]

    # Create temp view and apply UDTF
    strategy_blocks.createOrReplaceTempView("strategy_blocks_temp")

    blocks_before = strategy_blocks.count()

    blocks_final = (
        spark.sql(
            """
            SELECT udtf_output.* FROM strategy_blocks_temp,
            LATERAL split_large_blocks(block_key, block_key_type, companies, block_size) AS udtf_output
            """
        )
        .orderBy(F.col("block_size"))
        .cache()
    )

    blocks_after = blocks_final.count()

    # Report on block splitting
    sub_blocks_created = blocks_after - blocks_before
    if sub_blocks_created > 0:
        logger.info(
            f"Block splitting created {sub_blocks_created:,} additional sub-blocks "
            f"({blocks_before:,} → {blocks_after:,})"
        )
    else:
        logger.info(f"No blocks exceeded max size of {actual_max_block_size}, no splitting needed")

    # Determine output path based on strategy
    strategy_output_path = os.path.join(output_path, f"{strategy}_blocks.parquet")
    logger.info(f"Persisting {strategy} blocks to {strategy_output_path}")
    blocks_final.repartition(1).write.mode("overwrite").parquet(strategy_output_path)

    # Count blocks and companies
    total_blocks = blocks_after
    total_companies_in_blocks = blocks_final.agg(
        F.coalesce(F.sum("block_size"), F.lit(0)).alias("total")
    ).collect()[0]["total"]

    # Count singleton vs multi-company blocks
    singleton_blocks = blocks_final.filter(F.col("block_size") == 1).count()
    multi_company_blocks = blocks_final.filter(F.col("block_size") > 1).count()

    # Debug: Show schema and sample data for verification
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"{strategy} blocks final schema:")
        blocks_final.printSchema()
        logger.debug(f"Sample {strategy} blocks:")
        blocks_final.select("block_key", "block_size").show(5)

    logger.info("\n" + "=" * 60)
    logger.info(f"ENTITY RESOLUTION BLOCKING SUMMARY - {strategy.upper()} STRATEGY")
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
    logger.info(f"STRATEGY: {strategy.upper()}")
    if strategy == "first_word":
        logger.info("  Blocks companies by first word of name (e.g., 'Apple Inc' -> 'APPLE')")
    elif strategy == "acronym":
        logger.info("  Blocks companies by acronym (e.g., 'IBM' -> 'IBM')")
    else:  # combined
        logger.info("  Blocks only companies where BOTH first_word AND acronym agree")
        logger.info("  (Highest precision, may have lower recall)")
    logger.info("")
    logger.info("BLOCKING RESULTS:")
    logger.info(f"  Blocks created: {total_blocks:,}")
    logger.info(f"  Companies in blocks: {total_companies_in_blocks:,}")
    if blocks_before != blocks_after:
        logger.info(
            f"  Blocks split (> {actual_max_block_size}): {blocks_before:,} → {blocks_after:,}"
        )
    logger.info("")
    logger.info("BLOCK STATISTICS:")
    logger.info(
        f"  Singleton blocks (no match possible): {singleton_blocks:,} ({singleton_blocks / total_blocks * 100:.1f}%)"
    )
    logger.info(
        f"  Multi-company blocks (matchable): {multi_company_blocks:,} ({multi_company_blocks / total_blocks * 100:.1f}%)"
    )
    logger.info(f"  Maximum block size: {actual_max_block_size} companies")
    logger.info("")
    logger.info("OUTPUT FILE:")
    logger.info(f"  {strategy_output_path}")
    logger.info("")
    logger.info("NEXT STEP:")
    logger.info(
        f"  Run matching with: abzu process er match names --iteration N --strategy {strategy}"
    )
    logger.info("=" * 60)

    # Clean up
    companies_with_block_keys_df.unpersist()
    blocks_final.unpersist()
    if stop_spark:
        spark.stop()


if __name__ == "__main__":
    build_blocks()
