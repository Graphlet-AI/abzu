"""Spark schema definitions using Sparkdantic for BAML types."""

from typing import cast

import pyspark.sql.functions as F
from pyspark.sql import DataFrame
from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    DataType,
    IntegerType,
    LongType,
    MapType,
    StringType,
    StructField,
    StructType,
)
from sparkdantic import SparkModel

from abzu.baml_client.types import Company, CompanyList, Ticker
from abzu.logs import get_logger

logger = get_logger(__name__)

# Rebuild the models to resolve forward references
Company.model_rebuild()
Ticker.model_rebuild()
CompanyList.model_rebuild()

# Block schema field names - the canonical source of truth for ER block schemas
# These match the BAML CompanyList type
BLOCK_FIELDS = ["block_key", "block_key_type", "companies", "block_size"]


class SparkTicker(Ticker, SparkModel):
    """Spark-compatible Ticker model."""

    pass


class SparkCompany(Company, SparkModel):
    """Spark-compatible Company model matching BAML Company."""

    pass


def get_company_fields_without_blocks() -> list[str]:
    """Get Company field names excluding block-related fields.

    Returns:
        List of field names from Company model, excluding block_key, block_key_type, block_size
    """
    excluded_fields = {"block_key", "block_key_type", "block_size"}
    # Use the original Company model fields from BAML
    return [field for field in Company.model_fields.keys() if field not in excluded_fields]


def convert_ints_to_longs(data_type: DataType) -> DataType:
    """Recursively convert IntegerType to LongType in a schema.

    This is needed because some fields like revenue_usd can exceed int32 limits.

    Args:
        data_type: A PySpark data type

    Returns:
        The data type with IntegerType converted to LongType
    """
    if isinstance(data_type, IntegerType):
        return LongType()
    elif isinstance(data_type, StructType):
        fields = []
        for field in data_type.fields:
            new_field = StructField(
                field.name, convert_ints_to_longs(field.dataType), field.nullable, field.metadata
            )
            fields.append(new_field)
        return StructType(fields)
    elif isinstance(data_type, ArrayType):
        return ArrayType(convert_ints_to_longs(data_type.elementType), data_type.containsNull)
    elif isinstance(data_type, MapType):
        return MapType(
            convert_ints_to_longs(data_type.keyType),
            convert_ints_to_longs(data_type.valueType),
            data_type.valueContainsNull,
        )
    else:
        return data_type


# At the top of get_company_spark_schema() function
def get_company_spark_schema() -> StructType:
    """Get the Spark StructType schema for Company.

    Returns:
        StructType schema for Company model with IntegerType converted to LongType
    """
    # Ensure forward references are resolved
    Company.model_rebuild()
    Ticker.model_rebuild()

    company_schema = SparkCompany(
        id=1, name="Google", description="Search, Big Data and AI"
    ).model_spark_schema()

    # Convert all IntegerType fields to LongType to handle large values
    # This is needed for fields like revenue_usd which can be in billions
    company_schema = cast(StructType, convert_ints_to_longs(company_schema))

    return company_schema


def get_company_ddl_string() -> str:
    """Get DDL string representation of Company schema.

    Returns:
        DDL string for Company struct, suitable for UDTF returnType
    """
    # Get the Spark schema
    schema = get_company_spark_schema()

    # Convert to DDL string
    # This will give us something like: "id:bigint,uuid:string,name:string,..."
    result: str = schema.simpleString()
    return result


