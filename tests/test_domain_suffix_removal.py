"""Unit tests for domain suffix removal in entity resolution blocking."""

import pytest
from pyspark.sql import SparkSession

from abzu.spark.er_block import remove_domain_suffix


@pytest.fixture(scope="module")
def spark():
    """Create a SparkSession for testing."""
    spark = (
        SparkSession.builder.master("local[1]")  # type: ignore[attr-defined]
        .appName("test_domain_suffix")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield spark
    spark.stop()


def test_remove_domain_suffix_basic():
    """Test basic domain suffix removal."""
    # Should remove known domain suffixes
    assert remove_domain_suffix("Google.com") == "Google"
    assert remove_domain_suffix("Microsoft.org") == "Microsoft"
    assert remove_domain_suffix("Apple.net") == "Apple"
    assert remove_domain_suffix("Example.io") == "Example"
    assert remove_domain_suffix("Startup.ai") == "Startup"


def test_remove_domain_suffix_preserves_legitimate_periods():
    """Test that legitimate periods in company names are preserved."""
    # Should NOT remove periods that are not domain suffixes
    assert remove_domain_suffix("St. Jude Medical") == "St. Jude Medical"
    assert remove_domain_suffix("Dr. Pepper") == "Dr. Pepper"
    assert remove_domain_suffix("A.P. Moller") == "A.P. Moller"
    assert remove_domain_suffix("H&M Hennes & Mauritz AB") == "H&M Hennes & Mauritz AB"
    assert remove_domain_suffix("L.L.Bean") == "L.L.Bean"


def test_remove_domain_suffix_case_insensitive():
    """Test that domain suffix removal is case-insensitive."""
    assert remove_domain_suffix("Example.COM") == "Example"
    assert remove_domain_suffix("Example.Com") == "Example"
    assert remove_domain_suffix("Example.ORG") == "Example"
    assert remove_domain_suffix("Example.Org") == "Example"


def test_remove_domain_suffix_no_suffix():
    """Test handling of names without domain suffixes."""
    assert remove_domain_suffix("Microsoft Corporation") == "Microsoft Corporation"
    assert remove_domain_suffix("Apple Inc") == "Apple Inc"
    assert remove_domain_suffix("Amazon") == "Amazon"


def test_remove_domain_suffix_country_codes():
    """Test removal of country code domain suffixes."""
    assert remove_domain_suffix("Example.uk") == "Example"
    assert remove_domain_suffix("Example.ca") == "Example"
    assert remove_domain_suffix("Example.au") == "Example"
    assert remove_domain_suffix("Example.de") == "Example"
    assert remove_domain_suffix("Example.jp") == "Example"


def test_remove_domain_suffix_special_tlds():
    """Test removal of special TLD suffixes."""
    assert remove_domain_suffix("Example.biz") == "Example"
    assert remove_domain_suffix("Example.info") == "Example"
    assert remove_domain_suffix("Example.museum") == "Example"
    assert remove_domain_suffix("Example.coop") == "Example"


def test_remove_domain_suffix_edge_cases():
    """Test edge cases."""
    # Empty string
    assert remove_domain_suffix("") == ""
    # Just a domain suffix
    assert remove_domain_suffix(".com") == ""
    # Trailing period but not a domain suffix
    assert remove_domain_suffix("Example Corp.") == "Example Corp."
    # Multiple periods with domain suffix at end
    assert remove_domain_suffix("St. John's Corp.com") == "St. John's Corp"
    # Domain suffix in middle of name (should NOT be removed)
    assert remove_domain_suffix("Company.com Inc") == "Company.com Inc"
    assert remove_domain_suffix("Tech.io Ltd") == "Tech.io Ltd"
    # Domain suffix at end (should be removed)
    assert remove_domain_suffix("Example.com") == "Example"
    assert remove_domain_suffix("Startup.io") == "Startup"


def test_get_first_word_with_periods(spark):
    """Test that get_first_word preserves legitimate periods."""
    from pyspark.sql import functions as F

    from abzu.spark.er_block import get_first_word

    # Create test DataFrame
    test_data = [
        ("St. Jude Medical",),
        ("Dr. Pepper Company",),
        ("Google.com",),
        ("A.P. Moller - Maersk",),
    ]
    df = spark.createDataFrame(test_data, ["name"])

    # Apply the UDF
    result_df = df.withColumn("first_word", get_first_word(F.col("name")))
    results = result_df.collect()

    # Check results
    assert results[0]["first_word"] == "ST."  # Preserves period in "St."
    assert results[1]["first_word"] == "DR."  # Preserves period in "Dr."
    assert results[2]["first_word"] == "GOOGLE"  # Removes .com suffix
    assert results[3]["first_word"] == "A.P."  # Preserves periods in "A.P."


def test_get_acronym_with_periods(spark):
    """Test that get_acronym handles periods correctly."""
    from pyspark.sql import functions as F

    from abzu.spark.er_block import get_acronym

    # Create test DataFrame
    test_data = [
        ("St. Jude Medical",),
        ("Google.com",),
        ("International Business Machines.net",),
    ]
    df = spark.createDataFrame(test_data, ["name"])

    # Apply the UDF
    result_df = df.withColumn("acronym", get_acronym(F.col("name")))
    results = result_df.collect()

    # St. Jude Medical should generate SJM acronym
    assert results[0]["acronym"] == "SJM"
    # Google.com should remove .com and get first word
    assert results[1]["acronym"] == "GOOGLE"
    # IBM should generate IBM acronym after removing .net
    assert results[2]["acronym"] == "IBM"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
