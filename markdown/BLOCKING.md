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

Implementing multiple blocking strategies (first word of name and acroym) as in 'abzu process er block names' creates a challenge introduced by using two name based blocking strategies (first word and acronym). Each strategy generates its own golden record in a block and we must then block on `uuid` or `name` to reduce records down to a single golden record.

This is the purpose of the `abzu process er final` step, which uses `uuid` and `name` blocking to group records from the union of name based blocks into final blocks for matching.
