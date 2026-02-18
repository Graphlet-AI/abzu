// Edge Resolution: Merging duplicate relationships between the same pair of resolved companies.
// After node entity resolution, multiple edges of the same or related types may exist
// between the same pair of nodes. This module merges them using LLM-based reasoning.

// Existing class for article-level merged relationships (used by article processing)
class MergedRelationship {
  src int
  @description("Source company id in the deal.")

  dst int
  @description("Target company id in the deal.")

  type RelationshipType

  technologies int[]?
  @description("Technology ids involved in the deal.")

  products int[]?
  @description("Product ids involved in the deal.")

  descriptions string

  percentage float?
  @description("Percentage of ownership or involvement in the deal.")

  amount float?
  @description("Currency. Expand millions, billions or trillions to whole figures.")

  currency string?
  @description("ISO 4217 3-letter currency code")

  country Nation?
  @description("Country where the relationship occurs. Sometimes articles announce investments made by companies in specific countries.")

  date string?
  @description("Date of the relationship in ISO-8601 format")

  quarter string?
  @description("Actual or projected financial quarter of the deal in ISO-8601 format. This is the quarter of the year when a relationship took place or will take place.")

  contract_duration_years int?
  @description("Contract term if applicable")

  segment_ids int[]?
  @description("Business segment IDs where relationship applies")

  geographic_scope string?
  @description("Geographic scope of relationship")

  is_material bool?
  @description("Whether relationship is material to business")
}

// --- Edge Resolution Types ---

// Input: A single relationship to be potentially merged with others
class EdgeRelationshipInput {
  type string
  @description("Relationship type (e.g., Supplier, Acquisition, Investment)")

  description string
  @description("Description of the relationship")

  amount float?
  @description("Monetary amount involved")

  currency string?
  @description("ISO 4217 3-letter currency code")

  date string?
  @description("Date of the relationship in ISO-8601 format")

  percentage float?
  @description("Percentage of ownership or involvement")

  quarter string?
  @description("Financial quarter in ISO-8601 format")

  url string?
  @description("Source article URL")
}

// Input: Block of relationships between the same (src, dst) company pair
class EdgeBlock {
  src_name string
  @description("Name of the source company")

  dst_name string
  @description("Name of the destination company")

  relationships EdgeRelationshipInput[]
  @description("All relationships between these two companies to be merged")

  block_size int
  @description("Number of relationships in this block")
}

// Output: A merged relationship combining duplicates
class MergedEdgeRelationship {
  type string
  @description("The relationship type that best describes this merged relationship")

  description string
  @description("Combined description summarizing all merged relationships")

  amount float?
  @description("Best monetary amount (use most specific/recent)")

  currency string?
  @description("ISO 4217 3-letter currency code")

  date string?
  @description("Most specific/recent date in ISO-8601 format")

  percentage float?
  @description("Percentage of ownership or involvement")

  quarter string?
  @description("Financial quarter in ISO-8601 format")
}

// Output: Result of edge resolution for one block
class EdgeResolutionResult {
  merged_relationships MergedEdgeRelationship[]
  @description("The merged relationships after deduplication")

  was_resolved bool
  @description("Whether any merging was performed")

  original_count int
  @description("Number of input relationships")

  resolved_count int
  @description("Number of output relationships after merging")
}

function ResolveEdgeBlock(block: EdgeBlock) -> EdgeResolutionResult {
  client Gemini20Flash

  prompt #"
    You are merging duplicate business relationships between two companies.

    Source Company: {{ block.src_name }}
    Target Company: {{ block.dst_name }}

    Relationships to merge ({{ block.block_size }} total):
    {% for rel in block.relationships %}
    {{ loop.index }}. {{ rel.type }}: {{ rel.description }}
       {% if rel.amount %}Amount: {{ rel.amount }}{% if rel.currency %} {{ rel.currency }}{% endif %}{% endif %}
       {% if rel.date %}Date: {{ rel.date }}{% endif %}
       {% if rel.percentage %}Ownership: {{ rel.percentage }}%{% endif %}
       {% if rel.quarter %}Quarter: {{ rel.quarter }}{% endif %}
       {% if rel.url %}Source: {{ rel.url }}{% endif %}
    {% endfor %}

    Rules:
    1. Merge relationships that describe the SAME business deal or event
    2. Different relationship types CAN be merged if they describe the same deal
       (e.g., "Supplier" + "SupplyAgreement" for same contract)
    3. Combine descriptions into a coherent summary
    4. Use the most specific or recent date
    5. Use the largest amount (later reports often refine earlier estimates)
    6. Keep distinct relationships separate (different deals = different edges)

    {{ ctx.output_format }}
  "#
}

test ResolveEdgeBlock_duplicate_investments {
  functions [ResolveEdgeBlock]
  args {
    block {
      src_name "SoftBank"
      dst_name "OpenAI"
      relationships [
        {
          type "Investment"
          description "SoftBank invested in OpenAI"
          amount 500000000
          currency "USD"
          date "2024-01-15"
          url "https://example.com/article1"
        }
        {
          type "Investment"
          description "SoftBank made a $500M investment in OpenAI as part of a funding round"
          amount 500000000
          currency "USD"
          date "2024-01-16"
          url "https://example.com/article2"
        }
        {
          type "Financing"
          description "SoftBank financed OpenAI's latest funding round"
          amount 500000000
          currency "USD"
          date "2024-01-15"
          url "https://example.com/article3"
        }
      ]
      block_size 3
    }
  }
}

test ResolveEdgeBlock_distinct_relationships {
  functions [ResolveEdgeBlock]
  args {
    block {
      src_name "NVIDIA"
      dst_name "TSMC"
      relationships [
        {
          type "Supplier"
          description "TSMC manufactures chips for NVIDIA"
          date "2023-06-01"
        }
        {
          type "SupplyAgreement"
          description "NVIDIA and TSMC signed a long-term chip manufacturing agreement"
          date "2023-06-15"
        }
        {
          type "Investment"
          description "NVIDIA invested in TSMC's advanced packaging technology"
          amount 100000000
          currency "USD"
          date "2024-03-01"
        }
      ]
      block_size 3
    }
  }
}
