class CompanyList {
   block_key string? @description("The blocking key used to merge records.")
   block_key_type string? @description("The blocking strategy this block key comes from.")
   block_size int? @description("The number of records merged by entity resolution.")   
   companies Company[]
}

function MultiEntityResolution(company_list: CompanyList) -> CompanyList {
  // see clients.baml
  client Gemini20Flash

  // The prompt uses Jinja syntax. Change the models or this text and watch the prompt preview change!
  prompt #"
    Examine the following set of companies and determine which ones are the same entity. If two or more companies are the same, merge them and return the resolved company with all combined attributes filled out. If a record has a valid field and the other doesn't, add it. Consider both the company name and description when making matches. If there are multiple company descriptions, rewrite the description to summarize them into a single description of less than 60 words. Keep track of the source companies and their attributes throughout the process. 
    
    IMPORTANT UUID HANDLING: When merging companies, you MUST collect ALL the Company.uuid values from the input companies and store them in the Company.source_uuids field of the Companies in the output CompanyList. For example, if merging two companies with uuids 'abc-123' and 'def-456', the output source_uuids should be ['abc-123', 'def-456']. Always populate source_uuids with the input UUIDs - never leave it null if the input companies have UUIDs. The merged record should have uuid set to null (it will get a new UUID assigned later). If there are already UUIDs in Company.source_uuids then preserve them and append the merged Company.uuid values to the existing list.
    
    Choose the most complete corporate name when merging names, including the organization type ending. Company names without organization types can be merged with those that have them. Company names with different corporate endings are probably not the same company, depending on the description. Input records with the same UUID should be merged and only one UUID should be added to 'source_uuids'. Skip all NULL fields that would be in the input and output data, unless they are REQUIRED. If there is only 1 company in the input (no merging needed), copy its uuid to source_uuids and set the output Company.uuid to the value of the input Company.uuid. Make sure all Company records have a valid integer 'id' field and valid UUID 'uuid' field.

    Return a merged set of companies with all combined attributes from the source companies filled out.

    {# special macro to print the output instructions. #}
    {{ ctx.output_format(hoist_classes=["Company", "Ticker", "CompanyList"]) }}

    {{ _.role("user") }}

    Company List: {{ company_list }}
  "#
}

test TwoCompanyTest {
  functions [MultiEntityResolution]
  args {
    company_list {
      companies [
        {
          id 1
          uuid null
          name "Tesla, Inc."
          ticker {
            id 3
            uuid null
            exchange "NASDAQ"
            symbol "TSLA"
            source_text_snippet null
          }
          description "Tesla is a leader in electric transportation and energy storage, producing high-performance EVs, solar solutions, battery systems, and pioneering autonomous driving software to accelerate the global shift toward sustainable energy."
          founded_year 2003
          ceo "Elon Musk"
          source_text_snippet null
          source_ids null
          source_uuids null
        }
        {
          id 2
          uuid null
          name "Tesla"
          ticker {
            id 4
            uuid null
            symbol "TSLA"
            source_text_snippet null
          }
          description "Tesla is known for its electric car innovations and has developed the Powerwall home battery, launched in 2015 to advance accessible solar energy storage and reliable backup power for homes"
          headquarters_location "Austin, United States"
          source_text_snippet null
          source_ids null
          source_uuids null
        }
      ]
    }
  }
}

test UUIDTrackingTest {
  functions [MultiEntityResolution]
  args {
    company_list {
      companies [
        {
          id 1
          uuid "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
          name "Tesla, Inc."
          ticker {
            id 3
            uuid null
            exchange "NASDAQ"
            symbol "TSLA"
            source_text_snippet null
          }
          description "Tesla is a leader in electric transportation and energy storage, producing high-performance EVs, solar solutions, battery systems, and pioneering autonomous driving software to accelerate the global shift toward sustainable energy."
          founded_year 2003
          ceo "Elon Musk"
          source_text_snippet null
          source_ids null
          source_uuids null
        }
        {
          id 2
          uuid "b2c3d4e5-f6a7-8901-bcde-f23456789012"
          name "Tesla"
          ticker {
            id 4
            uuid null
            symbol "TSLA"
            source_text_snippet null
          }
          description "Tesla is known for its electric car innovations and has developed the Powerwall home battery, launched in 2015 to advance accessible solar energy storage and reliable backup power for homes"
          headquarters_location "Austin, United States"
          source_text_snippet null
          source_ids null
          source_uuids null
        }
      ]
    }
  }
}

test MultipleSourceUUIDsTest {
  functions [MultiEntityResolution]
  args {
    company_list {
      companies [
        {
          id 1
          uuid "company1-uuid-123"
          name "Nvidia Corporation"
          ticker {
            id 1
            uuid null
            exchange "NASDAQ"
            symbol "NVDA"
            source_text_snippet null
          }
          description "Leading AI and GPU technology company specializing in artificial intelligence computing and graphics processing"
          headquarters_location "Santa Clara, CA"
          founded_year 1993
          ceo "Jensen Huang"
          source_text_snippet null
          source_ids null
          source_uuids ["original-doc-uuid-456", "article-uuid-789"]
        }
        {
          id 2
          uuid "company2-uuid-abc"
          name "NVIDIA"
          ticker {
            id 2
            uuid null
            symbol "NVDA"
            source_text_snippet null
          }
          description "Graphics processing unit manufacturer and AI computing leader known for GeForce, Quadro, and data center products"
          website_url "https://nvidia.com"
          revenue_usd 26974000000
          employees 22473
          source_text_snippet null
          source_ids null
          source_uuids ["news-uuid-def", "report-uuid-ghi", "blog-uuid-jkl"]
        }
        {
          id 3
          uuid "company3-uuid-xyz"
          name "Nvidia Corp"
          ticker null
          description "Technology company that designs GPUs for gaming and professional markets, as well as system on a chip units"
          linkedin_url "https://www.linkedin.com/company/nvidia/"
          source_text_snippet null
          source_ids null
          source_uuids ["wiki-uuid-mno", "sec-filing-uuid-pqr"]
        }
      ]
    }
  }
}

test WikiEnrichTest {
    functions [MultiEntityResolution]
    args {
        company_list {
            companies [
                {
                    id 1
                    uuid "e607907e-e7cc-40a5-b033-a795e9980c8f"
                    name "Oracle"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A cloud computing company that offers Oracle Cloud Infrastructure (OCI) and provides large-scale AI infrastructure, superclusters, and services for AI training and inference."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 2
                    uuid "4fa2d16e-34aa-4dd9-9890-3e8e4449e4a7"
                    name "Advanced Micro Devices, Inc."
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company that designs and manufactures high-performance computing products, including the Instinct series of GPUs (like the MI355X) for AI and data centers."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 3
                    uuid "f8b4d927-3c61-4a89-b734-8e5f9d2c1346"
                    name "Nvidia"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company specializing in GPUs and full-stack AI computing platforms, including the GB200 and Blackwell series, and platforms like DGX Cloud."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 4
                    uuid "a2c7e893-5d41-4b67-9f82-3c1d8e4a7b95"
                    name "Seekr"
                    ticker null
                    cik null
                    jurisdiction null
                    description "An AI company that develops large language models and AI agents, particularly for Edge deployments and vision-language foundation model training. It is a customer of Oracle Cloud Infrastructure."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                }
                {
                    id 5
                    uuid "b9f3e248-7a12-4c56-8d91-4e6f2a3b8c71"
                    name "CoreWeave"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in Nvidia's DGX Cloud Lepton platform, a compute marketplace for GPU resources."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 6
                    uuid "c4d8f156-9b23-4e87-a635-7f3e8b2d9a46"
                    name "Crusoe"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in Nvidia's DGX Cloud Lepton platform, a compute marketplace for GPU resources."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 7
                    uuid "d7a5b394-2c48-4f93-b872-5e9c3d7f8a12"
                    name "Firmus"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in Nvidia's DGX Cloud Lepton platform, a compute marketplace for GPU resources."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 8
                    uuid "e8b6c472-1d23-4a98-bf45-9a7c5e3d6f84"
                    name "Foxconn"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in Nvidia's DGX Cloud Lepton platform, a compute marketplace for GPU resources."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 9
                    uuid "f9c7d583-2e34-4b09-a856-8b4d7c2e9f95"
                    name "GMI Cloud"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in Nvidia's DGX Cloud Lepton platform, a compute marketplace for GPU resources."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 10
                    uuid "a1d8e694-3f45-4c10-b967-9c5e8d3f1a06"
                    name "Lambda"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in Nvidia's DGX Cloud Lepton platform, a compute marketplace for GPU resources."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 11
                    uuid "b2e9f705-4a56-4d21-c078-ad6f9e4c2b17"
                    name "Nebius"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in Nvidia's DGX Cloud Lepton platform, a compute marketplace for GPU resources."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 12
                    uuid "c3fa0816-5b67-4e32-d189-be7a0f5d3c28"
                    name "Nscale"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in Nvidia's DGX Cloud Lepton platform, a compute marketplace for GPU resources."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 13
                    uuid "d40b1927-6c78-4f43-e29a-cf8b1a6e4d39"
                    name "SoftBank Corp."
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in Nvidia's DGX Cloud Lepton platform, a compute marketplace for GPU resources."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 14
                    uuid "e51c2a38-7d89-4a54-f3ab-d09c2b7f5e4a"
                    name "Yotta Data Services"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in Nvidia's DGX Cloud Lepton platform, a compute marketplace for GPU resources."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 15
                    uuid "f62d3b49-8e9a-4b65-043b-e1ad3c8a6f5b"
                    name "Oracle"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A cloud company that provides Oracle Cloud Infrastructure (OCI), a platform for large-scale AI training, inference, and supercomputing."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 16
                    uuid "073e4c5a-9fab-4c76-154c-f2be4d9b7a6c"
                    name "AMD"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A semiconductor company that designs and manufactures high-performance computing and graphics solutions, including the Instinct series of GPUs (MI355X, MI300X) for data centers and AI workloads."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 17
                    uuid "184f5d6b-a0bc-4d87-265d-03cf5eac8b7d"
                    name "Nvidia"
                    ticker null
                    cik null
                    jurisdiction null
                    description "An AI computing company known for its GPUs (e.g., GB200 Blackwell), full-stack AI computing platforms, and services like Nvidia DGX Cloud."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 18
                    uuid "295a6e7c-b1cd-4e98-376e-14da6fbdc98e"
                    name "Seekr"
                    ticker null
                    cik null
                    jurisdiction null
                    description "An AI company specializing in developing large language models and vision-language foundation models for edge deployments and analysis of imagery and sensor data."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 19
                    uuid "3a6b7f8d-c2de-4fa9-487f-25eb70cfeda9"
                    name "CoreWeave"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in the Nvidia DGX Cloud Lepton platform, a marketplace that connects developers with a global network of GPU compute."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 20
                    uuid "4b7c809e-d3ef-40ba-598a-36fc81d0febf"
                    name "Crusoe"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in the Nvidia DGX Cloud Lepton platform, a marketplace that connects developers with a global network of GPU compute."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 21
                    uuid "5c8d91af-e4f0-41cb-6aab-47ad92e10fc0"
                    name "Firmus"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in the Nvidia DGX Cloud Lepton platform, a marketplace that connects developers with a global network of GPU compute."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 22
                    uuid "6d9ea2b0-f501-42dc-7bbc-58be03f211d1"
                    name "Foxconn"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in the Nvidia DGX Cloud Lepton platform, a marketplace that connects developers with a global network of GPU compute."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 23
                    uuid "7eafb3c1-0612-43ed-8ccd-69cf14a322e2"
                    name "GMI Cloud"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in the Nvidia DGX Cloud Lepton platform, a marketplace that connects developers with a global network of GPU compute."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 24
                    uuid "8fb0c4d2-1723-44fe-9dde-7ada25b433f3"
                    name "Lambda"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in the Nvidia DGX Cloud Lepton platform, a marketplace that connects developers with a global network of GPU compute."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 25
                    uuid "90c1d5e3-2834-4510-aeef-8bcb36c544a4"
                    name "Nebius"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in the Nvidia DGX Cloud Lepton platform, a marketplace that connects developers with a global network of GPU compute."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 26
                    uuid "a1d2e6f4-3945-4621-bff0-9cdc47d655b5"
                    name "Nscale"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in the Nvidia DGX Cloud Lepton platform, a marketplace that connects developers with a global network of GPU compute."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 27
                    uuid "b2e3f705-4a56-4732-c001-adea58e766c6"
                    name "SoftBank Corp."
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in the Nvidia DGX Cloud Lepton platform, a marketplace that connects developers with a global network of GPU compute."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 28
                    uuid "c3f40816-5b67-4843-d112-befe69f877d7"
                    name "Yotta Data Services"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company participating in the Nvidia DGX Cloud Lepton platform, a marketplace that connects developers with a global network of GPU compute."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 29
                    uuid "d4051927-6c78-4954-e223-c0fa7af988e8"
                    name "Nvidia Corporation"
                    ticker null
                    cik null
                    jurisdiction null
                    description "An American technology company that designs and develops graphics processing units (GPUs), system on a chips (SoCs), and application programming interfaces (APIs) for gaming, professional visualization, data centers, and automotive markets. It is a major player in the artificial intelligence (AI) hardware and software space."
                    website_url null
                    headquarters_location "Santa Clara, California, USA"
                    revenue_usd 10918000000
                    employees null
                    founded_year 1993
                    ceo "Jensen Huang"
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 30
                    uuid "e5162a38-7d89-4a65-f334-d1ab8ba099f9"
                    name "AMD"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A semiconductor company and a main rival to Nvidia in the graphics card industry. Nvidia was founded as a competitor to AMD."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 31
                    uuid "f6273b49-8e9a-4b76-0445-e2bc9cb0bfaa"
                    name "LSI Logic"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A company where Nvidia co-founder Jensen Huang was previously the director of CoreWare."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 32
                    uuid "07384c5a-9fab-4c87-1556-f3cd0eb1c0bb"
                    name "Sun Microsystems"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A technology company where Nvidia co-founders Chris Malachowsky and Curtis Priem previously worked."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 33
                    uuid "18495d6b-a0bc-4d98-2667-04de1fbc2ccc"
                    name "IBM"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A technology company where Nvidia co-founder Curtis Priem was previously a senior staff engineer and graphics chip designer. Nvidia also partnered with IBM on its Watson AI."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 34
                    uuid "295a6e7c-b1cd-4ea9-3778-15ea20cddddd"
                    name "Sequoia Capital"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A venture capital firm that provided venture capital funding to Nvidia."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 35
                    uuid "3a6b7f8d-c2de-4fba-4889-26fb31deefee"
                    name "Sutter Hill Ventures"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A venture capital firm that provided venture capital funding to Nvidia."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 36
                    uuid "4b7c809e-d3ef-40cb-5a9b-37ac42e0f0ff"
                    name "ATI Technologies"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A graphics technology company and rival to Nvidia, which was later acquired by AMD."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 37
                    uuid "5c8d91af-e4f0-41dc-6bac-48bd53f11100"
                    name "Microsoft"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A major technology company that developed the DirectX platform and partnered with Nvidia on the Xbox console. The article also mentions its market capitalization relative to Nvidia and its involvement in an antitrust investigation."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 38
                    uuid "6d9ea2b0-f501-42ed-7cbd-59ce64a22211"
                    name "Sega"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A video game company that had a partnership with Nvidia for the Dreamcast console and later made a crucial $5 million investment in the company."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 39
                    uuid "7eafb3c1-0612-43fe-8dce-6ada75b33322"
                    name "3dfx"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A pioneer in consumer 3D graphics technology and a former rival whose intellectual assets were acquired by Nvidia in 2000."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 40
                    uuid "8fb0c4d2-1723-4410-9edf-7bdb86c44433"
                    name "Sony"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A technology and entertainment company that partnered with Nvidia for the design of the graphics processor (RSX) for the PlayStation 3 game console."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 41
                    uuid "90c1d5e3-2834-4521-af00-8cdc97d55544"
                    name "Apple Inc."
                    ticker null
                    cik null
                    jurisdiction null
                    description "A technology company whose laptops were affected by faulty Nvidia GPUs and with whom Nvidia had a later dispute over driver support for macOS."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 42
                    uuid "a1d2e6f4-3945-4632-c010-9ded08e66655"
                    name "Dell"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A computer technology company whose laptops were affected by faulty Nvidia GPUs and from whom China allegedly acquired banned Nvidia servers."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 43
                    uuid "b2e3f705-4a56-4743-d121-aefb19f77766"
                    name "HP"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A technology company whose laptops were affected by certain Nvidia mobile chipsets and GPUs that had abnormal failure rates."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 44
                    uuid "c3f40816-5b67-4854-e232-c0fb2b088877"
                    name "Intel"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A major semiconductor company and competitor to Nvidia. The two companies signed a $1.5 billion cross-licensing agreement in 2011, and Nvidia's CEO has mentioned being open to using Intel's foundry services."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 45
                    uuid "d4051927-6c78-4965-f343-d1bc3cb09988"
                    name "Toyota"
                    ticker null
                    cik null
                    jurisdiction null
                    description "An automotive company that partnered with Nvidia to use its Drive PX-series artificial intelligence platform for its autonomous vehicles."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 46
                    uuid "e5162a38-7d89-4a76-0454-e2cd4dc0aa99"
                    name "Baidu"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A Chinese search giant that announced a far-reaching AI partnership with Nvidia for cloud computing, autonomous driving, and consumer devices."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 47
                    uuid "f6273b49-8e9a-4b87-1565-f3de5ed1bbaa"
                    name "Google"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A technology company that integrated Nvidia's Tesla P4 graphic cards into its Google Cloud service. The Google Brain team also used Nvidia GPUs for deep learning research."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 48
                    uuid "07384c5a-9fab-4c98-2676-04ef6fc2ccbb"
                    name "Mellanox Technologies"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A high-performance computing company that was acquired by Nvidia in a deal announced in March 2019 for $6.9 billion."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 49
                    uuid "18495d6b-a0bc-4da9-3787-15fb71dddecc"
                    name "SoftBank Group"
                    ticker null
                    cik null
                    jurisdiction null
                    description "An investment holding company that agreed to sell Arm to Nvidia for $40 billion, a deal that was later called off."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 50
                    uuid "295a6e7c-b1cd-4eba-4898-26gc82eeeeee"
                    name "Arm"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A UK-based chip designer that Nvidia attempted to acquire from SoftBank. Nvidia has also reportedly started designing Arm-based CPUs."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 51
                    uuid "3a6b7f8d-c2de-4fcb-59a9-37hd93ffffff"
                    name "Oracle Corporation"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A technology company whose co-founder Larry Ellison was mentioned as seeking to acquire Nvidia's H100 GPUs."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 52
                    uuid "4b7c809e-d3ef-40dc-6bab-48ie04f10000"
                    name "Tesla, Inc."
                    ticker null
                    cik null
                    jurisdiction null
                    description "An electric vehicle and technology company that previously used Nvidia hardware in its vehicles. Its CEO, Elon Musk, was mentioned as seeking to acquire Nvidia's H100 GPUs."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 53
                    uuid "5c8d91af-e4f0-41ed-7cbc-59jf15g21111"
                    name "OpenAI"
                    ticker null
                    cik null
                    jurisdiction null
                    description "An AI research and deployment company that received Nvidia's first DGX-1 supercomputer and is subject to an antitrust investigation by the FTC."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 54
                    uuid "6d9ea2b0-f501-42fe-8dcd-6akg26h32222"
                    name "Taiwan Semiconductor Manufacturing Company (TSMC)"
                    ticker null
                    cik null
                    jurisdiction null
                    description "A semiconductor manufacturing company from which Nvidia ordered 300,000 H20 AI chips."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 55
                    uuid "7eafb3c1-0612-43gf-9ede-7blh37i43333"
                    name "Anthropic"
                    ticker null
                    cik null
                    jurisdiction null
                    description "An AI company whose CEO, Dario Amodei, had a public dispute with Nvidia's CEO over AI regulation and industry practices."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 56
                    uuid "8fb0c4d2-1723-4421-af00-8cmj48k54444"
                    name "Microsoft"
                    ticker null
                    cik null
                    jurisdiction null
                    description "Microsoft Corporation is an American multinational corporation and technology conglomerate headquartered in Redmond, Washington. Founded in 1975, the company became influential in the rise of personal computers through software like Windows, and the company has since expanded to Internet services, cloud computing, video gaming and other fields. Microsoft is the largest software maker, one of the most valuable public U.S. companies, and one of the most valuable brands globally.\nMicrosoft was founded by Bill Gates and Paul Allen to develop and sell BASIC interpreters for the Altair 8800. It rose to dominate the personal computer operating system market with MS-DOS in the mid-1980s, followed by Windows. During the 41 years from 1980 to 2021 Microsoft released 9 versions of MS-DOS with a median frequency of 2 years, and 13 versions of Windows with a median frequency of 3 years. The company's 1986 initial public offering (IPO) and subsequent rise in its share price created three billionaires and an estimated 12,000 millionaires among Microsoft employees. Since the 1990s, it has increasingly diversified from the operating system market. Steve Ballmer replaced Gates as CEO in 2000.  He oversaw the then-largest of Microsoft's corporate acquisitions in Skype Technologies in 2011, and an increased focus on hardware that led to its first in-house PC line, the Surface, in 2012, and the formation of Microsoft Mobile through Nokia. Since Satya Nadella took over as CEO in 2014, the company has changed focus towards cloud computing, as well as its large acquisition of LinkedIn for $26.2 billion in 2016. Under Nadella's direction, the company has also expanded its video gaming business to support the Xbox brand, establishing the Microsoft Gaming division in 2022 and acquiring Activision Blizzard for $68.7 billion in 2023.\nMicrosoft has been market-dominant in the IBM PC–compatible operating system market and the office software suite market since the 1990s. Its best-known software products are the Windows line of operating systems and the Microsoft Office and Microsoft 365 suite of productivity applications, which most notably include the Word word processor, Excel spreadsheet editor, and the PowerPoint presentation program. Its flagship hardware products are the Surface lineup of personal computers and Xbox video game consoles, the latter of which includes the Xbox network; the company also provides a range of consumer Internet services such as Bing web search, the MSN web portal, the Outlook.com (Hotmail) email service and the Microsoft Store. In the enterprise and development fields, Microsoft most notably provides the Azure cloud computing platform, Microsoft SQL Server database software, and Visual Studio.\nMicrosoft is considered one of the Big Five American information technology companies, alongside Alphabet, Amazon, Apple, and Meta. In April 2019, Microsoft reached a trillion-dollar market cap, becoming the third public U.S. company to be valued at over $1 trillion. It has been criticized for its monopolistic practices, and the company's software has been criticized for problems with ease of use, robustness, and security."
                    website_url null
                    headquarters_location "Redmond"
                    revenue_usd null
                    employees 221000
                    founded_year 1975
                    ceo "Steve Ballmer"
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 57
                    uuid "90c1d5e3-2834-4532-c010-9dnk59l65555"
                    name "Nebius Group"
                    ticker null
                    cik null
                    jurisdiction null
                    description "Nebius Group N.V., headquartered in Amsterdam, is a technology company that provides artificial intelligence infrastructure. The company also owns Avride and TripleTen, as well as stakes in Toloka and Clickhouse. It is headquartered in Amsterdam with offices in Israel and the United States.\nThe company was formed in 1989 as Yandex N.V. by Arkady Volozh as a holding company for Yandex. In July 2024, due to international sanctions during the Russian invasion of Ukraine, it sold Yandex to a consortium of Russian investors, retaining several businesses that operated outside of Russia, and was renamed Nebius Group, then focusing on artificial intelligence.\n\n"
                    website_url null
                    headquarters_location "Amsterdam"
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 58
                    uuid "a1d2e6f4-3945-4643-d121-aeol6am76666"
                    name "Nvidia"
                    ticker {
                        id 66
                        uuid null
                        symbol "NVDA"
                        exchange "NASDAQ"
                    }
                    cik null
                    jurisdiction null
                    description "Nvidia Corporation ( en-VID-ee-ə) is an American technology company headquartered in Santa Clara, California. Founded in 1993 by Jensen Huang, Chris Malachowsky, and Curtis Priem, it develops graphics processing units (GPUs), system on a chips (SoCs), and application programming interfaces (APIs) for data science, high-performance computing, and mobile and automotive applications.\nOriginally focused on GPUs for video gaming, Nvidia broadened their use into other markets, including artificial intelligence (AI), professional visualization, and supercomputing. The company's product lines include GeForce GPUs for gaming and creative workloads, and professional GPUs for edge computing, scientific research, and industrial applications. As of the first quarter of 2025, Nvidia held a 92% share of the discrete desktop and laptop GPU market.\nIn the early 2000s, the company invested over a billion dollars to develop CUDA, a software platform and API that enabled GPUs to run massively parallel programs for a broad range of compute-intensive applications. As a result, as of 2025, Nvidia controlled more than 80% of the market for GPUs used in training and deploying AI models, and provided chips for over 75% of the world's TOP500 supercomputers. The company has also expanded into gaming hardware and services, with products such as the Shield Portable, Shield Tablet, and Shield TV, and operates the GeForce Now cloud gaming service. It also developed the Tegra line of mobile processors for smartphones, tablets, and automotive infotainment systems. \nIn 2023, Nvidia became the seventh U.S. company to reach a US$1 trillion valuation. In 2025, it became the first to surpass US$4 trillion in market capitalization, driven by rising global demand for data center hardware in the midst of the AI boom. For its strength, size and market capitalization, Nvidia has been selected to be one of Bloomberg's \"Magnificent Seven\", the seven biggest companies on the stock market in these regards."
                    website_url null
                    headquarters_location "Santa Clara"
                    revenue_usd 10918000000
                    employees null
                    founded_year 1993
                    ceo "Jensen Huang"
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 59
                    uuid "b2e3f705-4a56-4754-e232-bfpm7bn87777"
                    name "OpenAI, Inc."
                    ticker null
                    cik null
                    jurisdiction null
                    description "OpenAI, Inc. is an American artificial intelligence (AI) organization founded in December 2015 and headquartered in San Francisco, California. It aims to develop \"safe and beneficial\" artificial general intelligence (AGI), which it defines as \"highly autonomous systems that outperform humans at most economically valuable work\". As a leading organization in the ongoing AI boom, OpenAI is known for the GPT family of large language models, the DALL-E series of text-to-image models, and a text-to-video model named Sora. Its release of ChatGPT in November 2022 has been credited with catalyzing widespread interest in generative AI.\nThe organization has a complex corporate structure. As of April 2025, it is led by the non-profit OpenAI, Inc., registered in Delaware, and has multiple for-profit subsidiaries including OpenAI Holdings, LLC and OpenAI Global, LLC. Microsoft has invested US$13 billion in OpenAI, and is entitled to 49% of OpenAI Global, LLC's profits, capped at an estimated 10x their investment. Microsoft also provides computing resources to OpenAI through its cloud platform, Microsoft Azure.\nIn 2023 and 2024, OpenAI faced multiple lawsuits for alleged copyright infringement against authors and media companies whose work was used to train some of OpenAI's products. In November 2023, OpenAI's board removed Sam Altman as CEO, citing a lack of confidence in him, but reinstated him five days later following a reconstruction of the board. Throughout 2024, roughly half of then-employed AI safety researchers left OpenAI, citing the company's prominent role in an industry-wide problem.\n\n"
                    website_url null
                    headquarters_location "San Francisco"
                    revenue_usd 1000000000
                    employees 770
                    founded_year null
                    ceo "Sam Altman"
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 60
                    uuid "c3f40816-5b67-4865-f343-c0qn8co98888"
                    name "Oracle Corporation"
                    ticker null
                    cik null
                    jurisdiction null
                    description "Oracle Corporation is an American multinational computer technology company headquartered in Austin, Texas. Co-founded in 1977 in Santa Clara, California, by Larry Ellison, who remains executive chairman, Oracle Corporation is the fourth-largest software company in the world by market capitalization as of 2025. Its market value was approximately US$720.26 billion as of August 7, 2025. The company's 2023 ranking in the Forbes Global 2000 was 80. \nThe company sells database software (particularly the Oracle Database), and cloud computing software and hardware. Oracle's core application software is a suite of enterprise software products, including enterprise resource planning (ERP), human capital management (HCM), customer relationship management (CRM), enterprise performance management (EPM), Customer Experience Commerce (CX Commerce) and supply chain management (SCM) software."
                    website_url null
                    headquarters_location "Austin"
                    revenue_usd null
                    employees null
                    founded_year 1977
                    ceo "Phil White"
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 61
                    uuid "d4051927-6c78-4976-0454-d1ro9dp09999"
                    name "Sega"
                    ticker null
                    cik null
                    jurisdiction null
                    description "Sega Corporation (say-gah) is a Japanese video game company and subsidiary of Sega Sammy Holdings headquartered in Tokyo. It produces several multi-million-selling game franchises for arcades and consoles, including Sonic the Hedgehog, Angry Birds, Phantasy Star, Puyo Puyo, Super Monkey Ball, Total War, Virtua Fighter, Megami Tensei, Sakura Wars, Persona, The House of the Dead, and Yakuza. From 1983 until 2001, Sega also developed its own consoles. \nSega was founded by Martin Bromley and Richard Stewart in Hawaii as Nihon Goraku Bussan on June 3, 1960. Shortly after, it acquired the assets of its predecessor, Service Games of Japan. In 1965, it became known as Sega Enterprises, Ltd., after acquiring Rosen Enterprises, an importer of coin-operated games. Sega developed its first coin-operated game, Periscope, in 1966. Sega was sold to Gulf and Western Industries in 1969. Following a downturn in the arcade business in the early 1980s, Sega began to develop video game consoles, starting with the SG-1000 and Master System, but struggled against competitors such as the Nintendo Entertainment System. In 1984, Sega executives David Rosen and Hayao Nakayama led a management buyout, with backing from CSK Corporation.\nIn 1988, Sega released the Mega Drive, or the Genesis in North America. The Mega Drive struggled against competition in Japan, but the Genesis found success overseas after the release of Sonic the Hedgehog in 1991 and briefly outsold its main competitor, the Super Nintendo Entertainment System, in the US. In 2001, after several commercial failures such as the 32X, Saturn, and Dreamcast, Sega stopped manufacturing consoles to become a third-party developer and publisher, and was acquired by Sammy Corporation in 2004. Sega Holdings Co., Ltd. was established in 2015; Sega Corporation was renamed to Sega Games Co., Ltd., and its arcade division was split into Sega Interactive. In 2020, Sega Games and Sega Interactive merged to become Sega Corporation.\n\nSega's international branches, Sega of America and Sega Europe, are headquartered in Irvine, California, and London. Its development studios include their internal research and development divisions (which utilize the Ryu Ga Gotoku Studio and Sonic Team brands for several core franchise entries), Sega Sapporo Studio which mainly provides support for the Tokyo-based development teams as well as handling partial game development, and Atlus (including their R&D divisions) and five development studios in the UK and Europe: Creative Assembly, Sports Interactive, Sega Hardlight, Two Point Studios, and Rovio Entertainment (including Ruby Games). Sega is one of the world's most prolific arcade game producers and its mascot, Sonic, is internationally recognized. Sega is recognized for its video game consoles, creativity and innovations. In more recent years, it has been criticized for its business decisions and the quality of its creative output.\nBeing the entertainment contents division of Sega Sammy Holdings, forming one half of the Sega Sammy Group, Sega also owns a toy and amusement machine company, Sega Fave, which comprises their arcade development and manufacturing divisions and two animation studios: TMS Entertainment, which animates, produces, and distributes anime, and Marza Animation Planet, which specializes in CG animation."
                    website_url null
                    headquarters_location "Tokyo"
                    revenue_usd null
                    employees 121
                    founded_year 2015
                    ceo "Tom Kalinske"
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 62
                    uuid "e5162a38-7d89-4a87-1565-e2sp0eq0aaaa"
                    name "Sequoia Capital"
                    ticker null
                    cik null
                    jurisdiction null
                    description "Sequoia Capital Operations, LLC (commonly known simply as Sequoia) is an American venture capital firm headquartered in Menlo Park, California, specializing in seed stage, early stage, and growth stage investments in private companies across technology sectors. As of January 2025, the firm had approximately US$56 billion in assets under management.\nSequoia is an umbrella brand for three regionally focused venture entities: Sequoia Capital Operations on Europe and United States, Peak XV Partners on India and Southeast Asia, and HongShan on China.\nNotable successful investments made by the firm include Apple, ByteDance, and Cisco."
                    website_url null
                    headquarters_location "Menlo Park"
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 63
                    uuid "f6273b49-8e9a-4b98-2676-f3tr1fr1bbbb"
                    name "SoftBank Group"
                    ticker null
                    cik null
                    jurisdiction null
                    description "SoftBank Group Corp. (ソフトバンクグループ株式会社, SofutoBanku Gurūpu Kabushiki gaisha) is a Japanese multinational investment holding company headquartered in Minato, Tokyo, that focuses on investment management. The group primarily invests in companies operating in technology that offer goods and services to customers in a multitude of markets and industries ranging from the internet to automation. With over $100 billion in capital at its onset, SoftBank's Vision Fund is the world's largest technology-focused venture capital fund. Fund investors included sovereign wealth funds from countries in the Middle East.\nThe company is known for the leadership of its controversial founder and largest shareholder Masayoshi Son. Its investee companies, subsidiaries and divisions, including several unprofitable unicorns, operate in robotics, artificial intelligence, software, logistics, transportation, biotechnology, robotic process automation, proptech, real estate, hospitality, broadband, fixed-line telecommunications, e-commerce, information technology, finance, media and marketing, and other areas. Among its most internationally recognizable current stockholdings are stakes in Arm (semiconductors), Alibaba (e-commerce), OYO Rooms (hospitality), WeWork (coworking) and Deutsche Telekom (telecommunications). SoftBank Corporation, its spun-out affiliate and former flagship business, is the third-largest wireless carrier in Japan, with 45.621 million subscribers as of March 2021.\nSoftBank was ranked in the 2024 Forbes Global 2000 list as the 461st largest public company in the world.\nThe logo of SoftBank is based on the flag of the Kaientai, a naval trading company founded in 1865, near the end of the Tokugawa shogunate, by Sakamoto Ryōma.\nAlthough SoftBank does not affiliate itself to any traditional keiretsu, it has close ties with Mizuho Financial Group, its primary lender.\nOn January 21, 2025, it was announced that Softbank, along with OpenAI and Oracle, would launch what was announced to be an artificial intelligence infrastructure system in conjunction with the US government, titled Stargate. The project is estimated to cost $500 billion. President Trump stated that the infrastructure was developed to have American-made AI in the United States. The project will be funded over the course of the next four years.\n\n"
                    website_url null
                    headquarters_location "Minato"
                    revenue_usd null
                    employees null
                    founded_year 1865
                    ceo "Masayoshi Son"
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 64
                    uuid "07384c5a-9fab-4ca9-3787-04us2gs2cccc"
                    name "SoftBank Group"
                    ticker null
                    cik null
                    jurisdiction null
                    description "SoftBank Group Corp. (ソフトバンクグループ株式会社, SofutoBanku Gurūpu Kabushiki gaisha) is a Japanese multinational investment holding company headquartered in Minato, Tokyo, that focuses on investment management. The group primarily invests in companies operating in technology that offer goods and services to customers in a multitude of markets and industries ranging from the internet to automation. With over $100 billion in capital at its onset, SoftBank's Vision Fund is the world's largest technology-focused venture capital fund. Fund investors included sovereign wealth funds from countries in the Middle East.\nThe company is known for the leadership of its controversial founder and largest shareholder Masayoshi Son. Its investee companies, subsidiaries and divisions, including several unprofitable unicorns, operate in robotics, artificial intelligence, software, logistics, transportation, biotechnology, robotic process automation, proptech, real estate, hospitality, broadband, fixed-line telecommunications, e-commerce, information technology, finance, media and marketing, and other areas. Among its most internationally recognizable current stockholdings are stakes in Arm (semiconductors), Alibaba (e-commerce), OYO Rooms (hospitality), WeWork (coworking) and Deutsche Telekom (telecommunications). SoftBank Corporation, its spun-out affiliate and former flagship business, is the third-largest wireless carrier in Japan, with 45.621 million subscribers as of March 2021.\nSoftBank was ranked in the 2024 Forbes Global 2000 list as the 461st largest public company in the world.\nThe logo of SoftBank is based on the flag of the Kaientai, a naval trading company founded in 1865, near the end of the Tokugawa shogunate, by Sakamoto Ryōma.\nAlthough SoftBank does not affiliate itself to any traditional keiretsu, it has close ties with Mizuho Financial Group, its primary lender.\nOn January 21, 2025, it was announced that Softbank, along with OpenAI and Oracle, would launch what was announced to be an artificial intelligence infrastructure system in conjunction with the US government, titled Stargate. The project is estimated to cost $500 billion. President Trump stated that the infrastructure was developed to have American-made AI in the United States. The project will be funded over the course of the next four years.\n\n"
                    website_url null
                    headquarters_location "Minato"
                    revenue_usd null
                    employees null
                    founded_year 1865
                    ceo "Masayoshi Son"
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
                {
                    id 65
                    uuid "18495d6b-a0bc-4dba-4898-15vt3ht3dddd"
                    name "CoreWeave"
                    ticker null
                    cik null
                    jurisdiction null
                    description "CoreWeave, Inc. is an American AI cloud-computing startup based in Livingston, New Jersey. It specializes in providing cloud-based graphics processing unit (GPU) infrastructure to artificial intelligence developers and enterprises, and also develops its own chip management software.\nFounded in 2017 and focused on high-performance computing, CoreWeave has its own data centers operating in the United States and Europe, with some dedicated to multiple companies and some to a single client. Its $1.6 billion supercomputer data center for Nvidia in Plano, Texas has been described by Nvidia as the fastest AI supercomputer in the world."
                    website_url null
                    headquarters_location "Livingston"
                    revenue_usd null
                    employees 550
                    founded_year 2017
                    ceo null
                    linkedin_url null
                    source_text_snippet null
                    source_ids null
                    source_uuids null
                }
            ]
        }
    }
}