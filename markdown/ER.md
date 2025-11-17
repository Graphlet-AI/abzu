# September 10, 2025 - Abzu Capital - Entity Resolution Run through Two Iterations

This file contains the results of two iterations of the entity resolution process for the Abzu Capital finance / technology knowledge graph. It shows each of the commands run and their output report at the end, as well as any relevant sampled data indicative of a problem or bug. Please read the debug output and reports that result from each command, compare the code for that command and the expected output with the actual output to determine any additional problems. Then figure out a plan for their resolution.

At the end there are notes and instructions on how to solve the problem. Take your time, read this file, inspect the relevant code, think hard, come up with a plan and add it to the end of this document under a heading `# Claude Code Plan`.

You can use the 'pyspark-mcp' server to run Spark to analyze the Company records that appear during the first `abzu process er block names --iteration 1` command and the second iteration command `abzu process er block names --iteration 2` to determine what about the Company schema changed to guide your investigation and diagnosis.

## Command: abzu process er clean

Removed all data in data/er/iterations/1 and 2

## Command: abzu process kg raw

```
2025-09-10 09:08:53,902 - abzu.spark.build_graph - INFO - Loaded 2,354 processed articles
25/09/10 09:08:54 WARN SparkStringUtils: Truncated the string representation of a plan since it was too large. This behavior can be adjusted by setting 'spark.sql.debug.maxToStringFields'.
2025-09-10 09:08:59,296 - abzu.spark.build_graph - INFO - 2,354 good articles. 0 bad articles.
2025-09-10 09:08:59,297 - abzu.spark.build_graph - INFO - Saved bad articles to data/knowledge_graph/bad_articles.jsonl, data/knowledge_graph/bad_articles.parquet, and data/knowledge_graph/bad_articles.csv
2025-09-10 09:08:59,297 - abzu.spark.build_graph - INFO - Replacing integer IDs with UUIDs for all entities...
2025-09-10 09:08:59,829 - abzu.spark.build_graph - INFO - Transformed 2,354 articles with UUID replacements
2025-09-10 09:08:59,829 - abzu.spark.build_graph - INFO - Extracting entities from documents ...
2025-09-10 09:08:59,829 - abzu.spark.build_graph - INFO - Extracting companies ...
2025-09-10 09:09:00,174 - abzu.spark.build_graph - INFO - After filtering nulls: 15,486 companies remain
2025-09-10 09:09:00,919 - abzu.spark.build_graph - INFO - Saved 15,486 companies to data/knowledge_graph/companies.parquet
2025-09-10 09:09:01,296 - abzu.spark.build_graph - INFO - Saved companies to data/knowledge_graph/companies.jsonl
2025-09-10 09:09:01,296 - abzu.spark.build_graph - INFO - Extracting products ...
2025-09-10 09:09:01,742 - abzu.spark.build_graph - INFO - Saved 6,242 products to data/knowledge_graph/products.parquet
2025-09-10 09:09:02,090 - abzu.spark.build_graph - INFO - Saved products to data/knowledge_graph/products.jsonl
2025-09-10 09:09:02,090 - abzu.spark.build_graph - INFO - Extracting technologies ...
2025-09-10 09:09:02,501 - abzu.spark.build_graph - INFO - Saved 10,978 technologies to data/knowledge_graph/technologies.parquet
2025-09-10 09:09:02,800 - abzu.spark.build_graph - INFO - Saved technologies to data/knowledge_graph/technologies.jsonl
2025-09-10 09:09:02,800 - abzu.spark.build_graph - INFO - Extracting tickers ...
2025-09-10 09:09:03,081 - abzu.spark.build_graph - INFO - Saved 1,702 tickers to data/knowledge_graph/tickers.parquet
2025-09-10 09:09:03,289 - abzu.spark.build_graph - INFO - Saved tickers to data/knowledge_graph/tickers.jsonl
2025-09-10 09:09:03,763 - abzu.spark.build_graph - INFO - Saved 4,962 relationships to data/knowledge_graph/relationships.parquet
2025-09-10 09:09:04,065 - abzu.spark.build_graph - INFO - Saved relationships to data/knowledge_graph/relationships.jsonl
2025-09-10 09:09:05,177 - abzu.spark.build_graph - INFO - Found 100.0% 4,962 valid relationships out of 4,962
```

## Command: abzu process er block names —iteration 1 # MAX_BLOCK_SIZE = 50

