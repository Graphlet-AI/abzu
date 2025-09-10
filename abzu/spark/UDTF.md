# PySpark UDTF (User-Defined Table Functions) Guide

## Overview

Python User-Defined Table Functions (UDTFs) in PySpark are functions that can return multiple rows and columns for each input row. Unlike UDFs which return a single value, UDTFs can generate zero or more output rows, making them powerful for data expansion operations.

## Basic UDTF Structure

### Using the @udtf Decorator (Recommended for PySpark 3.5+)

```python
from pyspark.sql.functions import udtf

@udtf(returnType="col1: string, col2: int")
class MyUDTF:
    def eval(self, input_value: str):
        # Process input and yield multiple rows
        for item in input_value.split(","):
            yield (item, len(item))
```

### Using F.udtf() (Alternative Pattern)

```python
from pyspark.sql import functions as F
from typing import Any

class _MyUDTF:
    def eval(self, input1: str, input2: list, input3: int):
        # Process and yield results
        yield (result1, result2, result3)

# Create the UDTF
MyUDTF: Any = F.udtf(
    returnType="output1: string, output2: array<string>, output3: int"
)(_MyUDTF)
```

## Calling UDTFs with DataFrames

### Method 1: Direct Call with Literal Values

```python
from pyspark.sql.functions import lit

# For @udtf decorated functions
result = MyUDTF(lit("hello,world")).show()
```

### Method 2: Using with DataFrame Columns

When using UDTFs created with `F.udtf()`, the correct pattern is:

```python
# CORRECT: Apply UDTF directly on DataFrame
result_df = MyUDTF(df.col1, df.col2, df.col3).alias("output1", "output2", "output3")

# Alternative: Using the UDTF in a select
result_df = df.select(MyUDTF(df.col1, df.col2).alias("out1", "out2"))
```

### Method 3: SQL Registration

```python
# Register the UDTF
spark.udtf.register("my_udtf", MyUDTF)

# Use in SQL
spark.sql("SELECT * FROM my_udtf('input_value')")
```

## Common Patterns and Best Practices

### 1. Splitting Large Collections

```python
class _SplitLargeBlocks:
    def eval(self, block_key: str, block_type: str, items: list, size: int):
        max_size = 50
        if size <= max_size:
            yield (block_key, block_type, items, size)
        else:
            chunk_num = 1
            for i in range(0, len(items), max_size):
                chunk = items[i:i + max_size]
                chunk_key = f"{block_key}_chunk_{chunk_num}"
                yield (chunk_key, block_type, chunk, len(chunk))
                chunk_num += 1

SplitLargeBlocks = F.udtf(
    returnType="block_key: string, block_type: string, items: array<struct<...>>, size: int"
)(_SplitLargeBlocks)

# Usage
result_df = df.select(
    SplitLargeBlocks(df.block_key, df.block_type, df.items, df.size)
    .alias("block_key", "block_type", "items", "size")
)
```

### 2. Expanding Nested Data

```python
@udtf(returnType="word: string, count: int")
class WordCounter:
    def eval(self, text: str):
        word_counts = {}
        for word in text.split():
            word_counts[word] = word_counts.get(word, 0) + 1
        for word, count in word_counts.items():
            yield (word, count)
```

### 3. Using terminate() for Aggregation

```python
@udtf(returnType="total: int, average: float")
class Aggregator:
    def __init__(self):
        self.sum = 0
        self.count = 0
    
    def eval(self, value: int):
        self.sum += value
        self.count += 1
        # Don't yield anything during eval
    
    def terminate(self):
        # Yield final results after processing all rows
        avg = self.sum / self.count if self.count > 0 else 0
        yield (self.sum, avg)
```

## Important Notes and Pitfalls

### 1. Column References in F.udtf() Pattern

When using `F.udtf()`, avoid using `F.col()` inside the UDTF call. Instead, reference DataFrame columns directly:

```python
# WRONG - This will cause "UNRESOLVED_COLUMN" error
df.select(
    MyUDTF(F.col("col1"), F.col("col2"))
)

# CORRECT
df.select(
    MyUDTF(df.col1, df.col2).alias("output1", "output2")
)
```

### 2. Single Column Returns

Always include a trailing comma when yielding a single column:

```python
def eval(self, input):
    yield (single_value,)  # Note the comma!
```

### 3. Return Type Specification

Be precise with return types, especially for complex structures:

```python
returnType=(
    "key: string, "
    "items: array<struct<id:string,name:string,value:int>>, "
    "count: int"
)
```

### 4. Performance Optimization

Enable Arrow optimization for better performance:

```python
@udtf(returnType="...", useArrow=True)
class OptimizedUDTF:
    ...
```

Or set globally:
```python
spark.conf.set("spark.sql.execution.pythonUDTF.arrow.enabled", "true")
```

## Complex Structure Example

For UDTFs that process complex nested structures (like in er_block.py):

```python
from pyspark.sql import functions as F
from typing import Any

class _ProcessComplexData:
    def eval(self, key: str, type: str, companies: list, size: int):
        # Process complex nested structures
        for company in companies:
            # Access nested fields
            company_name = company.name if hasattr(company, 'name') else company.get('name')
            yield (key, type, company_name, 1)

ProcessComplexData: Any = F.udtf(
    returnType=(
        "key: string, "
        "type: string, "
        "company_name: string, "
        "count: int"
    )
)(_ProcessComplexData)

# Usage - reference DataFrame columns directly
result = df.select(
    ProcessComplexData(df.key, df.type, df.companies, df.size)
    .alias("key", "type", "company_name", "count")
)
```

## Debugging Tips

1. **Check Column Names**: Ensure column names match exactly
2. **Verify Return Types**: Make sure the returnType matches what you're yielding
3. **Test with Small Data**: Start with a small DataFrame to verify logic
4. **Use printSchema()**: Check DataFrame schema before applying UDTF
5. **SQL Alternative**: If having issues, try registering and using via SQL

## References

- [Official PySpark UDTF Documentation](https://spark.apache.org/docs/latest/api/python/tutorial/sql/python_udtf.html)
- [PySpark SQL Functions API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)