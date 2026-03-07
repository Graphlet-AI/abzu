#!/usr/bin/env python3
"""Utility functions for Spark operations."""

import random
import uuid
from typing import Any

import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.sql import DataFrame, Row
from pyspark.sql.window import Window

from abzu.logs import get_logger

logger = get_logger(__name__)


def select_most_common_property(
    df: DataFrame,
    unique_id_column: str,
    property_column: str,
    additional_columns: list[str] | None = None,
) -> DataFrame:
    """
    Select the most common value of a property for each unique identifier.

    For each unique identifier, this function:
    1. Counts occurrences of each property value
    2. Ranks property values by count (most common first)
    3. If counts are tied, selects the longest string value
    4. Returns one row per unique identifier with the selected property

    Parameters
    ----------
    df : DataFrame
        Input DataFrame containing the data
    unique_id_column : str
        Column name of the unique identifier (e.g., "name" for companies)
    property_column : str
        Column name of the property to select (e.g., "ticker")
    additional_columns : list[str], optional
        Additional columns to include in the output that are associated with
        the property (e.g., "exchange" when property is "symbol")

    Returns
    -------
    DataFrame
        DataFrame with one row per unique identifier, containing the unique_id_column,
        property_column, and any additional_columns specified

    Examples
    --------
    >>> # Select most common ticker per company
    >>> result = select_most_common_property(
    ...     companies_df, unique_id_column="name", property_column="ticker"
    ... )

    >>> # Select most common symbol per company with exchange info
    >>> result = select_most_common_property(
    ...     ticker_df,
    ...     unique_id_column="name",
    ...     property_column="symbol",
    ...     additional_columns=["exchange"],
    ... )
    """
    # Prepare columns to group by
    group_columns = [unique_id_column, property_column]
    if additional_columns:
        group_columns.extend(additional_columns)

    # Count occurrences of each property value per unique identifier
    counts_df = df.groupBy(*group_columns).agg(F.count("*").alias("property_count"))

    # Create window to rank by count (descending) and string length (descending) as tiebreaker
    window_spec = Window.partitionBy(unique_id_column).orderBy(
        F.desc("property_count"), F.desc(F.length(F.col(property_column)))
    )

    # Select the most common (or longest if tied) property value
    result_df = (
        counts_df.withColumn("rank", F.row_number().over(window_spec))
        .filter(F.col("rank") == 1)
        .drop("rank", "property_count")
    )

    return result_df


# Create a modified schema where integer references are converted to string UUIDs
def create_uuid_schema(original_schema: T.StructType) -> T.StructType:
    """Create a schema where integer ID references are changed to string UUIDs."""
    fields = []
    for field in original_schema.fields:
        if field.name == "products":
            # Modify products array to change manufacturer from long to string
            # and technologies array from array<long> to array<string>
            product_fields = []
            for prod_field in field.dataType.elementType.fields:  # type: ignore[attr-defined]
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
            for tech_field in field.dataType.elementType.fields:  # type: ignore[attr-defined]
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
            for rel_field in field.dataType.elementType.fields:  # type: ignore[attr-defined]
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


def validate_referential_integrity(row: Row) -> bool:

    # Convert Row to dict for easier manipulation
    row_dict = row.asDict()

    # Validate that relationships only reference existing company IDs
    company_ids = set()
    if row_dict.get("companies"):
        for comp in row_dict["companies"]:
            comp_dict = comp.asDict() if hasattr(comp, "asDict") else comp
            if "id" in comp_dict and comp_dict["id"] is not None:
                company_ids.add(comp_dict["id"])

    try:
        # Check all relationships reference valid company IDs
        if row_dict.get("relationships"):
            for idx, rel in enumerate(row_dict["relationships"]):
                rel_dict = rel.asDict() if hasattr(rel, "asDict") else rel
                if "src_company" in rel_dict and rel_dict["src_company"] is not None:
                    if rel_dict["src_company"] not in company_ids:
                        raise ValueError(
                            f"Relationship {idx} from {row_dict['url']} references non-existent src_company ID: {rel_dict['src_company']}. "
                            f"Available company IDs: {sorted(company_ids)}"
                        )
                if "dst_company" in rel_dict and rel_dict["dst_company"] is not None:
                    if rel_dict["dst_company"] not in company_ids:
                        raise ValueError(
                            f"Relationship {idx} from {row_dict['url']} references non-existent dst_company ID: {rel_dict['dst_company']}. "
                            f"Available company IDs: {sorted(company_ids)}"
                        )

    except ValueError as e:
        logger.error(f"Referential integrity check failed for article {row_dict['url']}: {e}")
        return False

    return True


# Helper function to get or create UUID for an integer ID
def get_or_create_uuid(int_id: int, id_to_uuid_map: dict[int, str]) -> str:
    if int_id not in id_to_uuid_map:
        id_to_uuid_map[int_id] = str(uuid.uuid4())
    return id_to_uuid_map[int_id]


# Helper function to update entity with UUID
def update_entity_with_uuid(
    entity: Row | dict[str, Any] | None, id_to_uuid_map: dict[int, str]
) -> dict[str, Any] | None:
    if entity is None:
        return None
    # Convert to dict if it's a Row
    entity_dict = entity.asDict() if isinstance(entity, Row) else entity.copy()

    # Always ensure both ID and UUID exist
    # If ID is missing or null, assign a random one
    if "id" not in entity_dict or entity_dict["id"] is None:
        entity_dict["id"] = random.randint(1, 50)

    # Always ensure a UUID exists
    if "id" in entity_dict and entity_dict["id"] is not None:
        # Use consistent UUID mapping based on the ID
        entity_dict["uuid"] = get_or_create_uuid(entity_dict["id"], id_to_uuid_map)
    else:
        # Fallback: generate a new UUID if somehow ID is still missing
        entity_dict["uuid"] = str(uuid.uuid4())

    return entity_dict


def create_split_large_blocks_udtf(
    udtf_return_type: str,
    max_block_size: int,
) -> type:
    """Create a SplitLargeBlocks UDTF class with the given return type and max block size.

    This factory function creates a PySpark UDTF that splits blocks larger than
    max_block_size into smaller chunks. The UDTF is used for both regular ER blocking
    and final UUID-based deduplication.

    Parameters
    ----------
    udtf_return_type : str
        The return type string for the UDTF, e.g.,
        "block_key: string, block_key_type: string, companies: array<...>, block_size: long"
    max_block_size : int
        Maximum number of companies per block before splitting

    Returns
    -------
    type
        A decorated UDTF class that can be registered with spark.udtf.register()

    Examples
    --------
    >>> udtf_return_type = build_udtf_return_type()
    >>> SplitLargeBlocks = create_split_large_blocks_udtf(udtf_return_type, 50)
    >>> spark.udtf.register("split_large_blocks", SplitLargeBlocks)
    """

    @F.udtf(returnType=udtf_return_type)  # type: ignore
    class SplitLargeBlocks:
        def eval(
            self,
            block_key: str,
            block_key_type: str,
            companies: list[dict[str, Any]],
            block_size: int,
        ):  # type: ignore
            if block_size <= max_block_size:
                yield (block_key, block_key_type, companies, block_size)
            else:
                chunk_num = 1
                for i in range(0, len(companies), max_block_size):
                    chunk_companies = companies[i : i + max_block_size]
                    chunk_key = f"{block_key}_chunk_{chunk_num}"
                    yield (chunk_key, block_key_type, chunk_companies, len(chunk_companies))
                    chunk_num += 1

    return SplitLargeBlocks
