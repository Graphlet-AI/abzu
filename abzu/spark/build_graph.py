#!/usr/bin/env python3
"""Build a knowledge graph from pre-processed articles."""
import logging
import os
from typing import Optional

import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.sql import DataFrame, Row, SparkSession

from abzu.config import config
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session
from abzu.spark.utils import (
    create_uuid_schema,
    get_or_create_uuid,
    update_entity_with_uuid,
    validate_referential_integrity,
)

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

    logger.info(f"Reading processed articles from {input_path} ...")
    articles_df: DataFrame = spark.read.json(input_path)
    logger.info(f"Loaded {articles_df.count():,} processed articles")

    # Show a sample record
    if logger.isEnabledFor(logging.DEBUG):
        articles_df.show(1, truncate=100, vertical=True)

    #
    # Replace the integer IDs for Company entities within each article using a UDF
    #

    # This UDF processes an entire record from articles_df and replaces the integer IDs for Company,
    # Technology and Product entities with random UUIDs. The UUIDs must be consistent per integer
    # across each article.

    validate_referential_integrity_udf = F.udf(validate_referential_integrity, T.BooleanType())

    # Filter out records with references in relationships to non-existent companies.
    clean_articles_df = articles_df.filter(
        validate_referential_integrity_udf(
            F.struct([articles_df[x] for x in articles_df.columns])
        ).alias("data")
    )
    # Set aside all badly processed articles for re-processing
    bad_articles_df = articles_df.exceptAll(clean_articles_df)

    bad_article_json_path, bad_article_parquet_path, bad_article_csv_path = (
        os.path.join(output_path, "bad_articles.jsonl"),
        os.path.join(output_path, "bad_articles.parquet"),
        os.path.join(output_path, "bad_articles.csv"),
    )
    bad_articles_df.repartition(1).write.mode("overwrite").json(bad_article_json_path)
    bad_articles_df.repartition(1).write.mode("overwrite").parquet(bad_article_parquet_path)
    bad_articles_df.select(
        "title",
        "url",
        "posted_at",
        "collected_at",
    ).repartition(1).write.mode(
        "overwrite"
    ).csv(bad_article_csv_path)

    logger.info(
        f"{clean_articles_df.count():,} good articles. {bad_articles_df.count():,} bad articles."
    )
    logger.info(
        f"Saved bad articles to {bad_article_json_path}, {bad_article_parquet_path}, and {bad_article_csv_path}"
    )

    def replace_ids_with_uuids_impl(row: Row) -> Row:
        """
        Replace integer IDs with UUIDs in all entity references within an article row.

        This function processes an entire article record and replaces integer IDs in Company,
        Technology, Product, and Ticker entities with random UUIDs. The same UUID is used for
        all references to the same integer ID within a single article.

        Args:
            row: A PySpark Row object containing the article data

        Returns:
            A modified Row with UUIDs added to all entity references
        """
        # Convert Row to dict for easier manipulation
        row_dict = row.asDict()

        # Create mapping from integer IDs to UUIDs for this article
        id_to_uuid_map: dict[int, str] = {}

        # 1st Pass: collect all entity IDs to build the complete mapping. Ensures consistent UUIDs
        # across all references

        # Collect IDs from companies
        if row_dict.get("companies"):
            for comp in row_dict["companies"]:
                comp_dict = comp.asDict() if hasattr(comp, "asDict") else comp
                if "id" in comp_dict and comp_dict["id"] is not None:
                    get_or_create_uuid(comp_dict["id"], id_to_uuid_map)

        # Collect IDs from products
        if row_dict.get("products"):
            for product in row_dict["products"]:
                product_dict = product.asDict() if hasattr(product, "asDict") else product
                if "id" in product_dict and product_dict["id"] is not None:
                    get_or_create_uuid(product_dict["id"], id_to_uuid_map)

        # Collect IDs from technologies
        if row_dict.get("technologies"):
            for tech in row_dict["technologies"]:
                tech_dict = tech.asDict() if hasattr(tech, "asDict") else tech
                if "id" in tech_dict and tech_dict["id"] is not None:
                    get_or_create_uuid(tech_dict["id"], id_to_uuid_map)

        # Collect IDs from tickers
        if row_dict.get("tickers"):
            for ticker in row_dict["tickers"]:
                ticker_dict = ticker.asDict() if hasattr(ticker, "asDict") else ticker
                if "id" in ticker_dict and ticker_dict["id"] is not None:
                    get_or_create_uuid(ticker_dict["id"], id_to_uuid_map)

        # Collect IDs from relationships to ensure company references get consistent UUIDs
        # This is critical - without this, relationships get different UUIDs than companies
        if row_dict.get("relationships"):
            for rel in row_dict["relationships"]:
                rel_dict = rel.asDict() if hasattr(rel, "asDict") else rel
                if "src_company" in rel_dict and rel_dict["src_company"] is not None:
                    get_or_create_uuid(rel_dict["src_company"], id_to_uuid_map)
                if "dst_company" in rel_dict and rel_dict["dst_company"] is not None:
                    get_or_create_uuid(rel_dict["dst_company"], id_to_uuid_map)

        # Second pass: update entities with UUIDs and convert integer references

        # Process companies array - add UUIDs to each company
        if row_dict.get("companies"):
            row_dict["companies"] = [
                update_entity_with_uuid(comp, id_to_uuid_map) for comp in row_dict["companies"]
            ]

        # Process products array - add UUIDs to products and convert manufacturer references
        if row_dict.get("products"):
            updated_products = []
            for product in row_dict["products"]:
                product_dict = update_entity_with_uuid(product, id_to_uuid_map)
                if product_dict is not None:
                    # Convert manufacturer field from integer ID to UUID reference
                    if "manufacturer" in product_dict and product_dict["manufacturer"] is not None:
                        product_dict["manufacturer"] = get_or_create_uuid(
                            product_dict["manufacturer"], id_to_uuid_map
                        )
                    if "technologies" in product_dict and product_dict["technologies"]:
                        product_dict["technologies"] = [
                            get_or_create_uuid(tech_id, id_to_uuid_map)
                            for tech_id in product_dict["technologies"]
                            if tech_id is not None
                        ]
                    updated_products.append(product_dict)
            row_dict["products"] = updated_products

        # Process technologies array - add UUIDs to technologies and convert developer references
        if row_dict.get("technologies"):
            updated_technologies = []
            for tech in row_dict["technologies"]:
                tech_dict = update_entity_with_uuid(tech, id_to_uuid_map)
                if tech_dict is not None:
                    # Convert developer field from integer ID to UUID reference
                    if "developer" in tech_dict and tech_dict["developer"] is not None:
                        tech_dict["developer"] = get_or_create_uuid(
                            tech_dict["developer"], id_to_uuid_map
                        )
                    updated_technologies.append(tech_dict)
            row_dict["technologies"] = updated_technologies

        # Process tickers array - add UUIDs to tickers
        if row_dict.get("tickers"):
            row_dict["tickers"] = [
                update_entity_with_uuid(ticker, id_to_uuid_map)
                for ticker in row_dict["tickers"]
                if update_entity_with_uuid(ticker, id_to_uuid_map) is not None
            ]

        # Process relationships array - convert all integer references to UUIDs
        if row_dict.get("relationships"):
            updated_relationships = []
            for rel in row_dict["relationships"]:
                rel_dict = rel.asDict() if hasattr(rel, "asDict") else rel.copy()

                # Convert src_company and dst_company from integer IDs to UUID references
                if "src_company" in rel_dict and rel_dict["src_company"] is not None:
                    rel_dict["src_company"] = get_or_create_uuid(
                        rel_dict["src_company"], id_to_uuid_map
                    )
                if "dst_company" in rel_dict and rel_dict["dst_company"] is not None:
                    rel_dict["dst_company"] = get_or_create_uuid(
                        rel_dict["dst_company"], id_to_uuid_map
                    )

                # Convert technologies array from integer IDs to UUID references
                if "technologies" in rel_dict and rel_dict["technologies"]:
                    rel_dict["technologies"] = [
                        get_or_create_uuid(tech_id, id_to_uuid_map)
                        for tech_id in rel_dict["technologies"]
                        if tech_id is not None
                    ]

                # Convert products array from integer IDs to UUID references
                if "products" in rel_dict and rel_dict["products"]:
                    rel_dict["products"] = [
                        get_or_create_uuid(prod_id, id_to_uuid_map)
                        for prod_id in rel_dict["products"]
                        if prod_id is not None
                    ]

                updated_relationships.append(rel_dict)
            row_dict["relationships"] = updated_relationships

        # Return the modified row as a Row object
        return Row(**row_dict)

    # Create the non-deterministic UDF
    replace_ids_with_uuids = F.udf(
        replace_ids_with_uuids_impl, returnType=create_uuid_schema(articles_df.schema)
    ).asNondeterministic()

    # Apply the UDF to transform articles_df
    logger.info("Replacing integer IDs with UUIDs for all entities...")
    articles_uuid_df = clean_articles_df.select(
        replace_ids_with_uuids(
            F.struct([clean_articles_df[x] for x in clean_articles_df.columns])
        ).alias("data")
    ).select("data.*")

    # CRITICAL: Cache the transformed data to prevent UDF re-evaluation during extractions
    # This ensures UUID consistency across all entity extractions
    articles_uuid_df = articles_uuid_df.cache()

    # Force evaluation to materialize the cache
    logger.info(f"Transformed {articles_uuid_df.count():,} articles with UUID replacements")

    # Show sample to verify transformation
    if logger.isEnabledFor(logging.DEBUG):
        logger.info("Sample article with UUID replacements:")
        articles_uuid_df.show(1, truncate=100, vertical=True)

    # Extract entities into separate dataframes
    logger.info("Extracting entities from documents ...")

    # Extract companies and assign a random UUID id
    logger.info("Extracting companies ...")
    companies_df = (
        articles_uuid_df.select("url", F.explode_outer(F.col("companies")).alias("company"))
        .filter("company IS NOT NULL")
        .select("url", "company.*")
    )
    if logger.isEnabledFor(logging.DEBUG):
        companies_df.show(5, truncate=100, vertical=True)

    # Clean company names - remove carriage returns and extra whitespace
    companies_df = companies_df.withColumn(
        "name", F.trim(F.regexp_replace(F.col("name"), r"[\r\n]+", " "))
    )

    # Put the uuid, url columns first
    companies_df = companies_df.select(
        ["uuid", "url", "name", "description"]
        + [col for col in companies_df.columns if col not in ["uuid", "url", "name", "description"]]
    )

    # Check for null UUIDs and IDs - filter them out
    null_uuid_count = companies_df.filter(F.col("uuid").isNull()).count()  # type: ignore
    null_id_count = companies_df.filter(F.col("id").isNull()).count()  # type: ignore

    if null_uuid_count > 0:
        logger.warning(f"Found {null_uuid_count:,} companies with null UUIDs - filtering them out")
        # Show some examples for debugging
        logger.warning("Sample companies with null UUIDs:")
        companies_df.filter(F.col("uuid").isNull()).show(5, truncate=False)  # type: ignore

    if null_id_count > 0:
        logger.warning(f"Found {null_id_count:,} companies with null IDs - filtering them out")
        # Show some examples for debugging
        logger.warning("Sample companies with null IDs:")
        companies_df.filter(F.col("id").isNull()).show(5, truncate=False)  # type: ignore

    # Filter out companies with null UUIDs or IDs
    companies_df = companies_df.filter(F.col("uuid").isNotNull() & F.col("id").isNotNull())  # type: ignore
    logger.info(f"After filtering nulls: {companies_df.count():,} companies remain")

    # Explicitly cast id to ensure it's a non-null integer and uuid to ensure it's a non-null string
    companies_df = companies_df.withColumn("id", F.col("id").cast(T.LongType()))
    companies_df = companies_df.withColumn("uuid", F.col("uuid").cast(T.StringType()))

    # Store the original records with their UUIDs - they can be matched at the field level to nested
    # companies from the same post, such as Product.manufacturer or Technology.developer
    companies_output_path = os.path.join(output_path, "companies.parquet")
    companies_df.repartition(1).write.mode("overwrite").parquet(companies_output_path)
    logger.info(f"Saved {companies_df.count():,} companies to {companies_output_path}")

    companies_jsonl_output_path = os.path.join(output_path, "companies.jsonl")
    companies_df.repartition(1).write.mode("overwrite").json(companies_jsonl_output_path)
    logger.info(f"Saved companies to {companies_jsonl_output_path}")

    #
    # Now ETL Products - these are the products mentioned in the articles, manufactured by a Company
    #
    logger.info("Extracting products ...")
    products_df = (
        articles_uuid_df.select("url", F.explode_outer(F.col("products")).alias("product"))
        .filter("product IS NOT NULL")
        .select("url", "product.*")
    )
    if logger.isEnabledFor(logging.DEBUG):
        products_df.show(5, truncate=100, vertical=True)

    # Put the uuid and url columns first
    products_df = products_df.select(
        ["uuid", "url", "name", "description"]
        + [col for col in products_df.columns if col not in ["uuid", "url", "name", "description"]]
    )

    products_output_path = os.path.join(output_path, "products.parquet")
    products_df.repartition(1).write.mode("overwrite").parquet(products_output_path)
    logger.info(f"Saved {products_df.count():,} products to {products_output_path}")

    products_jsonl_output_path = os.path.join(output_path, "products.jsonl")
    products_df.repartition(1).write.mode("overwrite").json(products_jsonl_output_path)
    logger.info(f"Saved products to {products_jsonl_output_path}")

    #
    # Now ETL Technologies - these are the technologies mentioned in the articles, developed by a Company
    #

    logger.info("Extracting technologies ...")
    technologies_df = (
        articles_uuid_df.select("url", F.explode_outer(F.col("technologies")).alias("technology"))
        .filter("technology IS NOT NULL")
        .select("url", "technology.*")
    )
    if logger.isEnabledFor(logging.DEBUG):
        technologies_df.show(5, truncate=100, vertical=True)

    # Put the uuid and url columns first
    technologies_df = technologies_df.select(
        ["uuid", "url", "name", "description"]
        + [
            col
            for col in technologies_df.columns
            if col not in ["uuid", "url", "name", "description"]
        ]
    )

    technologies_output_path = os.path.join(output_path, "technologies.parquet")
    technologies_df.repartition(1).write.mode("overwrite").parquet(technologies_output_path)
    logger.info(f"Saved {technologies_df.count():,} technologies to {technologies_output_path}")

    technologies_jsonl_output_path = os.path.join(output_path, "technologies.jsonl")
    technologies_df.repartition(1).write.mode("overwrite").json(technologies_jsonl_output_path)
    logger.info(f"Saved technologies to {technologies_jsonl_output_path}")

    #
    # Now ETL Tickers - these are the ticker symbols mentioned in the articles
    #
    logger.info("Extracting tickers ...")
    tickers_df = (
        articles_uuid_df.select("url", F.explode_outer(F.col("tickers")).alias("ticker"))
        .filter("ticker IS NOT NULL")
        .select("url", "ticker.*")
    )
    if logger.isEnabledFor(logging.DEBUG):
        tickers_df.show(5, truncate=100, vertical=True)

    # Put the uuid and url columns first
    tickers_df = tickers_df.select(
        "uuid",
        "symbol",
        "exchange",
        "url",
    )

    tickers_output_path = os.path.join(output_path, "tickers.parquet")
    tickers_df.repartition(1).write.mode("overwrite").parquet(tickers_output_path)
    logger.info(f"Saved {tickers_df.count():,} tickers to {tickers_output_path}")

    tickers_jsonl_output_path = os.path.join(output_path, "tickers.jsonl")
    tickers_df.repartition(1).write.mode("overwrite").json(tickers_jsonl_output_path)
    logger.info(f"Saved tickers to {tickers_jsonl_output_path}")

    #
    # Now ETL Deals - these are the deals mentioned in the articles, involving two Companies
    #

    relationships_df = (
        articles_uuid_df.select(
            F.col("url").alias("article_url"),
            F.col("posted_at").alias("article_posted_at"),
            F.explode_outer(F.col("relationships")).alias("relationship"),
        )
        .filter("relationship IS NOT NULL")
        .select(
            F.col("article_url").alias("url"),
            F.col("article_posted_at").alias("posted_at"),
            "relationship.*",
        )
    )
    if logger.isEnabledFor(logging.DEBUG):
        relationships_df.show(5, truncate=100, vertical=True)

    relationship_count = relationships_df.count()

    rel_cols = [
        "src_company AS src",
        "dst_company AS dst",
        "type AS relationship",
        "description",
        "url",
        "posted_at",
    ] + [
        col
        for col in relationships_df.columns
        if col not in ["url", "posted_at", "src_company", "dst_company", "description", "type"]
    ]
    # Put the uuid and url columns first
    relationships_named_df = relationships_df.selectExpr(rel_cols)

    #
    # Only take relationships with non-null src/dst companies
    #
    relationships_clean_df = relationships_named_df.filter(
        F.col("src").isNotNull() & F.col("dst").isNotNull()  # type: ignore[call-arg]
    )

    #
    # Replace product/technology UUIDs with names for visualization
    #
    logger.info("Replacing product/technology UUIDs with names...")

    # Create lookup maps for products and technologies (uuid -> name)
    products_lookup = products_df.select(
        F.col("uuid").alias("product_uuid"),
        F.col("name").alias("product_name"),
    ).distinct()

    technologies_lookup = technologies_df.select(
        F.col("uuid").alias("tech_uuid"),
        F.col("name").alias("tech_name"),
    ).distinct()

    # Collect lookups as broadcast variables for efficiency
    products_map = {row["product_uuid"]: row["product_name"] for row in products_lookup.collect()}
    technologies_map = {row["tech_uuid"]: row["tech_name"] for row in technologies_lookup.collect()}

    # Broadcast the maps
    products_map_bc = spark.sparkContext.broadcast(products_map)
    technologies_map_bc = spark.sparkContext.broadcast(technologies_map)

    # UDFs that use the broadcast variables
    @F.udf(T.ArrayType(T.StringType()))
    def replace_product_uuids(uuids: list) -> list:
        if uuids is None:
            return None
        return [products_map_bc.value.get(uuid, uuid) for uuid in uuids if uuid is not None]

    @F.udf(T.ArrayType(T.StringType()))
    def replace_tech_uuids(uuids: list) -> list:
        if uuids is None:
            return None
        return [technologies_map_bc.value.get(uuid, uuid) for uuid in uuids if uuid is not None]

    # Apply the UDFs to replace UUIDs with names
    relationships_with_names_df = relationships_clean_df.withColumn(
        "products", replace_product_uuids(F.col("products"))
    ).withColumn("technologies", replace_tech_uuids(F.col("technologies")))

    relationships_output_path = os.path.join(output_path, "relationships.parquet")
    relationships_with_names_df.repartition(1).write.mode("overwrite").parquet(
        relationships_output_path
    )
    logger.info(f"Saved {relationships_df.count():,} relationships to {relationships_output_path}")

    relationships_jsonl_output_path = os.path.join(output_path, "relationships.jsonl")
    relationships_with_names_df.repartition(1).write.mode("overwrite").json(
        relationships_jsonl_output_path
    )
    logger.info(f"Saved relationships to {relationships_jsonl_output_path}")

    #
    # Validate that all src/dst fields in relationships refer to real companies
    #
    valid_companies = companies_df.select("uuid").distinct()

    # Use INNER joins to only keep matching rows
    valid_relationships_df = relationships_clean_df.join(
        valid_companies.withColumnRenamed("uuid", "src_uuid"),
        relationships_clean_df.src == F.col("src_uuid"),
        "inner",
    ).join(
        valid_companies.withColumnRenamed("uuid", "dst_uuid"),
        relationships_clean_df.dst == F.col("dst_uuid"),
        "inner",
    )

    valid_relationship_count = valid_relationships_df.count()
    logger.info(
        f"Found {(valid_relationship_count / relationship_count) * 100:.1f}% {valid_relationship_count:,} valid relationships out of {relationship_count:,}"
    )
