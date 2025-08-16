class CompanyList {
   companies Company[]
}

function MultiEntityResolution(company_list: CompanyList) -> CompanyList {
  // see clients.baml
  client Gemini25Flash

  // The prompt uses Jinja syntax. Change the models or this text and watch the prompt preview change!
  prompt #"
    Examine the following set of companies and determine which ones are the same entity. If two or more companies are the same, merge them and return the resolved company with all combined attributes filled out. If a record has a valid field and the other doesn't, add it. If there are multiple company descriptions, combine and summarize them into a single description of less than 60 words.

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

test WikiEnrichTest {
    functions [MultiEntityResolution]
    args {
        company_list {
            companies [
                {
                    id 1
                    uuid null
                    name "Oracle"
                    ticker null
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
                    uuid null
                    name "Advanced Micro Devices, Inc."
                    ticker null
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
                    uuid null
                    name "Nvidia"
                    ticker null
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
                    uuid null
                    name "Seekr"
                    ticker null
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
                    uuid null
                    name "CoreWeave"
                    ticker null
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
                    source_uuids null                }
                {
                    id 6
                    uuid null
                    name "Crusoe"
                    ticker null
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
                    source_uuids null                }
                {
                    id 7
                    uuid null
                    name "Firmus"
                    ticker null
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
                    source_uuids null                }
                {
                    id 8
                    uuid null
                    name "Foxconn"
                    ticker null
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
                    source_uuids null                }
                {
                    id 9
                    uuid null
                    name "GMI Cloud"
                    ticker null
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
                    source_uuids null                }
                {
                    id 10
                    uuid null
                    name "Lambda"
                    ticker null
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
                    source_uuids null                }
                {
                    id 11
                    uuid null
                    name "Nebius"
                    ticker null
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
                    source_uuids null                }
                {
                    id 12
                    uuid null
                    name "Nscale"
                    ticker null
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
                    source_uuids null                }
                {
                    id 13
                    uuid null
                    name "SoftBank Corp."
                    ticker null
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
                    source_uuids null                }
                {
                    id 14
                    uuid null
                    name "Yotta Data Services"
                    ticker null
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
                    source_uuids null                }
                {
                    id 15
                    uuid null
                    name "Oracle"
                    ticker null
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
                    source_uuids null                }
                {
                    id 16
                    uuid null
                    name "AMD"
                    ticker null
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
                    source_uuids null                }
                {
                    id 17
                    uuid null
                    name "Nvidia"
                    ticker null
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
                    source_uuids null                }
                {
                    id 18
                    uuid null
                    name "Seekr"
                    ticker null
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
                    source_uuids null                }
                {
                    id 19
                    uuid null
                    name "CoreWeave"
                    ticker null
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
                    source_uuids null                }
                {
                    id 20
                    uuid null
                    name "Crusoe"
                    ticker null
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
                    source_uuids null                }
                {
                    id 21
                    uuid null
                    name "Firmus"
                    ticker null
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
                    source_uuids null                }
                {
                    id 22
                    uuid null
                    name "Foxconn"
                    ticker null
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
                    source_uuids null                }
                {
                    id 23
                    uuid null
                    name "GMI Cloud"
                    ticker null
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
                    source_uuids null                }
                {
                    id 24
                    uuid null
                    name "Lambda"
                    ticker null
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
                    source_uuids null                }
                {
                    id 25
                    uuid null
                    name "Nebius"
                    ticker null
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
                    source_uuids null                }
                {
                    id 26
                    uuid null
                    name "Nscale"
                    ticker null
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
                    source_uuids null                }
                {
                    id 27
                    uuid null
                    name "SoftBank Corp."
                    ticker null
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
                    source_uuids null                }
                {
                    id 28
                    uuid null
                    name "Yotta Data Services"
                    ticker null
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
                    source_uuids null                }
                {
                    id 29
                    uuid null
                    name "Nvidia Corporation"
                    ticker null
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
                    source_uuids null                }
                {
                    id 30
                    uuid null
                    name "AMD"
                    ticker null
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
                    source_uuids null                }
                {
                    id 31
                    uuid null
                    name "LSI Logic"
                    ticker null
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
                    source_uuids null                }
                {
                    id 32
                    uuid null
                    name "Sun Microsystems"
                    ticker null
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
                    source_uuids null                }
                {
                    id 33
                    uuid null
                    name "IBM"
                    ticker null
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
                    source_uuids null                }
                {
                    id 34
                    uuid null
                    name "Sequoia Capital"
                    ticker null
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
                    source_uuids null                }
                {
                    id 35
                    uuid null
                    name "Sutter Hill Ventures"
                    ticker null
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
                    source_uuids null                }
                {
                    id 36
                    uuid null
                    name "ATI Technologies"
                    ticker null
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
                    source_uuids null                }
                {
                    id 37
                    uuid null
                    name "Microsoft"
                    ticker null
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
                    source_uuids null                }
                {
                    id 38
                    uuid null
                    name "Sega"
                    ticker null
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
                    source_uuids null                }
                {
                    id 39
                    uuid null
                    name "3dfx"
                    ticker null
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
                    source_uuids null                }
                {
                    id 40
                    uuid null
                    name "Sony"
                    ticker null
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
                    source_uuids null                }
                {
                    id 41
                    uuid null
                    name "Apple Inc."
                    ticker null
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
                    source_uuids null                }
                {
                    id 42
                    uuid null
                    name "Dell"
                    ticker null
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
                    source_uuids null                }
                {
                    id 43
                    uuid null
                    name "HP"
                    ticker null
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
                    source_uuids null                }
                {
                    id 44
                    uuid null
                    name "Intel"
                    ticker null
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
                    source_uuids null                }
                {
                    id 45
                    uuid null
                    name "Toyota"
                    ticker null
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
                    source_uuids null                }
                {
                    id 46
                    uuid null
                    name "Baidu"
                    ticker null
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
                    source_uuids null                }
                {
                    id 47
                    uuid null
                    name "Google"
                    ticker null
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
                    source_uuids null                }
                {
                    id 48
                    uuid null
                    name "Mellanox Technologies"
                    ticker null
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
                    source_uuids null                }
                {
                    id 49
                    uuid null
                    name "SoftBank Group"
                    ticker null
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
                    source_uuids null                }
                {
                    id 50
                    uuid null
                    name "Arm"
                    ticker null
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
                    source_uuids null                }
                {
                    id 51
                    uuid null
                    name "Oracle Corporation"
                    ticker null
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
                    source_uuids null                }
                {
                    id 52
                    uuid null
                    name "Tesla, Inc."
                    ticker null
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
                    source_uuids null                }
                {
                    id 53
                    uuid null
                    name "OpenAI"
                    ticker null
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
                    source_uuids null                }
                {
                    id 54
                    uuid null
                    name "Taiwan Semiconductor Manufacturing Company (TSMC)"
                    ticker null
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
                    source_uuids null                }
                {
                    id 55
                    uuid null
                    name "Anthropic"
                    ticker null
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
                    source_uuids null                }
                {
                    id 56
                    uuid null
                    name "Microsoft"
                    ticker null
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
                    source_uuids null                }
                {
                    id 57
                    uuid null
                    name "Nebius Group"
                    ticker null
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
                    source_uuids null                }
                {
                    id 58
                    uuid null
                    name "Nvidia"
                    ticker {
                        id 66
                        uuid null
                        symbol "NVDA"
                        exchange "NASDAQ"
                    }
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
                    source_uuids null                }
                {
                    id 59
                    uuid null
                    name "OpenAI, Inc."
                    ticker null
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
                    source_uuids null                }
                {
                    id 60
                    uuid null
                    name "Oracle Corporation"
                    ticker null
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
                    source_uuids null                }
                {
                    id 61
                    uuid null
                    name "Sega"
                    ticker null
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
                    source_uuids null                }
                {
                    id 62
                    uuid null
                    name "Sequoia Capital"
                    ticker null
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
                    source_uuids null                }
                {
                    id 63
                    uuid null
                    name "SoftBank Group"
                    ticker null
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
                    source_uuids null                }
                {
                    id 64
                    uuid null
                    name "SoftBank Group"
                    ticker null
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
                    source_uuids null                }
                {
                    id 65
                    uuid null
                    name "CoreWeave"
                    ticker null
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
                    source_uuids null                }
            ]
        }
    }
}