```
2025-09-10 09:29:20,295 - abzu.spark.er_block - INFO - Unified all_blocks: 5553 blocks, 21251 companies
2025-09-10 09:29:22,558 - abzu.spark.er_block - INFO - ============================================================
2025-09-10 09:29:22,558 - abzu.spark.er_block - INFO - ENTITY RESOLUTION BLOCKS CREATED
2025-09-10 09:29:22,558 - abzu.spark.er_block - INFO - ============================================================
2025-09-10 09:29:22,558 - abzu.spark.er_block - INFO - Combined Blocks (overlapping keys): 2,601 blocks with 12,564 companies
2025-09-10 09:29:22,558 - abzu.spark.er_block - INFO -   (Split from 2,522 original blocks)
2025-09-10 09:29:22,558 - abzu.spark.er_block - INFO -   Saved to: data/er/iterations/1/combined_blocks.json and data/er/iterations/1/combined_blocks.parquet
2025-09-10 09:29:22,558 - abzu.spark.er_block - INFO - First Word Only Blocks: 1,546 blocks with 3,898 companies
2025-09-10 09:29:22,559 - abzu.spark.er_block - INFO -   (Split from 1,536 original blocks)
2025-09-10 09:29:22,559 - abzu.spark.er_block - INFO -   Saved to: data/er/iterations/1/first_word_blocks.json and data/er/iterations/1/first_word_blocks.parquet
2025-09-10 09:29:22,559 - abzu.spark.er_block - INFO - Acronym Only Blocks: 1,406 blocks with 4,789 companies
2025-09-10 09:29:22,559 - abzu.spark.er_block - INFO -   (Split from 1,396 original blocks)
2025-09-10 09:29:22,559 - abzu.spark.er_block - INFO -   Saved to: data/er/iterations/1/acronym_blocks.json and data/er/iterations/1/acronym_blocks.parquet
2025-09-10 09:29:22,559 - abzu.spark.er_block - INFO - Total Blocks: 5,553 blocks (all blocks ≤ 50 companies)
2025-09-10 09:29:22,559 - abzu.spark.er_block - INFO - ============================================================
```

## Command: abzu process er match names -b 30 --iteration 1

```
2025-09-10 09:36:26,135 - abzu.er.match - INFO - Saved 2200 resolved blocks to data/er/iterations/1/matches.parquet
2025-09-10 09:36:26,227 - abzu.er.match - INFO -
Summary:
2025-09-10 09:36:26,227 - abzu.er.match - INFO -   Total blocks processed: 2200
2025-09-10 09:36:26,227 - abzu.er.match - INFO -   Successfully resolved: 2111
2025-09-10 09:36:26,227 - abzu.er.match - INFO -   Errors: 89
2025-09-10 09:36:26,227 - abzu.er.match - INFO -   Note: Resolved companies have new UUIDs; single-company blocks retain original UUIDs
2025-09-10 09:36:26,227 - abzu.er.match - INFO -   Total companies before: 15678.0
2025-09-10 09:36:26,227 - abzu.er.match - INFO -   Total companies after: 4557.0
2025-09-10 09:36:26,227 - abzu.er.match - INFO -   Reduction: 11121.0 companies merged
```

## Command: abzu process er eval names --iteration 1

```
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO - ENTITY RESOLUTION EVALUATION SUMMARY
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO - ============================================================
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO - Raw companies: 15,486 total, 15,416 unique
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO - Resolved companies: 6,915 total, 6,573 unique
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO - Data reduction: 8,913 companies (57.56%)
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO - New UUID verification: 2,016 UUIDs (13.08%) reuse raw UUIDs
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO - Source UUID coverage: 11,981/15,416 (77.72%)
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO - Source UUID validation: 15,524/15,541 valid (0.11% erroneous)
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO - Files saved:
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO -   - data/er/iterations/1/companies_resolved.parquet
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO -   - data/er/iterations/1/companies_resolved.json
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO -   - data/er/iterations/{iteration}/er_evaluation_metrics.parquet
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO -   - data/er/iterations/{iteration}/er_evaluation_metrics.json
2025-09-10 09:45:21,098 - abzu.spark.er_eval - INFO - ============================================================
```

## Command: abzu process er block names —iteration 2

```
2025-09-10 10:30:23,951 - abzu.spark.er_block - INFO - Unified all_blocks: 3380 blocks, 11301 companies
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO - ============================================================
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO - ENTITY RESOLUTION BLOCKS CREATED
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO - ============================================================
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO - Combined Blocks (overlapping keys): 903 blocks with 4,334 companies
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO -   (Split from 870 original blocks)
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO -   Saved to: data/er/iterations/2/combined_blocks.json and data/er/iterations/2/combined_blocks.parquet
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO - First Word Only Blocks: 1,422 blocks with 3,279 companies
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO -   (Split from 1,417 original blocks)
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO -   Saved to: data/er/iterations/2/first_word_blocks.json and data/er/iterations/2/first_word_blocks.parquet
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO - Acronym Only Blocks: 1,055 blocks with 3,688 companies
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO -   (Split from 1,052 original blocks)
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO -   Saved to: data/er/iterations/2/acronym_blocks.json and data/er/iterations/2/acronym_blocks.parquet
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO - Total Blocks: 3,380 blocks (all blocks ≤ 50 companies)
2025-09-10 10:30:26,159 - abzu.spark.er_block - INFO - ============================================================
```

The records for the second iteration of blocking still don’t match up to the expected schema, as indicated by "AAPL" in the "url" field and a name of "combined". We have seen this behavior before.

