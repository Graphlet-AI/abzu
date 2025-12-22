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

### Step 1: Blocking (`abzu process er block names`)

Creates blocks of potentially matching companies using multiple blocking strategies:

- **First Word** - First word of normalized company name (e.g., "Apple" from "Apple Inc")
- **Acronym** - Uppercase letters from the name (e.g., "AI" from "Apple Inc")
- **Combined** - Companies that appear in both first_word and acronym blocks

**Output Files**:

- `combined_blocks.parquet` - Companies appearing in both blocking strategies (highest confidence)
- `first_word_blocks.parquet` - Companies blocked by first word only
- `acronym_blocks.parquet` - Companies blocked by acronym only
- `union_blocks.parquet` - Union of all three block types (used for matching)

**Block Schema**:

```
block_key: string
block_key_type: string ("combined", "first_word", "acronym")
companies: array<Company>
block_size: long
```

**Options**:

- `--iteration N` - Iteration number (required)
- `-m, --max-block-size N` - Maximum companies per block (default: 50)

**Example**:

```bash
abzu process er block names --iteration 1 -m 50
```

### Step 2: Matching (`abzu process er match names`)

Uses an LLM to resolve each block, determining which companies are duplicates and merging them.

**Input**: `union_blocks.parquet` from blocking step

**Output**: `matches.parquet`

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

- `--iteration N` - Iteration number (required)
- `-b, --batch-size N` - Blocks to process in parallel (default: 50)
- `-n, --num-rows N` - Limit number of blocks to process (for testing)

**Example**:

```bash
abzu process er match names --iteration 1 -b 50
```

### Step 3: Evaluation (`abzu process er eval names`)

Evaluates match results, computes metrics, and prepares resolved companies for the next iteration.

**Input**:

- `matches.parquet` from matching step
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
abzu process er eval names --iteration 1
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
abzu process er match names --iteration 1 -b 50
abzu process er eval names --iteration 1

# Iteration 2 (uses output from iteration 1)
abzu process er block names --iteration 2 -m 50
abzu process er match names --iteration 2 -b 50
abzu process er eval names --iteration 2

# Continue until minimal reduction is achieved...
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
        names:
          blocks_dir: "${base_dir}/er/iterations/{iteration}/"
          blocks: "${base_dir}/er/iterations/{iteration}/union_blocks.{format}"
          matches: "${base_dir}/er/iterations/{iteration}/matches.{format}"
          final: "${base_dir}/er/iterations/{iteration}/companies_final.{format}"
          eval: "${base_dir}/er/iterations/{iteration}/companies_resolved.{format}"
      max_block_size: 50
      iteration: 3
```

## Testing

Test one iteration of the full pipeline:

```bash
# Block with small max size for testing
abzu process er block names --iteration 1 -m 30

# Match with limited rows for faster testing
abzu process er match names --iteration 1 -b 50 -n 100

# Evaluate
abzu process er eval names --iteration 1
```

## Key Implementation Files

- `abzu/spark/er_block.py` - Blocking logic
- `abzu/er/match.py` - LLM-based matching
- `abzu/spark/er_eval.py` - Evaluation and metrics
- `abzu/spark/er_final.py` - Final company consolidation
- `abzu/cli/process/er/` - CLI commands
