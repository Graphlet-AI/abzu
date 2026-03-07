"""Demonstrate the effect of Arrow optimization on list preservation."""

from typing import Any

import pandas as pd

from abzu.spark.config import get_spark_session


def test_arrow_optimization_effect() -> None:
    """Show how Arrow optimization affects Python lists."""

    # Create test data with lists
    test_data = {
        "id": [1, 2],
        "items": [["a", "b", "c"], ["d", "e"]],  # Python list  # Python list
        "numbers": [[1, 2, 3], [4, 5, 6]],
    }

    df = pd.DataFrame(test_data)
    print("Original pandas DataFrame:")
    print(f"  items[0] type: {type(df['items'].iloc[0])}")
    print(f"  items[0] value: {df['items'].iloc[0]}")
    print()

    # Test 1: With Arrow optimization ENABLED (default)
    print("=" * 60)
    print("TEST 1: Arrow Optimization ENABLED")
    print("=" * 60)

    spark1 = get_spark_session("TestArrowEnabled")
    spark1.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")  # Explicitly enable

    spark_df1 = spark1.createDataFrame(df)
    pdf_with_arrow = spark_df1.toPandas()

    first_items = pdf_with_arrow["items"].iloc[0]
    print("After round-trip with Arrow:")
    print(f"  items[0] type: {type(first_items)}")
    print(f"  items[0] value: {first_items}")
    print(f"  Has .tolist()? {hasattr(first_items, 'tolist')}")

    if hasattr(first_items, "tolist"):
        print("  → This is a NumPy array! ❌")
    else:
        print("  → This is a Python list! ✅")

    spark1.stop()
    print()

    # Test 2: With Arrow optimization DISABLED
    print("=" * 60)
    print("TEST 2: Arrow Optimization DISABLED")
    print("=" * 60)

    spark2 = get_spark_session("TestArrowDisabled")
    spark2.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")  # Disable Arrow

    spark_df2 = spark2.createDataFrame(df)
    pdf_without_arrow = spark_df2.toPandas()

    second_items = pdf_without_arrow["items"].iloc[0]
    print("After round-trip without Arrow:")
    print(f"  items[0] type: {type(second_items)}")
    print(f"  items[0] value: {second_items}")
    print(f"  Has .tolist()? {hasattr(second_items, 'tolist')}")

    if hasattr(second_items, "tolist"):
        print("  → This is a NumPy array! ❌")
    else:
        print("  → This is a Python list! ✅")

    spark2.stop()
    print()

    # Test 3: Show the practical impact
    print("=" * 60)
    print("PRACTICAL IMPACT")
    print("=" * 60)

    # Simulate what happens in BAML when it expects a list
    def simulate_baml_processing(items: list[Any]) -> list[Any] | None:
        """Simulate BAML expecting to call list.append()"""
        try:
            # BAML might try to do this
            items.append("new_item")
            print(f"✅ Successfully appended to {type(items)}")
            return items
        except AttributeError as e:
            print(f"❌ Failed: {e}")
            print(f"   (because {type(items)} doesn't have .append())")
            return None

    print("Simulating BAML processing:")
    print("  With Arrow (numpy array):")
    simulate_baml_processing(first_items.copy() if hasattr(first_items, "copy") else first_items[:])

    print("  Without Arrow (Python list):")
    simulate_baml_processing(
        second_items.copy() if hasattr(second_items, "copy") else second_items[:]
    )


if __name__ == "__main__":
    test_arrow_optimization_effect()
