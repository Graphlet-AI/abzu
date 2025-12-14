class DuplicateCompanyGroup {
   @@description("A group of duplicate companies with the same UUID that need to be merged.")
   uuid string @description("The UUID shared by all duplicates in this group.")
   duplicate_companies Company[] @description("All duplicate company records that share this UUID.")
   match_block_keys string[] @description("All block_keys where these duplicates appeared.")
}

class ResolvedCompany {
   @@description("A single merged company record resolved from duplicates.")
   company Company @description("The final merged company with best values from all duplicates.")
}

function FinalEntityResolution(duplicate_group: DuplicateCompanyGroup) -> ResolvedCompany {
  // see clients.baml
  client Gemini25FlashLite

  // The prompt uses Jinja syntax
  prompt #"
    You are resolving duplicate company records that share the same UUID but appeared in different blocking strategies or blocks. Your task is to merge these duplicates into a single, highest-quality record.

    IMPORTANT UUID HANDLING: The output Company MUST preserve the UUID from the input duplicate_group.uuid field. All duplicate companies in the input have the same UUID - you must use this UUID in the output, NOT create a new one.

    MERGING STRATEGY:
    For each field in the Company record, choose the BEST value from all the duplicate records based on these criteria:

    1. **Name**: Choose the most complete and formal company name (with organization type like Inc., Corp., Ltd.)
    2. **Ticker**: Prefer records with valid ticker symbols and exchange information
    3. **Description**: Choose the longest, most detailed, and informative description
    4. **Contact/Location Data**: Prefer non-null values; if multiple exist, choose the most specific/complete
    5. **Financial Data**: Prefer non-null numeric values (revenue_usd, employees, founded_year, etc.)
    6. **URLs**: Prefer non-null website_url, linkedin_url values
    7. **Arrays (source_uuids, source_ids, match_skip_history)**: MERGE all values from all duplicates, remove duplicates, and sort

    BLOCK TRACKING:
    The duplicate_group.match_block_keys array contains all the block_keys where these duplicates appeared. This is informational context - you don't need to output it, but it helps explain why you're seeing duplicates.

    OUTPUT REQUIREMENTS:
    - Return a single Company record with the uuid set to duplicate_group.uuid
    - Combine source_uuids arrays from all duplicates (flatten, deduplicate, sort)
    - Combine source_ids arrays from all duplicates (flatten, deduplicate, sort)
    - Combine match_skip_history arrays from all duplicates (flatten, deduplicate, sort)
    - For all other fields, select the BEST value as described above

    {# special macro to print the output instructions. #}
    {{ ctx.output_format(hoist_classes=["Company", "Ticker", "ResolvedCompany"]) }}

    {{ _.role("user") }}

    UUID: {{ duplicate_group.uuid }}
    Number of duplicates: {{ duplicate_group.duplicate_companies|length }}
    Block keys where found: {{ duplicate_group.match_block_keys }}

    Duplicate Companies to Merge:
    {% for company in duplicate_group.duplicate_companies %}
    {{ company }}
    {% endfor %}
  "#
}

test TwoDuplicatesTest {
  functions [FinalEntityResolution]
  args {
    duplicate_group {
      uuid "test-uuid-123"
      match_block_keys ["APPLE", "AAPL_ACRONYM"]
      duplicate_companies [
        {
          id 0
          uuid "test-uuid-123"
          name "Apple Inc."
          ticker {
            id 0
            uuid null
            exchange "NASDAQ"
            symbol "AAPL"
          }
          description "Technology company"
          founded_year 1976
          source_uuids ["source-1", "source-2"]
          match_skip_history null
        }
        {
          id 1
          uuid "test-uuid-123"
          name "Apple"
          ticker {
            id 1
            uuid null
            symbol "AAPL"
          }
          description "Apple Inc. is an American multinational corporation and technology company headquartered in Cupertino, California. Founded in 1976, the company is known for consumer electronics, software, and online services."
          headquarters_location "Cupertino, CA"
          revenue_usd 394328000000
          employees 164000
          source_uuids ["source-3", "source-4"]
          match_skip_history [1]
        }
      ]
    }
  }
}

test ThreeDuplicatesWithNullsTest {
  functions [FinalEntityResolution]
  args {
    duplicate_group {
      uuid "nvidia-uuid-456"
      match_block_keys ["NVIDIA", "NVDA_ACRONYM", "NVIDIA_COMBINED"]
      duplicate_companies [
        {
          id 0
          uuid "nvidia-uuid-456"
          name "Nvidia"
          ticker null
          description "GPU manufacturer"
          source_uuids ["doc-1"]
          match_skip_history null
        }
        {
          id 1
          uuid "nvidia-uuid-456"
          name "NVIDIA Corp"
          ticker {
            id 0
            uuid null
            symbol "NVDA"
            exchange "NASDAQ"
          }
          description null
          headquarters_location "Santa Clara, CA"
          founded_year 1993
          source_uuids ["doc-2", "doc-3"]
          match_skip_history [1, 2]
        }
        {
          id 2
          uuid "nvidia-uuid-456"
          name "Nvidia Corporation"
          ticker {
            id 1
            uuid null
            symbol "NVDA"
          }
          description "Nvidia Corporation is a leading technology company specializing in graphics processing units (GPUs) and artificial intelligence computing platforms."
          revenue_usd 60922000000
          employees 29600
          ceo "Jensen Huang"
          source_uuids ["doc-4"]
          match_skip_history [2]
        }
      ]
    }
  }
}
