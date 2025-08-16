
// This is a BAML config file, which extends the Jinja2 templating language to write LLM functions.

enum Result {
    MATCH @description("The two companies match and have been resolved to a single entity.")
    NO_MATCH @description("The two companies do not match and have not been resolved to a single entity, or we can't be certain.")
}

class EntityResolutionResponse {

//   @description("The first company being matched with another company. This is the company that is being resolved to a single entity. If you think a company is a public entity, remember it may be abbrevited: e.g. 'Alphabet Inc.' may be referred to as 'Google' or 'GOOGL'. If you think a company is publicly traded, remember it may be referred to by its full name or by its abbreviation, e.g. 'International Business Machines' may be referred to as 'IBM'. If you think a company is a well known private entity, remember it may be referred to by its full name or by its abbreviation, e.g. 'Space Exploration Technologies Corp.' may be referred to as 'SpaceX'. If you think a company is a subsidiary of another company, remember it may be referred to by its full name or by its abbreviation, e.g. 'Instagram' may be referred to as 'Facebook' or 'Meta Platforms Inc.'.")
  
  match Result
  @description("Do the two companies match?")

  company Company?
  @description("The resolved, combined company if the two companies match. If not, this is null.")
}

function EntityResolution(company_one: Company, company_two: Company) -> EntityResolutionResponse {
  // see clients.baml
  client Gemini25Flash

  // The prompt uses Jinja syntax. Change the models or this text and watch the prompt preview change!
  prompt #"
    Examine the following two companies and determine if they are the same entity. Consider acronyms of company names when making your decision. If two companies are the same, return the resolved company with all combined attributes filled out. If one record has a valid field and the other doesn't, add it. If there are multiple company descriptions, summarize and combine them into a single description of less than 60 words.

    Return a match decision and a single company object with all combined attributes filled out if the two companies are the same entity, or an empty company object if they are not the same entity.

    {# special macro to print the output instructions. #}
    {{ ctx.output_format(hoist_classes=["Company", "Ticker"]) }}

    {{ _.role("user") }}

    Company One: {{ company_one }}
    Company Two: {{ company_two }}
  "#
}

test CombineDescriptionPositiveTest {
  functions [EntityResolution]
  args {
    company_one {
        id 1
        uuid "7558314c-0b3f-4db8-8895-4fea5b17fd27"
        name "Tesla, Inc."
        ticker {
            exchange "NASDAQ"
            symbol "TSLA"
      }
      description "Tesla is a leader in electric transportation and energy storage, producing high-performance EVs, solar solutions, battery systems, and pioneering autonomous driving software to accelerate the global shift toward sustainable energy."
      founded_year 2003
      ceo "Elon Musk"
    }
    company_two {
        id 2
        uuid "83b9df69-3449-4b1a-821a-d19914befac3"
        name "Tesla"
        ticker {
            symbol "TSLA"
            name "Tesla"
        }
        description "Tesla is known for its electric car innovations  ￼ and has developed the Powerwall home battery, launched in 2015  ￼ to advance accessible solar energy storage and reliable backup power for homes"
        headquarters_location "Austin, United States"
    }
  }
}

test DifferentNameFullRecordNegativeTest {
  functions [EntityResolution]
  args {
    company_one {
        id 1
        uuid "dcba5279-d8df-452c-aac3-cef3b079af02"
        name "Applied Materials, Inc."
        ticker {
            symbol "AMAT"
            name "Applied Materials, Inc."
        }
        description "Applied Materials is a global leader in materials engineering solutions for semiconductor manufacturing, providing equipment, services and software for chip fabrication including deposition, etch, and inspection systems."
    }
    company_two {
        id 2
        uuid "f0fbc099-fae6-4cb6-ae3e-e29a02425651"
        name "Applied Material Sciences"
    }
  }
  @@assert( verify_no_match, {{ this.match == "NO_MATCH" }} )
  // @@assert( verify_null_match, {{ this.company == null }} )
}

test DifferentFullRecordsNegativeTest {
  functions [EntityResolution]
  args {
    company_one {
        id 1
        uuid "3277a2d4-8645-4cc6-be34-79ebb851493d"
        name "Applied Materials, Inc."
        ticker {
            exchange "NASDAQ"
            symbol "AMAT"
        }
        description "Applied Materials is a global leader in materials engineering solutions for semiconductor manufacturing, providing equipment, services and software for chip fabrication including deposition, etch, and inspection systems."
        founded_year 1967
        ceo "Gary Dickerson"
        headquarters_location "Santa Clara, United States"
    }
    company_two {
        id 2
        uuid "5658a4e4-cfcb-4790-97fd-b8c26df1af1c"
        name "Applied Material Sciences"
        ticker {
            exchange "TSXV"
            symbol "AMS"
        }
        description "Applied Material Sciences specializes in advanced composite materials and nanotechnology solutions for aerospace and defense applications, developing carbon fiber components and specialized coatings for extreme environments."
        founded_year 2008
        ceo "Michael Chen"
        headquarters_location "Vancouver, Canada"
    }
  }
  @@assert( verify_no_match, {{ this.match == "NO_MATCH" }} )
  @@assert( verify_null_match, {{ this.company is none }} )
}

test JustNameSameExceptPeriodTest {
    functions [EntityResolution]
    args {
        company_one {
            id 1
            uuid "7e8b2c35-21e7-4821-a8da-abe43387671e"
            name "ABB Ltd."
        }
        company_two {
            id 2
            uuid "9cb6bb96-16d8-4bc7-bfd8-de1b9b4754ae"
            name "ABB Ltd"
        }
    }
    @@assert( verify_match, {{ this.match == "MATCH" }} )
}

test JustNameSameExceptAbbreviationTest {
    functions [EntityResolution]
    args {
        company_one {
            id 1
            uuid "cc47e115-7e0f-4a34-886c-fadbd3f3e125"
            name "International Business Machines Corporation"
        }
        company_two {
            id 2
            uuid "4386b965-d60d-4815-8902-0394b1ee044c"
            name "IBM"
        }
    }
    @@assert( verify_match, {{ this.match == "MATCH" }} )
}