def normalize_company_dataframe(df: DataFrame, preserve_extra_fields: bool = False) -> DataFrame:
    """Normalize a DataFrame to match the Company schema exactly.

    This ensures consistent field order and types across iterations.

    Args:
        df: Input DataFrame with company data
        preserve_extra_fields: If True, keep fields not in Company schema (append at end)

    Returns:
        DataFrame with normalized schema matching Company model
    """
    # Get expected fields from Company model
    expected_fields = list(Company.model_fields.keys())

    # Get the correct schema types for each field
    company_schema = get_company_spark_schema()
    field_types = {field.name: field.dataType for field in company_schema.fields}

    # Get current DataFrame columns
    current_columns = df.columns

    # Log schema differences for debugging
    missing_fields = set(expected_fields) - set(current_columns)
    extra_fields = set(current_columns) - set(expected_fields)

    if missing_fields:
        logger.debug(f"Adding missing fields with null values: {missing_fields}")
    if extra_fields:
        if preserve_extra_fields:
            logger.debug(f"Preserving extra fields: {extra_fields}")
        else:
            logger.debug(f"Dropping extra fields: {extra_fields}")

    # Build select list with expected fields in correct order
    select_list = []
    for field in expected_fields:
        if field in current_columns:
            select_list.append(F.col(field))
        else:
            # Add missing field as null with correct type from BAML schema
            field_type = field_types.get(field)
            if field_type:
                select_list.append(F.lit(None).cast(field_type).alias(field))
            else:
                select_list.append(F.lit(None).alias(field))

    # Optionally preserve extra fields at the end
    if preserve_extra_fields:
        for field in extra_fields:
            select_list.append(F.col(field))

    # Select fields in correct order
    normalized_df = df.select(*select_list)

    # Log the normalized schema for debugging
    logger.debug(f"Normalized schema fields: {normalized_df.columns}")

    return normalized_df


def build_udtf_company_struct_string() -> str:
    """Build the struct string for companies array in UDTF returnType.

    Returns:
        String like "struct<id:bigint,uuid:string,...>" for use in UDTF returnType
    """
    # Get DDL for Company
    ddl = get_company_ddl_string()

    # The simpleString() gives us "struct<...>" format
    # We need just the inner part for the array element type
    if ddl.startswith("struct<") and ddl.endswith(">"):
        # Extract the fields part
        fields_part = ddl[7:-1]  # Remove "struct<" and ">"
        return fields_part
    else:
        # If format is different, use as-is
        return ddl


def build_udtf_return_type() -> str:
    """Build complete UDTF returnType string dynamically.

    Returns:
        Complete returnType string for the SplitLargeBlocks UDTF
    """
    # Get the company struct fields
    company_struct = build_udtf_company_struct_string()

    # Build the complete return type - uses BLOCK_FIELDS for consistency
    return (
        f"block_key: string, block_key_type: string, "
        f"companies: array<struct<{company_struct}>>, "
        f"block_size: long"
    )


def get_block_fields() -> list[str]:
    """Get the expected field names for ER blocks.

    Returns:
        List of field names that should be present in block DataFrames/JSON.
        These match the BAML CompanyList type.
    """
    return BLOCK_FIELDS.copy()


def validate_block_schema(columns: list[str]) -> None:
    """Validate that a block DataFrame has the required fields.

    Args:
        columns: List of column names from a DataFrame

    Raises:
        ValueError: If required block fields are missing
    """
    required_fields = set(BLOCK_FIELDS)
    actual_fields = set(columns)
    missing_fields = required_fields - actual_fields

    if missing_fields:
        raise ValueError(
            f"Block schema validation failed. Missing required fields: {missing_fields}. "
            f"Expected fields: {BLOCK_FIELDS}. "
            f"Actual fields: {list(columns)}. "
            f"This is likely a bug in the ER pipeline - blocks must include all fields "
            f"from the BAML CompanyList type."
        )


def get_matches_schema() -> StructType:
    """Get the Spark schema for reading matches.jsonl files.

    The matches file contains blocks with resolved_companies arrays.
    This schema enforces correct BAML types when reading JSON.

    Returns:
        StructType schema for matches JSON file
    """
    company_schema = get_company_spark_schema()

    return StructType(
        [
            StructField("block_key", StringType(), True),
            StructField("block_key_type", StringType(), True),
            StructField("original_companies", ArrayType(company_schema), True),
            StructField("resolved_companies", ArrayType(company_schema), True),
            StructField("original_count", LongType(), True),
            StructField("resolved_count", LongType(), True),
            StructField("was_resolved", BooleanType(), True),
        ]
    )
