# Semantic Entity Resolution Blocking

When performing semantic entity resolution (SER) we use semantic clustering to reduce the number of comparisons needed to find matching entities in large datasets. This technique, known as blocking, groups similar entities together based on their semantic content, allowing for more efficient and accurate matching.

## Blocking Strategies

### Baseline: Name-Based Blocking

Before implementing semantic blocking, we use simple name-based blocking strategies as a baseline. These are computationally cheap and effective for catching obvious duplicates:

**First Word Blocking**: Extracts the first word of the normalized company name as the block key.

- "Apple Inc" → `APPLE`
- "Apple Corporation" → `APPLE`
- "Microsoft Corporation" → `MICROSOFT`

**Acronym Blocking**: Extracts uppercase letters from the company name as the block key.

- "International Business Machines" → `IBM`
- "Apple Inc" → `AI`
- "NVIDIA Corporation" → `NC`

**Combined Blocking**: Companies that appear in both first_word and acronym blocks are grouped together with higher confidence, as both strategies agree they should be compared.

The union of all three block types (`union_blocks.parquet`) is used for matching. This approach ensures:

- High recall by capturing matches through multiple strategies
- Prioritization of combined blocks (where both strategies agree)
- Manageable block sizes through chunking large blocks

### Semantic Blocking

Semantic clustering can use raw embeddings or fine-tuned embeddings (see https://github.com/Graphlet-AI/eridu) to create blocks of similar entities. The choice of embedding model can significantly impact the quality of the clusters and, consequently, the effectiveness of the blocking strategy.

### What to block

Modern embeddings are capable of blocking entire JSON records or individual fields within those records. The decision on what to block should be based on the specific use case and the nature of the data. For instance, blocking on company names and addresses may be effective for business entity resolution, while blocking on product descriptions may be more suitable for product matching tasks.

### Block Size

This is something that can be controlld through hyperparameters in the clustering algorithm. We need to keep these small to manage compute costs, but large enough to capture potential matches.

## Multiple Blocking Strategies

Implementing multiple blocking strategies (first word of name and acronym) as in `abzu process er block names` creates a challenge: the same entity can appear in multiple blocks, and each block independently produces a resolved output. This is known as the **multi-block output problem**.

### The Multi-Block Output Problem

When using union-based blocking (combining results from multiple blocking strategies), a single entity like "Meta Platforms, Inc." may appear in multiple blocks:

| Block Key | Block Type | Companies in Block                                |
| --------- | ---------- | ------------------------------------------------- |
| META      | first_word | Meta Platforms, Inc., Metaverse Labs              |
| MP        | acronym    | Meta Platforms, Inc., M3 Property, Magna PFV, ... |

Each block is processed independently by the matching step, and each produces its own resolved output with a **new UUID**:

- META block → Meta Platforms (UUID: `abc123...`)
- MP block → Meta Platforms (UUID: `def456...`)

The evaluation step's `distinct()` operation doesn't merge these because UUIDs differ, resulting in duplicate records in the final output with identical attributes but different UUIDs.

**Investigation Example (Iteration 5):**

```
Meta Platforms, Inc. | UUID: cd3c3576-5c22-4cc1-a3fa-7bb13c94e68f | 222 source_uuids
Meta Platforms, Inc. | UUID: 75ed538f-06c0-4fe9-9027-2085ec045757 | 222 source_uuids
```

### Historical Solutions

Entity resolution systems have developed several approaches to handle multi-block membership:

#### 1. Transitive Closure (Connected Components)

The most common approach treats match decisions as edges in a graph and computes connected components:

1. Create a graph where each record is a node
2. Add edges between records that match (from any block)
3. Compute connected components using Union-Find or graph traversal
4. Each component becomes one resolved entity

**Advantages:** Mathematically sound, handles chains of matches (A=B, B=C → A=C)
**Disadvantages:** Requires additional graph computation step, can create oversized clusters

#### 2. Block-Aware Deduplication

Deduplicate resolved outputs by identifying attributes rather than by UUID:

```python
# Instead of: resolved_df.distinct()
# Use: Group by identifying attributes and merge source_uuids
resolved_df.groupBy("name", "ticker", "headquarters_location")
    .agg(
        F.first("description").alias("description"),
        F.flatten(F.collect_list("source_uuids")).alias("source_uuids"),
        # ... other fields
    )
```

**Advantages:** Simple to implement, works within existing pipeline
**Disadvantages:** Requires choosing which attributes define identity

#### 3. Canonical Block Assignment

Assign each record to exactly ONE canonical block before matching:

1. When a record appears in multiple blocks, choose the "best" block based on:
   - Block size (prefer smaller blocks for precision)
   - Block type priority (e.g., combined > first_word > acronym)
   - Alphabetical ordering (deterministic tiebreaker)
2. Process only canonical assignments
3. No post-deduplication needed

**Advantages:** Prevents duplicates by design
**Disadvantages:** May miss matches if canonical block choice is wrong

#### 4. Two-Phase Resolution

Use blocking output as candidate pairs, then resolve globally:

**Phase 1 - Candidate Generation:**

- Run all blocking strategies
- Collect all (record_A, record_B) candidate pairs from blocks
- Deduplicate candidate pairs

**Phase 2 - Global Resolution:**

- Score all candidate pairs with matcher
- Build match graph from positive matches
- Compute transitive closure for final entities

**Advantages:** Clean separation of concerns, handles complex match chains
**Disadvantages:** More complex pipeline, higher memory requirements

### Recommended Fix for Abzu

For the current pipeline, **Block-Aware Deduplication** is the simplest fix. Add to `er_eval.py` after exploding resolved companies:

```python
# Deduplicate by name, merging source_uuids from different blocks
from pyspark.sql import functions as F

deduped_df = (
    resolved_companies_df
    .groupBy(F.lower(F.col("name")).alias("name_lower"))
    .agg(
        F.first("uuid").alias("uuid"),  # Keep one UUID
        F.first("name").alias("name"),
        F.first("ticker").alias("ticker"),
        F.first("description").alias("description"),
        F.first("headquarters_location").alias("headquarters_location"),
        # ... other scalar fields ...
        F.array_distinct(
            F.flatten(F.collect_list("source_uuids"))
        ).alias("source_uuids"),  # Merge all source_uuids
    )
    .drop("name_lower")
)
```

This would merge the two Meta Platforms records into one, combining their source_uuids arrays (222 + 222 = ~444 unique after dedup).

### Future Improvement: Transitive Closure

For more robust resolution, implement connected components:

1. After matching, create edges: `(source_uuid, resolved_uuid)` for each source→resolved mapping
2. Build a graph from all edges across all blocks
3. Compute connected components using GraphFrames or Spark GraphX
4. Each component = one final entity, with all source_uuids from all members

This handles complex cases like:

- A matches B in block 1
- B matches C in block 2
- Result: A, B, C are all the same entity (even if A and C never appeared in the same block)

## Embedding Code Audit (January 2026)

A critical review of the existing embedding-related code reveals significant issues that must be addressed before implementing semantic blocking.

### Current State of Embedding Code

#### 1. `abzu/er/blocker.py` - `E5EntityBlocker`

**Status: DEAD CODE - Not integrated into pipeline**

```python
class E5EntityBlocker:
    def __init__(self, model_name: str = "Qwen/Qwen3-Embedding-4B"):
        ...
```

**Issues:**

- Class name says "E5" but default model is `Qwen/Qwen3-Embedding-4B`
- Uses `AgglomerativeClustering` (O(n²)) instead of LSH (O(n))
- NOT called anywhere in `er_block.py` or the CLI
- The actual blocking pipeline (`abzu process er block names`) uses only heuristic strategies

#### 2. `abzu/kg/tickers.py` - `TickerMatcher`

**Status: Working but limited to ticker matching**

```python
class TickerMatcher:
    def __init__(self, model_name: str = "intfloat/e5-base-v2"):
        ...
```

**Issues:**

- Different default model than `E5EntityBlocker`
- Only used for SEC ticker→company matching, not ER
- Duplicates device detection logic from `blocker.py`

#### 3. `abzu/spark/er_block.py` - Actual Blocking Implementation

**Status: Production code, NO embeddings**

Uses only heuristic blocking:

- `get_first_word()` - extracts first word
- `get_acronym()` - extracts uppercase letters

No semantic/embedding-based blocking despite documentation suggesting otherwise.

### Model Inconsistencies

| Location             | Default Model                             | Purpose      |
| -------------------- | ----------------------------------------- | ------------ |
| `blocker.py`         | `Qwen/Qwen3-Embedding-4B`                 | ER (unused)  |
| `tickers.py`         | `intfloat/e5-base-v2`                     | Ticker match |
| `test_er_blocker.py` | `sentence-transformers/all-MiniLM-L6-v2`  | Tests        |
| User expectation     | `intfloat/multilingual-e5-large-instruct` | ER blocking  |

### Missing Components

1. **No LSH/Approximate Nearest Neighbors**

   - Current: `AgglomerativeClustering` - O(n²) pairwise comparisons
   - Needed: LSH, FAISS, or Annoy for scalable blocking
   - No `datasketch`, `faiss`, or `annoy` in dependencies

2. **No Integration with Pipeline**

   - `E5EntityBlocker.create_blocks()` exists but never called
   - `er_block.py` doesn't import or use any embedding utilities

3. **No Canonical Assignment**
   - Nothing prevents companies from appearing in multiple semantic blocks

## Semantic Blocking Implementation Plan

### Phase 1: Embedding Infrastructure

#### Device Detection Utility

Create shared utility in `abzu/utils.py`:

```python
from typing import Literal
import torch

def get_torch_device() -> Literal["cuda", "mps", "cpu"]:
    """Get the best available PyTorch device."""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"
```

#### Unified Embedding Model

Standardize on `intfloat/multilingual-e5-large-instruct` for all ER tasks:

```python
from sentence_transformers import SentenceTransformer

class CompanyEmbedder:
    """Embedding utility for company names using E5-large-instruct."""

    MODEL_NAME = "intfloat/multilingual-e5-large-instruct"
    INSTRUCTION = "Represent this company name for clustering similar entities: "

    def __init__(self):
        device = get_torch_device()
        self.model = SentenceTransformer(
            self.MODEL_NAME,
            device=device,
            model_kwargs={"device_map": "auto"}
        )

    def encode(self, names: list[str], batch_size: int = 64) -> np.ndarray:
        """Encode company names with instruction prefix."""
        # E5-instruct requires instruction prefix for best results
        texts = [f"{self.INSTRUCTION}{name}" for name in names]
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=batch_size,
        )
```

### Phase 2: FAISS IndexIVFFlat Blocking

Use FAISS `IndexIVFFlat` for scalable semantic blocking. IVF (Inverted File) partitions vectors into Voronoi cells using k-means clustering - each cluster IS a block:

```python
import faiss
import numpy as np

class FAISSBlocker:
    """FAISS IVF-based semantic blocking with controlled granularity."""

    def __init__(
        self,
        target_block_size: int = 50,
        min_block_size: int = 2,
        max_block_size: int = 100,
    ):
        self.target_block_size = target_block_size
        self.min_block_size = min_block_size
        self.max_block_size = max_block_size

    def create_blocks(
        self,
        embeddings: np.ndarray,
        company_uuids: list[str],
    ) -> dict[str, list[str]]:
        """Create blocks from embeddings using FAISS IVF clustering.

        Args:
            embeddings: Normalized embedding vectors (n x d)
            company_uuids: List of company UUIDs corresponding to embeddings

        Returns:
            Dict mapping block_key to list of company UUIDs
        """
        n = len(embeddings)
        d = embeddings.shape[1]

        # Calculate nlist based on target block size
        # Rule: nlist = n / target_block_size
        nlist = max(1, n // self.target_block_size)

        # FAISS recommendation: nlist shouldn't exceed sqrt(n) for small datasets
        nlist = min(nlist, int(np.sqrt(n)))
        nlist = max(nlist, 1)

        # Create IVF index with inner product (for normalized vectors)
        quantizer = faiss.IndexFlatIP(d)
        index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_INNER_PRODUCT)

        # Train and add vectors
        index.train(embeddings.astype(np.float32))
        index.add(embeddings.astype(np.float32))

        # Get cluster assignments for each vector
        _, assignments = quantizer.search(embeddings.astype(np.float32), 1)
        assignments = assignments.flatten()

        # Build initial blocks from cluster assignments
        raw_blocks: dict[int, list[str]] = {}
        for idx, cluster_id in enumerate(assignments):
            if cluster_id not in raw_blocks:
                raw_blocks[cluster_id] = []
            raw_blocks[cluster_id].append(company_uuids[idx])

        # Post-process: enforce min/max block size constraints
        final_blocks: dict[str, list[str]] = {}
        tiny_block_companies: list[str] = []

        for cluster_id, members in raw_blocks.items():
            if len(members) > self.max_block_size:
                # Split oversized blocks into chunks
                for i in range(0, len(members), self.max_block_size):
                    chunk = members[i:i + self.max_block_size]
                    final_blocks[f"semantic_{cluster_id}_chunk_{i // self.max_block_size}"] = chunk
            elif len(members) < self.min_block_size:
                # Collect tiny blocks for merging
                tiny_block_companies.extend(members)
            else:
                final_blocks[f"semantic_{cluster_id}"] = members

        # Merge tiny blocks into miscellaneous blocks
        if tiny_block_companies:
            for i in range(0, len(tiny_block_companies), self.max_block_size):
                chunk = tiny_block_companies[i:i + self.max_block_size]
                final_blocks[f"semantic_misc_{i // self.max_block_size}"] = chunk

        return final_blocks
```

#### Controlling Granularity

| Parameter           | Effect                                                      |
| ------------------- | ----------------------------------------------------------- |
| `target_block_size` | Average companies per block (controls `nlist = n / target`) |
| `min_block_size`    | Blocks smaller than this get merged into "misc" blocks      |
| `max_block_size`    | Blocks larger than this get split into chunks               |

#### Why FAISS IVFFlat over LSH?

1. **Native clustering**: IVF uses k-means, producing natural semantic clusters
2. **Granularity control**: Direct control via `nlist` parameter
3. **GPU acceleration**: `faiss-gpu` for large datasets
4. **Dense vector native**: No need to convert embeddings to MinHash signatures
5. **Battle-tested**: Used in production at Facebook/Meta scale

### Phase 3: Two-Stage Blocking Pipeline

Implement semantic blocking as a second stage after heuristic blocking:

```
Stage 1: Heuristic Blocking (existing)
├── First-word blocks
├── Acronym blocks
└── Combined blocks

Stage 2: Semantic Blocking (new)
├── Encode remaining unblocked/singleton companies
├── FAISS IVF clustering to create semantic blocks
└── Each company assigned to exactly ONE semantic block
```

### Phase 4: Pipeline Integration

#### New CLI Command

```bash
abzu process er block semantic --iteration 1 --target-block-size 50
```

#### Modified `er_block.py`

```python
def build_blocks(
    input_path: str,
    output_path: str,
    use_semantic: bool = False,
    target_block_size: int = 50,
    ...
):
    # Existing heuristic blocking
    ...

    if use_semantic:
        # Stage 2: Semantic blocking for singletons
        singleton_uuids = get_singleton_company_uuids(...)
        embedder = CompanyEmbedder()
        blocker = FAISSBlocker(target_block_size=target_block_size)

        # Encode and block
        singleton_names = get_names_for_uuids(singleton_uuids)
        embeddings = embedder.encode(singleton_names)
        semantic_blocks = blocker.create_blocks(embeddings, singleton_uuids)

        # Merge with heuristic blocks
        ...
```

### Phase 5: Evaluation Step Changes

Update `er_eval.py` to handle semantic blocks:

1. **Block-aware deduplication** (immediate fix)
2. **Track block_key_type in metrics** to measure heuristic vs semantic effectiveness
3. **Report semantic block statistics** separately

### Dependencies to Add

```toml
# pyproject.toml
faiss-cpu = ">=1.7.0"  # Or faiss-gpu for GPU acceleration
```

### Migration Path

1. **Immediate**: Remove dead `blocker.py` code (DONE)
2. **Short-term**: Implement `FAISSBlocker`, integrate into pipeline
3. **Medium-term**: Add semantic blocking CLI command
4. **Long-term**: Fine-tune embeddings using [Graphlet-AI/eridu](https://github.com/Graphlet-AI/eridu)
