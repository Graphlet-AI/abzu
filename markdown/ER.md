# Entity Resolution (ER) Pipeline Specification

This document describes the entity resolution pipeline for resolving duplicate company entities in the Abzu Capital knowledge graph.

## Overview

The ER pipeline operates in iterations, progressively merging duplicate company records. Each iteration consists of three steps:

1. **Block** - Group potentially similar companies together using blocking keys
2. **Match** - Use an LLM to determine which companies in each block are duplicates
3. **Eval** - Evaluate the results and prepare input for the next iteration

## Data Storage

**Format**: All ER data is stored exclusively in Parquet format for efficient processing with Spark.

**Location**: `data/er/iterations/{iteration}/`

## Pipeline Steps

### Step 1: Blocking

Two blocking strategies are available:

#### Name-Based Blocking (`abzu process er block names`)

Creates blocks using heuristic string matching:

- **First Word** - First word of normalized company name (e.g., "Apple" from "Apple Inc")
- **Acronym** - Uppercase letters from the name (e.g., "AI" from "Apple Inc")
- **Combined** - Companies that appear in both first_word and acronym blocks

**Output Files**:

- `combined_blocks.parquet` - Companies appearing in both blocking strategies (highest confidence)
- `first_word_blocks.parquet` - Companies blocked by first word only
- `acronym_blocks.parquet` - Companies blocked by acronym only
- `union_blocks.parquet` - Union of all three block types

**Example**:

```bash
abzu process er block names --iteration 1 -m 50
```

#### Semantic Blocking (`abzu process er block semantic`)

Creates blocks using FAISS IVF clustering on sentence embeddings:

- Uses `intfloat/multilingual-e5-base` embeddings by default
- Groups semantically similar company names regardless of string similarity
- Provides detailed analysis of cluster quality (cosine distance, Levenshtein metrics)

**Output Files**:

- `semantic_blocks.parquet` - Semantically clustered company blocks

**Options**:

- `--iteration N` - Iteration number
- `-t, --target-block-size N` - Target average block size (default: 50)
- `-d, --max-distance F` - Maximum cosine distance threshold (optional)
- `-b, --batch-size N` - Batch size for embedding computation

**Example**:

```bash
abzu process er block semantic --iteration 1 -t 50
```

#### Block Schema

```
block_key: string
block_key_type: string ("combined", "first_word", "acronym", "semantic")
companies: array<Company>
block_size: long
```

### Step 2: Matching (`abzu process er match`)

Uses an LLM to resolve each block, determining which companies are duplicates and merging them.

**Input**: By default, loads BOTH `union_blocks.parquet` AND `semantic_blocks.parquet` if they exist, combining them for matching.

**Output**: `matches.jsonl`

**Match Schema**:

```
block_key: string
block_key_type: string
resolved_companies: array<Company>
was_resolved: boolean
original_count: int
resolved_count: int
```

**Options**:

- `--iteration N` - Iteration number
- `-b, --batch-size N` - Blocks to process in parallel (default: 5)
- `-n, --limit N` - Limit number of blocks to process (for testing)
- `-s, --size-range MIN:MAX` - Only process blocks within size range
- `--name-blocks-only` - Only use name-based blocks
- `--semantic-blocks-only` - Only use semantic blocks

**Example**:

```bash
# Match using both name and semantic blocks
abzu process er match --iteration 1 -b 5

# Match using only semantic blocks
abzu process er match --iteration 1 --semantic-blocks-only
```

### Step 3: Evaluation (`abzu process er eval`)

Evaluates match results, computes metrics, and prepares resolved companies for the next iteration.

**Input**:

- `matches.jsonl` from matching step
- Original raw companies from `data/knowledge_graph/companies.parquet`

**Output**:

- `companies_resolved.parquet` - Resolved companies for next iteration
- `er_evaluation_metrics.parquet` - Evaluation metrics

**Metrics Computed**:

- Raw company count
- Resolved company count
- Data reduction percentage
- Source UUID coverage (tracking original company provenance)
- Source UUID validation (error rate)

**Example**:

```bash
abzu process er eval --iteration 1
```

## Source UUID Tracking

Throughout the ER pipeline, `source_uuids` tracks the provenance of merged companies:

- First iteration: Each company's UUID is added to its own `source_uuids`
- Subsequent iterations: When companies merge, all their `source_uuids` are combined
- This allows tracing any resolved company back to its original source records

## Multi-Iteration Workflow

Run multiple iterations until convergence:

```bash
# Iteration 1
abzu process er block names --iteration 1 -m 50
abzu process er block semantic --iteration 1 -t 50
abzu process er match --iteration 1 -b 5
abzu process er eval --iteration 1

# Iteration 2 (uses output from iteration 1)
abzu process er block names --iteration 2 -m 50
abzu process er block semantic --iteration 2 -t 50
abzu process er match --iteration 2 -b 5
abzu process er eval --iteration 2

# Continue until minimal reduction is achieved...
```

Or use the all-in-one command:

```bash
abzu process er all --iteration 1 -m 50 -b 5
```

## Cleanup

To clean up ER output files for a fresh run:

```bash
# Clean all iterations
abzu process er clean

# Clean specific iteration
abzu process er clean --iteration 1

# Dry run (show what would be deleted)
abzu process er clean --dry-run
```

## Configuration

ER paths are configured in `config.yml`:

```yaml
process:
  kg:
    er:
      paths:
        input: "${process.kg.raw.output}/companies.parquet"
        output: "${base_dir}/er/"
        blocks_dir: "${base_dir}/er/iterations/{iteration}/"
        blocks: "${base_dir}/er/iterations/{iteration}/union_blocks.parquet"
        semantic_blocks: "${base_dir}/er/iterations/{iteration}/semantic_blocks.parquet"
        matches: "${base_dir}/er/iterations/{iteration}/matches.jsonl"
        eval: "${base_dir}/er/iterations/{iteration}/companies_resolved.parquet"
      max_block_size: 50
      iteration: 3
      model:
        blocker: "intfloat/multilingual-e5-base"
```

## Testing

Test one iteration of the full pipeline:

```bash
# Block with small max size for testing
abzu process er block names --iteration 1 -m 30
abzu process er block semantic --iteration 1 -t 30

# Match with limited blocks for faster testing
abzu process er match --iteration 1 -b 5 -n 100

# Evaluate
abzu process er eval --iteration 1
```

## Key Implementation Files

- `abzu/spark/er_block.py` - Name-based blocking logic
- `abzu/spark/er_block_semantic.py` - Semantic blocking with FAISS
- `abzu/er/match.py` - LLM-based matching
- `abzu/spark/er_eval.py` - Evaluation and metrics
- `abzu/cli/process/er/` - CLI commands
