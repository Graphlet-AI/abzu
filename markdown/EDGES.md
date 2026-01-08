# Edge Resolution - Merging Duplicate Edge Types Between Two Nodes

In knowledge graphs, following node entity resolution, it is common to have multiple edges of the same type representing the same relationship between the same pair of nodes. To maintain a clean and efficient graph structure, we need to merge these duplicate edges into a single representative edge. We develop operators to handle this edge resolution process.

## Edge Resolution Strategy

1. Convert BAML schema from `src_company` / `dst_company` to `src` / `dst` to generalize for any node types. Make sure to update all relevant code and documentation and regenerate BAML Python files.
2. Create a CLI command `abzu process er edges merge` to perform edge resolution.
3. Create a CLI command `abzu process er eval` to evaluate edge resolution quality.
4. Compute a report as part of `abzu process er eval` to summarize raw duplicate edge statistics.
5. Create a `MergedRelationship` BAML data model to represent merged edges with aggregated attributes. Use signatures to provide metadata about the merging process. Deduplication can occur in edge properties.
6. Implement merging logic that combines duplicate edges based on defined criteria (e.g., same source, destination, and edge type). Aggregate attributes such as weights, timestamps, or other relevant properties.
7. Ensure that the merged edges maintain referential integrity with the source and destination nodes.