```json
{
  "block_key": "AAPL",
  "block_key_type": "combined",
  "companies": [
    {
      "uuid": "f5374f7b-1d66-42f2-a1b6-4d9e0b3ea284",
      "block_key": "AAPL",
      "block_key_type": "combined",
      "url": "AAPL",
      "name": "combined",
      "cik": "AAPL is likely referring to Apple Inc., a technology company that designs, develops, and sells consumer electronics, computer software, and online services. Apple Inc. is an American multinational technology company.",
      "id": 7,
      "posted_at": "AAPL",
      "ticker": {
        "symbol": "AAPL"
      }
    }
  ],
  "block_size": 1
}
```

These issues that arise during the second iteration blocking are due to a problem with the schema of the pyspark.sql.DataFrame we feed our UDTF on the second iteration, which is different than the first. See @UDTF.md and @abzu/spark/er_block.py lines 373 - 437:

```python
    @F.udtf(  # type: ignore
        returnType=(
            "block_key: string, block_key_type: string, "
            "companies: array<struct<uuid:string,block_key:string,block_key_type:string,"
            "url:string,name:string,description:string,ceo:string,cik:string,employees:long,"
            "founded_year:long,headquarters_location:string,id:long,jurisdiction:string,linkedin_url:string,"
            "posted_at:string,revenue_usd:long,source_ids:array<long>,source_uuids:array<string>,"
            "ticker:struct<exchange:string,id:long,name:string,symbol:string,uuid:string>,"
            "website_url:string>>, "
            "block_size: long"
        )
    )
    class SplitLargeBlocks:
        def eval(self, block_key: str, block_key_type: str, companies: list, block_size: int):
            if block_size <= MAX_BLOCK_SIZE:
                yield (block_key, block_key_type, companies, block_size)
            else:
                chunk_num = 1
                for i in range(0, len(companies), MAX_BLOCK_SIZE):
                    chunk_companies = companies[i : i + MAX_BLOCK_SIZE]
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
```

During the first iteration the schema is what this UDTF expects. During the second it is not. Our task is to fix the schema so that it is identical between the first and second runds.

## Command: abzu process er match names -b 20 --iteration 2

```
2025-09-10 10:47:20,520 - abzu.er.match - INFO - Saved 1549 resolved blocks to data/er/iterations/2/matches.parquet
2025-09-10 10:47:20,568 - abzu.er.match - INFO -
Summary:
2025-09-10 10:47:20,568 - abzu.er.match - INFO -   Total blocks processed: 1549
2025-09-10 10:47:20,568 - abzu.er.match - INFO -   Successfully resolved: 50
2025-09-10 10:47:20,568 - abzu.er.match - INFO -   Errors: 1499
2025-09-10 10:47:20,568 - abzu.er.match - INFO -   Note: Resolved companies have new UUIDs; single-company blocks retain original UUIDs
2025-09-10 10:47:20,568 - abzu.er.match - INFO -   Total companies before: 102.0
2025-09-10 10:47:20,568 - abzu.er.match - INFO -   Total companies after: 54.0
2025-09-10 10:47:20,568 - abzu.er.match - INFO -   Reduction: 48.0 companies merged
```

The records for the second iteration of matching still don’t match up to the expected - posted_at has name of ‘Google’ in it…

```json
{
  "uuid": "c5dc3d06-4293-46cb-a7c7-a4817d57845e",
  "block_key": "GOOGLE",
  "block_key_type": "combined",
  "url": "GOOGLE_chunk_6",
  "name": "combined",
  "description": null,
  "ceo": null,
  "cik": "A technology company known for its search engine, cloud computing, and artificial intelligence research.",
  "employees": null,
  "founded_year": null,
  "headquarters_location": null,
  "id": 103,
  "jurisdiction": null,
  "linkedin_url": null,
  "posted_at": "Google",
  "revenue_usd": null,
  "source_ids": null,
  "source_uuids": null,
  "ticker": null,
  "website_url": "<https://techcrunch.com/2025/07/14/mark-zuckerberg-says-meta-is-building-a-5gw-ai-data-center/>"
}
```

## Command: abzu process er eval names --iteration 2

2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - ENTITY RESOLUTION EVALUATION SUMMARY
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - ============================================================
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - Raw companies: 15,486 total, 15,416 unique
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - Resolved companies: 9,901 total, 6,021 unique
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - Data reduction: 9,465 companies (61.12%)
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - New UUID verification: 2,016 UUIDs (13.08%) reuse raw UUIDs
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - Source UUID coverage: 234/15,416 (1.52%)
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - Source UUID validation: 0/1,980 valid (100.00% erroneous)
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - Files saved:
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - - data/er/iterations/2/companies_resolved.parquet
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - - data/er/iterations/2/companies_resolved.json
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - - data/er/iterations/{iteration}/er_evaluation_metrics.parquet
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - - data/er/iterations/{iteration}/er_evaluation_metrics.json
2025-09-10 11:19:30,226 - abzu.spark.er_eval - INFO - ============================================================

# Claude Code Plan

Claude Code, put your plan to fix these issues here...
