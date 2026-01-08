# Semantic Entity Resolution Blocking

When performing semantic entity resolution (SER) we use semantic clustering to reduce the number of comparisons needed to find matching entities in large datasets. This technique, known as blocking, groups similar entities together based on their semantic content, allowing for more efficient and accurate matching.

## Baseline Heuristic Blocking: Name-Based

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

### Baseline Code

See: @abzu/spark/er_block.py - for the baseline heuristic blocking implementation.

**Status: Production code, NO embeddings**

Uses only heuristic blocking:

- `get_first_word()` - extracts first word
- `get_acronym()` - extracts uppercase letters

No semantic/embedding-based blocking despite documentation suggesting otherwise.

## Semantic Blocking

Semantic clustering can use raw embeddings or fine-tuned embeddings (see <https://github.com/Graphlet-AI/eridu>) to create blocks of similar entities. The choice of embedding model can significantly impact the quality of the clusters and, consequently, the effectiveness of the blocking strategy.

We will use FAISS with `IndexIVFFlat` and A-KNN (approximate nearest neighbors) for semantic blocking. This approach provides scalable clustering with controlled granularity.

### Device Detection Utility

Create shared utility in @abzu/utils.py:

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

### Phase 1: Embedding Records

Standardize on `intfloat/multilingual-e5-base/large` for all ER tasks, as it performs much better at fine-tuning than Qwen series of models which indicates good representation quality.

See: `CompanyEmbedder` in @abzu/er/embeddings.py

### Phase 2: FAISS IndexIVFFlat Blocking

We use [FAISS](https://github.com/facebookresearch/faiss) `IndexIVFFlat` for scalable semantic blocking. IVF (Inverted File) partitions vectors into Voronoi cells using k-means clustering - each cluster IS a block in @abzu/er/faiss.py.

#### Controlling Clustering Granularity

| Parameter           | Effect                                                      |
| ------------------- | ----------------------------------------------------------- |
| `target_block_size` | Average companies per block (controls `nlist = n / target`) |
| `max_distance`      | Maximum distance threshold for clustering (optional)        |

#### Why FAISS IVFFlat over LSH?

1. **Native clustering**: IVF uses k-means, producing natural semantic clusters
2. **Granularity control**: Direct control via `nlist` parameter
3. **GPU acceleration**: `faiss-gpu` for large datasets
4. **Dense vector native**: No need to convert embeddings to MinHash signatures
5. **Battle-tested**: Used in production at Facebook/Meta scale

### Phase 3: Evaluation Step Changes

Update `er_eval.py` to handle semantic blocks.

### Dependencies to Add

```toml
# pyproject.toml
faiss-cpu = ">=1.13.2"  # Or faiss-gpu for GPU acceleration
```

### Phase 4: Eridu Fine-Tuning (Long-term)

Fine-tune embeddings using [Graphlet-AI/eridu](https://github.com/Graphlet-AI/eridu) for improved clustering performance.
