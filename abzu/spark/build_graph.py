#!/usr/bin/env python3
"""Build a knowledge graph from pre-processed articles."""
import uuid
from typing import Optional

import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.sql import DataFrame, Row, SparkSession

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

    logger.info(f"Reading processed articles from {input_path} ...")
    articles_df: DataFrame = spark.read.json(input_path)
    logger.info(f"Loaded {articles_df.count():,} processed articles")

    # Show a sample record
    articles_df.show(1, truncate=100, vertical=True)

    #
    # Replace the integer IDs for Company entities within each article using a UDF
    #

    # This UDF processes an entire record from articles_df and replaces the integer IDs for Company,
    # Technology and Product entities with random UUIDs. The UUIDs must be consistent per integer
    # across each article.

    # Create a modified schema where integer references are converted to string UUIDs
    def create_uuid_schema(original_schema):
        """Create a schema where integer ID references are changed to string UUIDs."""
        fields = []
        for field in original_schema.fields:
            if field.name == "products":
                # Modify products array to change manufacturer from long to string
                # and technologies array from array<long> to array<string>
                product_fields = []
                for prod_field in field.dataType.elementType.fields:
                    if prod_field.name == "manufacturer":
                        # Change manufacturer from long to string (UUID)
                        product_fields.append(T.StructField("manufacturer", T.StringType(), True))
                    elif prod_field.name == "technologies":
                        # Change technologies from array<long> to array<string> (UUIDs)
                        product_fields.append(
                            T.StructField("technologies", T.ArrayType(T.StringType()), True)
                        )
                    else:
                        product_fields.append(prod_field)
                new_product_type = T.StructType(product_fields)
                fields.append(T.StructField("products", T.ArrayType(new_product_type), True))
            elif field.name == "technologies":
                # Modify technologies array to change developer from long to string
                tech_fields = []
                for tech_field in field.dataType.elementType.fields:
                    if tech_field.name == "developer":
                        # Change developer from long to string (UUID)
                        tech_fields.append(T.StructField("developer", T.StringType(), True))
                    else:
                        tech_fields.append(tech_field)
                new_tech_type = T.StructType(tech_fields)
                fields.append(T.StructField("technologies", T.ArrayType(new_tech_type), True))
            elif field.name == "relationships":
                # Modify relationships array to change company refs and arrays to strings
                rel_fields = []
                for rel_field in field.dataType.elementType.fields:
                    if rel_field.name in ["src_company", "dst_company"]:
                        # Change company refs from long to string (UUID)
                        rel_fields.append(T.StructField(rel_field.name, T.StringType(), True))
                    elif rel_field.name in ["technologies", "products"]:
                        # Change arrays from array<long> to array<string> (UUIDs)
                        rel_fields.append(
                            T.StructField(rel_field.name, T.ArrayType(T.StringType()), True)
                        )
                    else:
                        rel_fields.append(rel_field)
                new_rel_type = T.StructType(rel_fields)
                fields.append(T.StructField("relationships", T.ArrayType(new_rel_type), True))
            else:
                fields.append(field)
        return T.StructType(fields)

    uuid_schema = create_uuid_schema(articles_df.schema)

    @F.udf(returnType=uuid_schema)
    def replace_ids_with_uuids(row: Row) -> Row:
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
        id_to_uuid_map = {}

        # Helper function to get or create UUID for an integer ID
        def get_or_create_uuid(int_id):
            if int_id not in id_to_uuid_map:
                id_to_uuid_map[int_id] = str(uuid.uuid4())
            return id_to_uuid_map[int_id]

        # Helper function to update entity with UUID
        def update_entity_with_uuid(entity):
            if entity is None:
                return None
            # Convert to dict if it's a Row
            entity_dict = entity.asDict() if hasattr(entity, "asDict") else entity.copy()

            # Update uuid field if id exists
            if "id" in entity_dict and entity_dict["id"] is not None:
                entity_dict["uuid"] = get_or_create_uuid(entity_dict["id"])

            return entity_dict

        # First pass: collect all entity IDs to build the complete mapping
        # This ensures consistent UUIDs across all references

        # Collect IDs from companies
        if row_dict.get("companies"):
            for comp in row_dict["companies"]:
                comp_dict = comp.asDict() if hasattr(comp, "asDict") else comp
                if "id" in comp_dict and comp_dict["id"] is not None:
                    get_or_create_uuid(comp_dict["id"])

        # Collect IDs from products
        if row_dict.get("products"):
            for product in row_dict["products"]:
                product_dict = product.asDict() if hasattr(product, "asDict") else product
                if "id" in product_dict and product_dict["id"] is not None:
                    get_or_create_uuid(product_dict["id"])

        # Collect IDs from technologies
        if row_dict.get("technologies"):
            for tech in row_dict["technologies"]:
                tech_dict = tech.asDict() if hasattr(tech, "asDict") else tech
                if "id" in tech_dict and tech_dict["id"] is not None:
                    get_or_create_uuid(tech_dict["id"])

        # Collect IDs from tickers
        if row_dict.get("tickers"):
            for ticker in row_dict["tickers"]:
                ticker_dict = ticker.asDict() if hasattr(ticker, "asDict") else ticker
                if "id" in ticker_dict and ticker_dict["id"] is not None:
                    get_or_create_uuid(ticker_dict["id"])

        # Second pass: update entities with UUIDs and convert integer references

        # Process companies array - add UUIDs to each company
        if row_dict.get("companies"):
            row_dict["companies"] = [
                update_entity_with_uuid(comp) for comp in row_dict["companies"]
            ]

        # Process products array - add UUIDs to products and convert manufacturer references
        if row_dict.get("products"):
            updated_products = []
            for product in row_dict["products"]:
                product_dict = update_entity_with_uuid(product)
                # Convert manufacturer field from integer ID to UUID reference
                if "manufacturer" in product_dict and product_dict["manufacturer"] is not None:
                    product_dict["manufacturer"] = get_or_create_uuid(product_dict["manufacturer"])
                if "technologies" in product_dict and product_dict["technologies"]:
                    product_dict["technologies"] = [
                        get_or_create_uuid(tech_id)
                        for tech_id in product_dict["technologies"]
                        if tech_id is not None
                    ]
                updated_products.append(product_dict)
            row_dict["products"] = updated_products

        # Process technologies array - add UUIDs to technologies and convert developer references
        if row_dict.get("technologies"):
            updated_technologies = []
            for tech in row_dict["technologies"]:
                tech_dict = update_entity_with_uuid(tech)
                # Convert developer field from integer ID to UUID reference
                if "developer" in tech_dict and tech_dict["developer"] is not None:
                    tech_dict["developer"] = get_or_create_uuid(tech_dict["developer"])
                updated_technologies.append(tech_dict)
            row_dict["technologies"] = updated_technologies

        # Process tickers array - add UUIDs to tickers
        if row_dict.get("tickers"):
            row_dict["tickers"] = [
                update_entity_with_uuid(ticker) for ticker in row_dict["tickers"]
            ]

        # Process relationships array - convert all integer references to UUIDs
        if row_dict.get("relationships"):
            updated_relationships = []
            for rel in row_dict["relationships"]:
                rel_dict = rel.asDict() if hasattr(rel, "asDict") else rel.copy()

                # Convert src_company and dst_company from integer IDs to UUID references
                if "src_company" in rel_dict and rel_dict["src_company"] is not None:
                    rel_dict["src_company"] = get_or_create_uuid(rel_dict["src_company"])
                if "dst_company" in rel_dict and rel_dict["dst_company"] is not None:
                    rel_dict["dst_company"] = get_or_create_uuid(rel_dict["dst_company"])

                # Convert technologies array from integer IDs to UUID references
                if "technologies" in rel_dict and rel_dict["technologies"]:
                    rel_dict["technologies"] = [
                        get_or_create_uuid(tech_id)
                        for tech_id in rel_dict["technologies"]
                        if tech_id is not None
                    ]

                # Convert products array from integer IDs to UUID references
                if "products" in rel_dict and rel_dict["products"]:
                    rel_dict["products"] = [
                        get_or_create_uuid(prod_id)
                        for prod_id in rel_dict["products"]
                        if prod_id is not None
                    ]

                updated_relationships.append(rel_dict)
            row_dict["relationships"] = updated_relationships

        # Return the modified row as a Row object
        return Row(**row_dict)

    # Apply the UDF to transform articles_df
    logger.info("Replacing integer IDs with UUIDs for all entities...")
    articles_uuid_df = articles_df.select(
        replace_ids_with_uuids(F.struct([articles_df[x] for x in articles_df.columns])).alias(
            "data"
        )
    ).select("data.*")

    # Show sample to verify transformation
    logger.info("Sample article with UUID replacements:")
    articles_uuid_df.show(1, truncate=False, vertical=True)

    # Extract entities into separate dataframes
    logger.info("Extracting entities from documents ...")

    # Extract companies and assign a random UUID id
    logger.info("Extracting companies ...")
    companies_df = (
        articles_uuid_df.select(F.explode_outer(F.col("companies")).alias("company"))
        .filter("company IS NOT NULL")
        .select("company.*")
    )
    companies_df.show(5, truncate=100, vertical=True)

    # Store the original records with their UUIDs - they can be matched at the field level to nested
    # companies from the same post, such as Product.manufacturer or Technology.developer
    companies_output_path = f"{output_path}/companies.parquet"
    companies_df.repartition(1).write.mode("overwrite").parquet(companies_output_path)
    logger.info(f"Saved {companies_df.count():,} companies to {companies_output_path}")

    #
    # Now ETL Products - these are the products mentioned in the articles, manufactured by a Company
    #
    logger.info("Extracting products ...")
    products_df = (
        articles_uuid_df.select(F.explode_outer(F.col("products")).alias("product"))
        .filter("product IS NOT NULL")
        .select("product.*")
    )
    products_df.show(5, truncate=100, vertical=True)

    products_output_path = f"{output_path}/products.parquet"
    products_df.repartition(1).write.mode("overwrite").parquet(products_output_path)
    logger.info(f"Saved {products_df.count():,} products to {products_output_path}")

    #
    # Now ETL Technologies - these are the technologies mentioned in the articles, developed by a Company
    #

    logger.info("Extracting technologies ...")
    technologies_df = (
        articles_uuid_df.select(F.explode_outer(F.col("technologies")).alias("technology"))
        .filter("technology IS NOT NULL")
        .select("technology.*")
    )
    technologies_df.show(5, truncate=100, vertical=True)

    technologies_output_path = f"{output_path}/technologies.parquet"
    technologies_df.repartition(1).write.mode("overwrite").parquet(technologies_output_path)
    logger.info(f"Saved {technologies_df.count():,} technologies to {technologies_output_path}")

    #
    # Now ETL Deals - these are the deals mentioned in the articles, involving two Companies
    #

    relationships_df = (
        articles_uuid_df.select(F.explode_outer(F.col("relationships")).alias("relationship"))
        .filter("relationship IS NOT NULL")
        .select("relationship.*")
    )
    relationships_df.show(5, truncate=100, vertical=True)

    relationships_output_path = f"{output_path}/relationships.parquet"
    relationships_df.repartition(1).write.mode("overwrite").parquet(relationships_output_path)
    logger.info(f"Saved {relationships_df.count():,} deals to {relationships_output_path}")
