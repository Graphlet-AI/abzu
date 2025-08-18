
// This is a BAML config file, which extends the Jinja2 templating language to write LLM functions.

class IndustryArticle {
  
  title string

  url string?
  @description("URL of the article")

  source NewsSource?
  @description("News source of the article: who published the article?")

  collected_at string?
  @description("Date the article was collected, in ISO-8601 format")
  
  posted_at string?
  @description("Date the article was published, in ISO-8601 format")

  urls string[]?
  @description("Any URLs mentioned in the article. This is a URL that was quoted or linked to, not the source url of the article.")

  authors Author[]?

  summary string
  @description("Summary of the article. What is it about? What are the key points?")

  companies Company[]?
  @description("Companies mentioned in the article. Use full name with company suffix.")

  tickers Ticker[]?
  @description("Ticker symbols of the companies mentioned in the article")

  products Product[]?
  @description("Products mentioned in the article")

  technologies Technology[]?
  @description("Technologies mentioned in the article. Technologies does not include products.")

  relationships CompanyRelationship[]?
  @description("Commercial deals and relationships mentioned in the article.")

  cited_sources NewsSource[]?
  @description("News sources mentioned in the article. This is a news source that was quoted or linked to. This is not the source of the article.")
}

class Author {
  name string
  @description("Name of the author or editor of the article")

  profile_url string?
  @description("URL of the author's profile")
}

class Ticker {
  id int
  @description("A unique identifier for this object.")

  uuid string?
  @description("A unique identifier for this object. Leave blank.")

  symbol string
  @description("Ticker symbol of the company if publicly traded")

  exchange string?
  @description("Exchange where the company is traded")
}

class Company {
  id int
  @description("A unique identifier for this object.")

  uuid string?
  @description("A unique identifier for this object. Leave blank.")

  name string
  @description("Formal name of the company with company suffix")

  ticker Ticker?
  @description("Ticker symbol of the company if publicly traded")

  description string
  @description("What does the company do? What is it known for?")

  website_url string?

  headquarters_location string?
  @description("Location of the company's headquarters, city, state and country")

  revenue_usd int?
  @description("Revenue of the company in USD")

  employees int?

  founded_year int?

  ceo string?
  @description("Full name of the company's CEO")

  linkedin_url string?

  source_ids int[]?
  @description("List of source Company ids that this Company originates from merges. Leave null if length is one.")

  source_uuids string[]?
  @description("Leave null at all times.")
}

class Product {
  id int
  @description("A unique identifier for this object.")

  uuid string?
  @description("A unique identifier for this object. Leave blank.")

  name string
  @description("Full name of the company's product")

  description string
  @description("Description of the product. What does it do? What is it used for?")

  manufacturers Company[]?
  @description("Name of one or more companies that manufacture or sell the product")

  technologies Technology[]?
  @description("Name of one or more technologies used in this product.")

  source_ids int[]?
  @description("List of source Product ids that this Product originates from merges. Leave null if length is one.")

  source_uuids string[]?
  @description("Leave null at all times.")
}

class Technology {
  id int
  @description("A unique identifier for this object.")

  uuid string?
  @description("A unique identifier for this object. Leave blank.")

  name string
  @description("Full name of the technology")

  developers Company[]?
  @description("Name of one or more Companies that invented or developed this technology")

  description string
  @description("Description of the technology. What does it do? What is it used for?")

  source_ids int[]?
  @description("List of source Technology ids that this Technology originates from merges. Leave null if length is one.")

  source_uuids string[]?
  @description("Leave null at all times.")
}

class Nation {
  common_name string @description("Common name of country")
  full_name string? @description("Official name of country")
  iso_2 string?
  iso_3 string?
  gdp float? @description("Gross Domestic Product of the country")
}

enum CompanyRelationshipType {
  Supplier @description("Sells a product or technology to another company")
  Acquisition @description("One company buys another company")
  Financing @description("Financing of a deal between companies")
  Investment @description("Investment in a company or country")
  Partnership @description("Partnership between two companies")
  Licensing @description("One company licenses a technology to another company")
  Subsidiary @description("One company is owned by another company and operates independently")
}

class CompanyRelationship {
  src_company Company
  @description("Source company in the deal.")

  dst_company Company?
  @description("Target company in the deal.")

  type CompanyRelationshipType

  technologies Technology[]?
  @description("Technologies involved in the deal.")

  products Product[]?
  @description("Products involved in the deal.")

  description string

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
}

class NewsSource {
  name string
  @description("Name of the news source. Newspaper, magazine, blog, etc.")

  url string?
  @description("URL of the web page of the news source")
}

function ExtractIndustryArticle(article_text: string) -> IndustryArticle {
  // see clients.baml
  client Gemini25Flash

  // The prompt uses Jinja syntax. Change the models or this text and watch the prompt preview change!
  prompt #"
    Parse the following article, perform information extraction to return a structured representation of the data in the schema below. Include only the information that is explicitly stated in the article except in the description fields, where you can give a generic description of an entity. Skip all fields that would be null, unless they are REQUIRED. Assign each unique entity an integer identifier in the id.integer field that appears wherever that entity is present in the output.

    {# special macro to print the output instructions. #}
    {{ ctx.output_format(hoist_classes=["Company", "Ticker", "Product", "Technology", "CompanyRelationship", "NewsSource", "Author"]) }}

    {{ _.role("user") }}
    {{ article_text }}
  "#
}

test GB200SemiAnalysisTest {
    functions [ExtractIndustryArticle]
    args {
        article_text #"
Title: GB200 Hardware Architecture – Component Supply Chain & BOM – SemiAnalysis

## GB200 Hardware Architecture – Component Supply Chain & BOM

## Hyperscale customization, NVLink Backplane, NVL36, NVL72, NVL576, PCIe Retimers, Switches, Optics, DSP, PCB, InfiniBand/Ethernet, Substrate, CCL, CDU, Sidecar, PDU, VRM, Busbar, Railkit, BMC

Dylan Patel
Wega Chu
Chaolien Tseng
Myron Xie
Jeremie Eliahou Ontiveros
Daniel Nishball
- Share using Native toolsShareCopied to clipboard
- Click to share on LinkedIn (Opens in new window)LinkedIn
- Click to share on X (Opens in new window)X
- Click to share on Facebook (Opens in new window)Facebook
- Hyperscale customization, NVLink Backplane, NVL36, NVL72, NVL576, PCIe Retimers, Switches, Optics, DSP, PCB, InfiniBand/Ethernet, Substrate, CCL, CDU, Sidecar, PDU, VRM, Busbar, Railkit, BMC
- Table of Contents:
- The 4 Rack Scale Form Factors of Blackwell
- Power Budget Estimates
- Compute Tray Diagrams & Cabling
- Networking
- NVLink Scale Up Interconnect
- GB200 NVL576
- Backend Networking
- Frontend Networking
- Networking Cables + Transceivers Bill of Materials
- Substrate, PCB, and CCL
- Keeping It Cool: Liquid Cooling Analysis
- Redesigning Rack Architecture for DLC
- Heat Transfer Flow from the Chip
- Liquid Cooling Form Factors: L2A vs L2L
- Redesigning Data Center Infrastructure for DLC
- Liquid Cooling Components Procurement Decision Chain
- DLC Components Competitive Landscape Analysis
- Power Delivery Network
- BMC
- Mechanical Components
- OEM / ODM Mapping
- Subscribe for full access

## Hyperscale customization, NVLink Backplane, NVL36, NVL72, NVL576, PCIe Retimers, Switches, Optics, DSP, PCB, InfiniBand/Ethernet, Substrate, CCL, CDU, Sidecar, PDU, VRM, Busbar, Railkit, BMC

Nvidia’s GB200 bringssignificant advances in performanceviasuperior hardware architecture, but the deployment complexities rise dramatically. While on the face of it, Nvidia has released a standard rack that people will just install in their datacenters without much trouble, plug-and-play style, the reality is there are dozens of different deployment variants with tradeoffs and a significant complexity increase generation on generation. The supply chain gets reworked for end datacenter deployers, clouds, server OEMs / ODMs, and downstream component supply chains.
Subscribe to get notified of all SemiAnalysis articles
Enter the code sent to your email
Please verify your email address to proceed.
By subscribing, you agree to thePrivacy PolicyandTerms and Conditions.
Today we are going to go from A to Z on the different form factors of GB200 and how they changed versus the prior 8 GPU HGX baseboard servers.We will break downs on unit volumes, supplier market share and cost for over 50 different subcomponents of the GB200 rack.Furthermore, we will dive into the hyperscale customization that changes the subcomponent supply chain heavily. Lastly we will also do a deep dive into the various types of liquid cooling architectures, deployment complexities, and the supply chain there.

## Table of Contents:

- GB200 form factors
GB200 form factors
- Power budget
Power budget
- Compute tray architecture
Compute tray architecture
- Networking fabricsNVLink fabricNVL72NVL36x2NVL576Backend fabric (Infiniband/Ethernet)Frontend fabricNetworking dollar content summaryOpticsDSP
Networking fabrics
- NVLink fabricNVL72NVL36x2NVL576
NVLink fabric
- NVL72
NVL72
- NVL36x2
NVL36x2
- NVL576
NVL576
- Backend fabric (Infiniband/Ethernet)
Backend fabric (Infiniband/Ethernet)
- Frontend fabric
Frontend fabric
- Networking dollar content summary
Networking dollar content summary
- Optics
Optics
- DSP
DSP
- Hyperscaler customization
Hyperscaler customization
- Substrate, PCB, and CCL
Substrate, PCB, and CCL
- Liquid coolingRack architecture changes & contentHeat transfer flowL2A (Liquid to Air) vs L2L (Liquid to Liquid)Redesigning data center infrastructureSupply chain procurement decision maker & analysisLiquid cooling components competition
Liquid cooling
- Rack architecture changes & content
Rack architecture changes & content
- Heat transfer flow
Heat transfer flow
- L2A (Liquid to Air) vs L2L (Liquid to Liquid)
L2A (Liquid to Air) vs L2L (Liquid to Liquid)
- Redesigning data center infrastructure
Redesigning data center infrastructure
- Supply chain procurement decision maker & analysis
Supply chain procurement decision maker & analysis
- Liquid cooling components competition
Liquid cooling components competition
- Power delivery network, PDB, Busbar, VRM
Power delivery network, PDB, Busbar, VRM
- BMC
BMC
- Mechanical components
Mechanical components
- OEM / ODM Mapping
OEM / ODM Mapping

## The 4 Rack Scale Form Factors of Blackwell

With GB200 Racks, there are 4 different major form factors offered, with customization within each.
- GB200 NVL72
GB200 NVL72
- GB200 NVL36x2
GB200 NVL36x2
- GB200 NVL36x2 (Ariel)
GB200 NVL36x2 (Ariel)
- x86 B200 NVL72/NVL36x2
x86 B200 NVL72/NVL36x2
The first one is theGB200 NVL72 form factor. This form factor requires approximately 120kW per rack. To put this density into context, a general-purpose CPU rack supports up to 12kW/rack, while the higher-density H100 air-cooled racks typically only support about 40kW/rack. Moving well past 40kW per rack is the primary reason why liquid cooling is required for GB200.
The GB200 NVL72 racks consists of 18 1U compute trays and 9 NVSwitch trays. Each compute tray is 1U in height and contains 2 Bianca boards. Each Bianca board is 1 Grace CPU and 2 Blackwell GPUs. The NVSwitch trays have two 28.8Tb/s NVSwitch5 ASICs.
With the exception of one hyperscaler who plans to deploy this as the primary variant, we believe that this version will be rarely deployed until Blackwell Ultra as most datacenter infrastructure cannot support this high of a rack density even with direct-to-chip liquid cooling (DLC).
The next form factor is theGB200 NVL36 * 2which is two racks side by side interconnected together.Most of the GB200 racks will use this form factor.Each rack contains 18 Grace CPUs and 36 Blackwell GPUs. Between the 2 racks, it still maintains being non-blocking all-to-all between all the 72 GPUs found in NVL72. Each compute tray is 2U in height and contains 2 Bianca boards. Each NVSwitch tray has two 28.8Tb/s NVSwitch5 ASIC chips. Each chip has 14.4Tb/s pointing backward toward the backplane and 14.4Tb/s pointing toward the front plate. Each NVswitch tray has 18 1.6T twin-port OSFP cages which connect horizontally to a pair NVL36 rack.
The per rack power & cooling density is 66kW per rack for a total of 132kW for NVL36 racks * 2. This is the time to market solution as each rack is only 66kW/rack. Unfortunately, a NVL36x2 system does use ~10kW more power compared to NVL72 due to the additional NVSwitch ASICs and the requirement for cross rack interconnect cabling. NVL36x2 will have 36 NVSwitch5 ASICs in total compared to only 18 NVSwitch5 ASICs on the NVL72.Even with this increase in overall power of 10kW, most firms will deploy this version next year instead of NVL72 as their datacenter can’t support 120kW per rack density.We will discuss the reason for this later in the liquid cooling section.
The last form factor is thespecific rack with a custom “Ariel” boardinstead of the standard Bianca. We believe this variant will primarily be used by Meta. Due to Meta’s recommendation system training and inferencing workloads, they require a higher CPU core and more memory per GPU ratio in order to store massive embedding tables and perform pre/post-processing on the CPUs.
Subscribe to get notified of all SemiAnalysis articles
Enter the code sent to your email
Please verify your email address to proceed.
By subscribing, you agree to thePrivacy PolicyandTerms and Conditions.
The content is similar to the standard GB200 NVL72: but instead the Bianca board is swapped for an Ariel board that has 1 Grace CPU and 1 Blackwell GPU. Due to the doubling of Grace CPU content per GPU, this SKU will be more expensive even compared to NVL36x2. Similar to NVL36x2, each NVSwitch tray has 18 1.6T twin-port OSFP cages which connect horizontally to a pair NVL36 rack.
We believe that the majority of Meta’s allocation will be the normal NVL36x2 as that is more geared towards GenAI workloads while the Ariel version will just be for their largest Recommendation System workloads. While there is nothing preventing Ariel from being used for GenAI workloads, the overprovisioning of CPUs means it will be inferior froma TCO standpointdue to higher capital cost and power.
Lastly, in Q2 2025, there will be aB200 NVL72 and NVL36x2 form factorthat will use x86 CPUs instead of Nvidia’s in-house grace CPU. This form factor is called Miranda. We believe that the CPU to GPU per compute tray will stay the same at 2 CPUs and 4 GPUs per compute tray.
We believe that this variant of NVL72/NVL36x2 will have lower upfront capital cost compared to the Grace CPU version, with less revenue flowing to Nvidia. Since it is using an x86 CPU, there will be much lower CPU to GPU bandwidth compared to Grace C2C which can talk to the GPUs at up to 900GB/s bidirectional (450GB/s). Because of this TCO is questionable. Furthermore as the x86 CPUs will not be able to share power between the CPU and GPUs to optimize for the workload total peak power required is much higher.In our accelerator model, we have broken down which GB200 form factors & the exact volume each of the top 50 buyers will be deploying.

## Power Budget Estimates

We estimate that the max TDP of each compute tray is 6.3kW. Most of the power draw from the compute tray is from the two Bianca board and 8 fans in each tray. The NVSwitch tray in NVL72 does not need to connect between racks as such has a 170W lower power draw compared to NVL36. With NVL36, there are 18 1.6T ACC cables to connect horizontally to the neighboring rack. We will explain the NVLink topology in further sections. 123.6kW per NVL72 is the total power draw including the inefficiencies from rectifying from AC power from the whip to DC power that the compute tray takes in.
While for NVL36*2, each rack has a max TDP of ~67kW while both rack pairs take in ~132kW. This is approximately 10kW more power draw compared to NVL72.

## Compute Tray Diagrams & Cabling

The heart of the GB200 NVL72/NVL36x2 is the Bianca board. The Bianca board contains two Blackwell B200 GPUs and a single Grace CPU. The ratio between CPU and GPU is now 1:2 on a board compared to GH200, which is a 1:1 ratio. Most of the customers that evaluated GH200 have told Nvidia that it was too expensive as 1:1 CPU ratio was too much for their workloads. This is one of the main reasons why GH200 shipped in such low volumes compared to HGX H100 (2 x86 CPUs, 8 H100 GPUs).For Blackwell, GB200 volume is way up relatively and there will be crossover in unit shipments versus HGX Blackwell B100/B200.
Normally in Hopper & Blackwell HGX servers, there are Broadcom PCIe switches between the CPU and the GPU. For the GB200, the CPU and GPU are both on the same PCB, reducing insertion loss to a point that there is no longer any need for switches or retimers between the CPU and GPU on the reference design. This is on the surface is extremely negative for Astera Labs. It now has ~35% short interest of free float, but that mostly from folks who aren’t following the supply chain deeply and only understand there are no retimers in the reference design. We will share more details below and in theGB200 Component & Supply Chain Model.
Another interesting thing about the reference design is that instead of using the typical MCIO PCIe x16 connectors to connect the main PCB board to a PCIe form factor ConnectX-7/8, the ConnectX-7/8 ICs now sit directly on top of the Bianca board using a mezzanine board via Mirror Mezz connectors.
This has the advantage of using the same cold plate to cool both the CPUs, GPUs, and ConnectX-7/8 NICs. The electrical lanes are routed to the OSFP cages at the front of the chassis with DensiLink connectors from the mezzanine board. This is similar to how Nvidia used DensiLink on their gold plated DGX H100 chassis to route from the ConnectX-7 to the OSFP cages.
Similar to the Dual GH200, within the same compute tray, there is a high speed Coherent NVLink connection that operates up to 600GB/s bidirectional bandwidth (300GB/s unidirectional). This is an extremely fast connection and allows the CPUs to share resources and memory similar to the HGX H100/B100/B200 servers which have 2 CPUs and have NUMA (Non-Uniform Memory Access) regions.
Due to this coherent link that hooks up two Bianca board, you can share memory, storage & resources such as NICs between the CPUs. For this reason, you will be able to depopulate a frontend NICs and only have 1 frontend NIC per compute tray instead of 2 as suggested in the reference design. This is similar to how in x86, even though, you have 2 CPUs per server, you only need 1 frontend NIC since the CPUs are able to share resources. We will discuss this more in the frontend networking section.
In terms of how the 2700 Watts of power gets to the board, there are 4 RapidLock 12V DC and 4 RapidLock GND (Ground) Power Connectors located around the CPU and GPU’s respective voltage regulator modules (VRM). These 12V and GND power connectors will connect to the compute tray’s power distribution board (PDB). The power distribution board takes 48V DC from the rack level busbar and steps it down to 12V DC for the Bianca board. We will discuss the changes to the power delivery network for the system in the power delivery section later.
In terms of the internal compute tray cables + connectors, most of the cost is dominated by the Mirror mezz connectors that connect the ConnectX-7/8 mezzanine board to the Bianca board & by the DensiLink cables that connect from the ConnectX-7/8 to the OSFP cages on the front of the chassis.
In the Nvidia reference design, there are two Bluefield-3s per compute tray, but as explained in later sections, we believe that most firms will not opt for any Bluefield-3 at all. At the front of the chassis, you can find all your typical server-related management ports, like RJ45, USB, etc. There are also eight NVMe storage bays for local node-level storage, and you can also find your scale-out backend OSFP cages.
The backend cage leads us to discuss one of the most critical pieces of the GB200: networking.

## Networking

Similar to the HGX H100, AMD MI300X, Intel Gaudi, AWS Trainium, there are 4 different networks in the GB200 systems:
- Frontend Networking (Normal Ethernet)
Frontend Networking (Normal Ethernet)
- Backend Networking (InfiniBand/RoCE Ethernet)
Backend Networking (InfiniBand/RoCE Ethernet)
- Accelerator Interconnect (NVLink)
Accelerator Interconnect (NVLink)
- Out of Band Networking
Out of Band Networking
As a quick refresher, thefrontend networkingis just your normal ethernet network that you use to connect to the internet, SLURM/Kubernetes, networked storage, data loading, model checkpoints. This network is typically 25-50Gb/s per GPU, so on a HGX H100 server, it will be 200-400Gb/s per server, while on a GB200 computer tray node, it will be 200-800Gb/s per server depending on the configuration.
Yourbackend networkis used to scale out GPU-GPU communications across hundred to thousands of racks. This network could either be Nvidia’s Infiniband or Nvidia Spectrum-X Ethernet or Broadcom Ethernet. With the optionsfrom Nvidia being way more expensive compared to the Broadcom Ethernet solutions.
Thescale-up accelerator interconnect(NVLink on Nvidia, Infinity Fabric/UALink on AMD,ICI on Google TPU, NeuronLink on Amazon Trainium 2) is an ultra-high speed network that connects GPUs together within a system. On Hopper, this network connected 8 GPUs together at 450GB/s each while on Blackwell NVL72, it will connect 72 GPUs together at 900GB/ each. There is a variant of Blackwell called NVL576 that will connect 576 GPUs together but basically no customers will opt for it. In general, your accelerator interconnect is 8-10x faster than your backend networking.
Lastly, there is yourout of band management networkwhich is used for re-imaging your operating system, monitor node health such as fan speed, temperatures, power draw, etc. Your baseboard management controller (BMC) on servers, PDUs, switches, CDUs are usually connected to this network to monitor and control these IT equipment.
Subscribe to get notified of all SemiAnalysis articles
Enter the code sent to your email
Please verify your email address to proceed.
By subscribing, you agree to thePrivacy PolicyandTerms and Conditions.

## NVLink Scale Up Interconnect

Compared to HGX H100, the frontend, backend and out of band networking of GB200 are mostly same with the exception of NVLink expanding outside of the chassis. Only hyperscaler customizations are different gen on gen. Previously in HGX H100, the 8 GPUs and 4 NVSwitch4 Switch ASICs are connected together using PCB traces as they are on the same PCB, the HGX baseboard.
Now on HGX Blackwell, the NVSwitch ASICs are in the middle to reduce the length of the PCB trace given the upgraded 224G SerDes
But on the GB200, the NVSwitches are on a different tray from GPUs and therefore you need to either use Optics or ACCs to connect between them.
In NVL72, they keep the same flat 1 tier NVLink topology as HGX Hopper/Blackwell such that you can talk to any of the GPUs within the same rack with only 1 hop through an NVSwitch. This is unlike AMD & Intel’s current generation interconnect which connects directly from GPU to GPU without a switch, which leads to reduced Accelerator to Accelerator bandwidth.
In NVL36x2, it only takes 1 hop to get to any of the 36 GPUs within the same rack but in order to talk to the other 36 GPUs in the rack beside it, it takes 2 NVSwitch hops to get across the racks. Intuitively, one additional hop adds latency but is not noticeable for training. It will slightly impact inference, but not too muchunless extremely high interactivity (>500TPS) at batch 1 without speculative decoding is the target.Note that is quite an unrealistic scenario we don’t expect anyone to utilize.
Nvidia claims that if they used optics with transceivers, they would have needed to add 20kW per NVL72 rack. We did the math and calculated that it would need to use 648 1.6T twin port transceivers with each transceiver consuming approximately 30Watts so the math works out to be 19.4kW/rack which is basically the same as Nvidia’s claim. At about $850 per 1.6T transceiver, this works out to be $550,800 per rack in just transceiver costs alone. When you mark that up by Nvidia’s 75% gross margin, that would mean $2,203,200 per rack of NVLink transceivers that the end customer would need to pay.This is one of the main reasons why DGX H100 NVL256 never shipped due to the massive cost of transceivers.Furthermore, bleeding edge transceivers like the 1.6T NVLink transceivers have way worse reliability compared to copper cables or even prior generation optics.
As such, this is the reason Nvidia chose to use 5184 copper cables, which is a much cheaper, less power hungry, and more reliable option. Each GPU has 900GB/s unidirectional bandwidth. Each differential pair (DP) is capable of transmitting 200Gb/s in 1 direction thus it will take 72 DP per GPU for both directions. Since there are 72 GPUs per NVL72 rack, that would mean there is 5184 differential pairs. Each NVLink cable contains 1 differential pair thus there are 5184 cables.
This is a massive increase in copper content generation on generation. In a bit of a whiplash, we have seen some investors estimate that there is around $3k of NVLink interconnect content per GPU bringing the total to $216k/NVL72 rack but this is completely wrong.
First of all, how did people even get to ridiculous numbers such as $3k per GPU? We believe that they took the 900GB/s (7200Gb/s) of unidirectional bandwidth per GPU and looked at the retail price of a 400Gb/s copper cable at $162. Since it takes 18 400Gb/s full duplex cables per GPU, that would bring the price per GPU to $3k. This figure is wrong by a massive margin.
Furthermore, there is a misconception that the cables are expensive. Most of the cost is not from the cables itself but instead in termination of the cables & the connectors. The connectors are expensive as they need to prevent crosstalk between different differential pairs. Crosstalk is extremely bad as it blurs out other signals and causes errors where the de-serializers can’t read the correct bits. Nvidia has chosen to use the Ultrapass Paladin backplane product from Amphenol for their NVLink backplane interconnect as the primary initial source.
We will use the primary source’s name for each connector and cable in the article, but the there are 3 sources with varying share over time, details of which we share in the fullGB200 Component & Supply Chain Model
Each Blackwell GPU is connected to an Amphenol Paladin HD 224G/s connector, each with 72 differential pairs. Then, that connector attaches to the backplane Paladin connector. Next, it will connect using SkewClear EXD Gen 2 Cable to the NVSwitch tray Paladin HD connector with 144 differential pairs per connector. From the NVSwitch Paladin connector to the NVSwitch ASIC chip, OverPass flyover cables are needed since there are 4 144 DP connectors (576 DPs) per switch tray and there would be way too much crosstalk to do PCB traces in such a small area. Furthermore loss over the PCB is worse than over the flyover cables.
With NVL36x2, each system will require an additional 162 1.6T twin-port horizontal ACC cableswhich are extremely priceyto connect the NVSwitch trays between Rack A and Rack B.We break down the ACC cable and chip market here.There are multiple players with significant share. Furthermore, an additional 324 DensiLink flyover cables will be required for the OSFP cages. These DensiLink flyover cables alone are more than $10,000 of additional cost per NVL36x2.
Moreover, it will require twice as many NVSwitch5 ASICs to enable the connection between Rack A and Rack B. This will bring the total NVLink copper cabling costs up bymore than double versus NVL72.
Even though the NVLink backplane content is more than twice as expensive for NVL36x2 vs NVL72, most customers will opt for the NVL36x2 design due to power and cooling constraints which we will discuss below. To be clear while it is very pricey, both NVL36x2 and NVL72 have lower copper costs than the investor community thinks.
The real winner is the cabling vendors and active copper chip vendors in the supply chain who have a massive increase in volumes for leading edge 1.6T due to the prevalence of NVL36x2.
Subscribe to get notified of all SemiAnalysis articles
Enter the code sent to your email
Please verify your email address to proceed.
By subscribing, you agree to thePrivacy PolicyandTerms and Conditions.

## GB200 NVL576

As Jensen mentioned on stage, GB200 NVLink can connect to 576 Blackwell GPUs together. We believe this is done using a 2 tier fat tree topology with 18 planes. This is similar to what they planned for DGX H100 NVL256 to connect 16 NVL36 racks. It will use 288 L1 NVSwitch5 ASICs (144 1U switch trays) located in the compute racks like NVL36x2, and it will use 144 L2 NVSwitch ASICs (72 2U switch trays) located on dedicated NV Switch trays. Like NVL36x2, the connection between the GPUs and the L1 NVSwitch will use the same copper backplane since it is over a short distance.
Unfortunately, between the L1 NVSwitch and the L2 NVSwitch, the distance is greater than what copper can achieve; thus, optical connections must be used. Furthermore, the L2 NVSwitches use Flyover cables to go to the OSFP cages on the front of the chassis. The additional BOM cost for NVL576 is astronomical at over $5.6 million dollars (9.7k per GPU) that Nvidia would need to pay to their suppliers.
Applying a blanket 75% gross margin means customers would need to pay an additional 38.8k per GPU for NVL576 copper + optical connections. While Nvidia can cut back on margins, even at 0% for the scale out NVLink solution, it’s basically untenable.This is the exact same reason to why DGX H100 NVL256 never shipped due to the massive cost of transceivers. Optics is far too expensive for the accelerator interconnect as the accelerator interconnect needs to be extremely high bandwidth.

## Backend Networking

The backend networking of GB200 is where most of the options crop up. Nvidia generally releases GPUs with the new generation of NIC and Switch ready to go, but this generation, due to Nvidia’s aggressive timelines, especially with 224G SerDes, the new networking comes halfway through the Blackwell generation. As such, all initial shipments of GB200 will utilize the same ConnectX-7 that shipped in the majority of H100 servers.
For the Backend Networking there a handful of different types of switches that customers will use depending on which NIC they utilize.
- Quantum-2 QM9700 Infiniband NDR
Quantum-2 QM9700 Infiniband NDR
- Quantum-X800 QM3400 Infiniband XDR
Quantum-X800 QM3400 Infiniband XDR
- Quantum-X800 QM3200 Infiniband NDR/XDR
Quantum-X800 QM3200 Infiniband NDR/XDR
- Spectrum-X SN5600
Spectrum-X SN5600
- Spectrum-X Ultra
Spectrum-X Ultra
- Broadcom Tomahawk 5
Broadcom Tomahawk 5
- Broadcom Tomahawk 6
Broadcom Tomahawk 6
In terms of the backend networking, the time to market shipments will all be the QM9700 Quantum-2 switch or Broadcom Tomahawk 5 just like H100 geneartion. Despite it being the same backend networking hardware, there is a big challenge with utilizingrail optimized designs. This due to the port mismatch between the switch and how many ports there are on a rack. With NVL72, there are 4 GPUs per compute tray, which means in a 4 rail optimized design, each Quantum-2 switch should have 18 downlink ports.
Since each switch has the same number of uplink ports in a fat tree, that means only 36 out of the 64 ports will be used. In effect, each switch will have many idle ports. If 2 rails went to each switch, then that would be 72 ports which will be over what the QM9700 Quantum-2 switch offers. In order to utilize all ports within each Quantum-2 switch, there will be 9 non-rail optimized leaf switches for every 4 NVL72 rack.
For ConnectX-7, you can also use the Q3200 Quantum-3 switch tray which contains 2 independent switches, each with 36 400Gb/s ports. This does not have a port mismatch and can use 4-rail optimized with 4 Q3200 Quantum-X800 Switch per NVL72.
For the upgraded 800Gb/s ConnectX-8, which will ship starting Q2 2025 with Quantum-X800 Q3400 which has 144 800Gb/s ports distributed across 72 twin port OSFP ports. Since there is no port mismatch, most customers will choose the Nvidia recommended design of 4-rail optimized with the switch rack being end of rack (EoR).
With CX-8, you can also use Spectrum-X Ultra 800G, forgoing the costly and expensive Bluefield option that was required in the prior generation.We discuss the Quantum-X800 switch option here and how it will affect the optical transceiver market.Broadcom based Tomahawk 6 deployment variants will also arrive in the 2ndhalf of next year.
The transition from CX-7 to CX-8 will be the main impetus for the shift from 400G (4x100G) SR4 optical transceivers to 800G (4x200G) DR4 optical transceivers. With CX-7 on the GB200 NVL72, each GPU has 400G of bandwidth and is connected to one OSFP cage with the multimode400G Single-Port SR4 transceiverwith four optical lanes each powered by a multimode 100G VCSEL. With a CX-7 based network, the switch side usually employs the 800G twin-port SR8 or DR8 transceiver.
For CX-8, all the speeds double, 800G (4x200G) DR4 per GPU and 1.6T(8x200G) DR8 per OSFP cage on the switch end. Because development work on the 200G multimode VCSEL will not complete for another 9 to 18 months for the 1.6T ramp, the industry has instead turned to the single mode 200G EML instead.
Similar to DGX H100, Cedar-8 will be available where both CX-8 NIC ICs from each Bianca board goes into a single OSFP224 cage.The advantages of requiring two 1.6T (8x200G lanes) twin port transceivers instead of four 800G(4x200G lanes) single port transceivers. Since a single port 4x200G transceiver is approximately 35% less expensive than an 8x200G twin port transceiver, by using Cedar-8 instead of two 4x200G transceivers, the cost will be 30% lower. Due to the cooling challenges of having 2x as much bandwidth in a single OSFP cage on the compute tray, we expect that most firms will not be using the Cedar-8.
Most firms will be sticking to ConnectX-7/ConnectX-8 at launch. Even firms such as Google, that have historically used custom backend NICs from the likes of Intel, will be switching back to the Nvidia ConnectX-8 NICs.
The only exception that will integrate their own backend NIC will be Amazon. We believe they will use their custom backend 400G (4x100G) NIC. This networking card will be different from their standard Nitro NICs as it will mostly be performance oriented.
In order to use custom backend NICs on the Bianca board instead of using ConnectX ICs on the mezzanine board, they will need to use an adapter mezzanine board that splits from the mirror mezz connectors into 8 MCIO PCIe connectors that go to the front of the chassis.
Since there will be no ConnectX-7/8 or Bluefield-3, which both have integrated PCIe switches, a dedicated PCIe switch from Broadcom / Astera Labs will be required to connect the backend NICs to both the CPU and GPU. InSemiAnalysis GB200 Component & Supply Chain Model, we breakdown the PCIe switch supplier, volume, and ASP. There are still hyperscaler custom design that includes PCIe Switches for between the CPU and NICs. Nvidia’s Miranda design is also quite different than GB200 on PCIe Lane Handling. FurthermoreAmazon Trainium 2 deployments have large amounts of Astera Labs retimer content.
Using a custom NIC brings extra engineering work to firms as they can’t use the default water cooling block which is engineered to cool the ConnectX ICs too. They would also need to run fresh thermal simulations to ensure that custom NICs in the front of the chassis have enough cooling capacity to not cause overheating problems. Moreover, they will not be able to use the 1U compute tray version used in NVL72.
They can only opt for the 2U NVL36 version which has enough air-cooling capacity at the front of the tray. All of this extra engineering work will delay the time to market for Amazon and anybody else attempting to use custom backend NICs. These challenges are why Google opted to use ConnectX-8 instead of continuing to use Intel’s IPUs for their GB200 servers.

## Frontend Networking

In the reference design, there are two 400Gb/s Bluefield-3 per compute tray. Since there are 4 GPUs per compute tray, that would mean that each GPU gets 200Gb/s of frontend bandwidth. The most advanced HGX H100 server deployed today has a single 200-400Gb/s ConnectX-7 NIC for their frontend traffic. That is for 8 GPUs, meaning 25-50Gb/s per GPU. 200Gb/s of frontend bandwidth per GPU is an extreme amount and most customers will not opt for this additional cost. In general, the Nvidia reference design is overprovisioned for the absolute worst-case situation for them to sell you more content.
We believe that the only major customer that will use Bluefield-3 as a frontend NIC will be Oracle. They run a cloud service that needs frontend network virtualization but have deployed a custom NIC solution, unlike the other hyperscalers. Amazon, Google, & Microsoft all have custom frontend NICs that are present in all their general-purpose CPU servers and accelerated computing servers already. They intend to continue to use these solutions as they offer a great TCO advantage and are already vertically integrated into their networking/cloud software stack.
Ironically, the only firm (xAI) that has widely used Bluefield-3 for the AI cluster is not even using it for its intended DPU purpose. xAI is using their Bluefield-3 in NIC mode instead of DPU mode since first-generation Nvidia Spectrum-X Ethernet requires Bluefield-3 for backend NICs as a bandage solution. Spectrum-X800 Ultra will work with CX-8 backend NICs and will not require Bluefield-3/4s to operate properly.

## Networking Cables + Transceivers Bill of Materials

Below, we have calculated the Bill of Material costs Nvidia pays their contract manufacturers. We will be only calculating the cost of the transceivers on the compute/NVSwitch tray end as the calculations get complex if you include switches, as clusters can be tier 2 or tier 3, or even 4 tiers in giant clusters.
You can see that with ConnectX-8, by using a Top of Rack design with DAC/ACC copper instead of a 4-rail optimized backend design; there are savings of ~$32k for just the backend network alone. Unfortunately, due to the tight power requirements of the compute racks, we believe that most people will have to put their backend switches in a different service rack and use optics to connect between them.
For the out of band management, this is all cheap copper RJ45 cables that cost less than a dollar each to connect from the compute/switch trays to the top of the rack out of band management switch. As mentioned above, the reference design is overkill for how much frontend NICs and bandwidth they have.We believe that most firms will have 200G of frontend bandwidth instead of having 2 BF-3 which is 800Gb/s of bandwidth in total per compute tray.This will lead to a saving of $3.5k per system just in transceiver costs alone.
On the optics and DSPs, Nvidia is expanding the supply chain greatly to Eoptolink from just Fabrinet and Innolight who were the vast majority. Eoptolink is focusing on 800G LPO and 1.6T with DSP.
The DSP game also changes massively. While Marvell was 100% share on Nvidia last generation with H100. This generation, Broadcom comes in a big way. We see both Innolight and Eoptolink looking to be adding Broadcom in volume for the DSP.
Furthermore, Nvidia has hired a number of DSP engineers and taped out a 1.6T DSP. We do not believe this will ramp in the near term, but if it does, it will be on the Fabrinet transceivers. The biggest challenge to ramping up the internal DSP is that Nvidia has used primarily the same long reach high power SerDes on each side of the DSP. Typically, DSPs have differently optimized SerDes on the optics facing vs NIC/Switch facing sides. Both sets of SerDes are optimized for power more than reach alone which was Nvidia’s main optimization point when they designed their 224G SerDes. Nvidia’s internal DSP guzzle too much power, and as such their in-house DSP is too difficult to ramp production of due to cooling challenges in the already toasty 1.6T transceivers. Nvidia’s DSP can also function as a retimer if needed, but the ACCs are enough.
We have market share and ASP of Optics provider and DSPs in theSemiAnalysis GB200 Component & Supply Chain Model.
The above only covered the high level and basics, but below, we will dive into all the subcomponents and BOM on the GB200 including substrate, PCB, CCL, Substrate, liquid cooling, Sidecars, CDUs, UQDs, Manifolds, Vapor Chambers, Cold Plates, BMCs, and Power Delivery below. We will also cover more on the hyperscale customization. We will also cover all the complexities and decision matrices for liquid cooling supply chain selections.
Subscribe to get notified of all SemiAnalysis articles
Enter the code sent to your email
Please verify your email address to proceed.
By subscribing, you agree to thePrivacy PolicyandTerms and Conditions.

##### Subscribe for full access to this article

With a SemiAnalysis subscription you’ll get access to newsletter articles and article discussions.
Model access not included – please reach out tosales@semianalysis.comfor our institutional offerings.
Enter the code sent to your email
Please verify your email address to proceed.
By subscribing, you agree to thePrivacy PolicyandTerms and Conditions.

## Keep Reading

- Nvidia’s Blackwell Reworked – Shipment Delays & GB200A Reworked PlatformsMGX GB200A NVL36, B102, B20, CoWoS-L, CoWoS-S, GB200A NVL64, ConnectX-8, Liquid Cooling vs Air Cooling, NVLink Backplane, PCB, CCL, Substrate, BMC, Power Delivery

##### Nvidia’s Blackwell Reworked – Shipment Delays & GB200A Reworked PlatformsMGX GB200A NVL36, B102, B20, CoWoS-L, CoWoS-S, GB200A NVL64, ConnectX-8, Liquid Cooling vs Air Cooling, NVLink Backplane, PCB, CCL, Substrate, BMC, Power Delivery

- GB200 & GB200A Component & Supply Chain Model

##### GB200 & GB200A Component & Supply Chain Model

- Nvidia’s Christmas Present: GB300 & B300 – Reasoning Inference, Amazon, Memory, Supply ChainBlackwell Delays, Microsoft Orders, GB300 BOM, Nvidia Gross Margin, ConnectX-8, VRMs, Micron, Samsung, SK Hynix, Wistron, FII Foxconn, Aspeed, Axiado

##### Nvidia’s Christmas Present: GB300 & B300 – Reasoning Inference, Amazon, Memory, Supply ChainBlackwell Delays, Microsoft Orders, GB300 BOM, Nvidia Gross Margin, ConnectX-8, VRMs, Micron, Samsung, SK Hynix, Wistron, FII Foxconn, Aspeed, Axiado

## Most Popular

### Huawei AI CloudMatrix 384 – China's Answer to Nvidia GB200 NVL72

#### China Abundance of Power, 100% Optics, 0% Copper, Power Inefficiency, 2.6x lower FLOP per Watt, 14 Transceivers per Chip, Linear Pluggable Optics

### The GPU Cloud ClusterMAX™ Rating System | How to Rent GPUs

#### 90%+ Coverage by Rental GPU Value, GPU Cloud Evaluation Guidelines, GPU Pricing Updates, GPU Bubble Burst, CoreWeave IPO, Hyperscalers, AI Neocloud Economics, Neocloud IRR

### AMD 2.0 – New Sense of Urgency | MI450X Chance to Beat Nvidia | Nvidia's New Moat

#### Rapid Improvements, Developers First Approach, Low AMD AI Software Engineer Pay, Python DSL, UALink Disaster, MI325x, MI355x, MI430X UL4, MI450X Architecture, IF64/IF128, Flexible IO, UALink, IFoE

## Comments

- Ben PJuly 17, 2024

##### Sign up for a paid plan and join the discussion

With a SemiAnalysis subscription you get full access to all articles, Data Explorer graphs, article discussions, and further insight into deep dives.
Enter the code sent to your email
Please verify your email address to proceed.
        "#
    }
}
test SemiAnalysisTest {
  functions [ExtractIndustryArticle]
  args {
    article_text #"
Title: Nvidia’s Christmas Present: GB300 & B300 – Reasoning Inference, Amazon, Memory, Supply Chain Blackwell Delays, Microsoft Orders, GB300 BOM, Nvidia Gross Margin, ConnectX-8, VRMs, Micron, Samsung, SK Hynix, Wistron, FII Foxconn, Aspeed, Axiado

Merry Christmas has come thanks to Santa Huang. Despite Nvidia’s Blackwell GPU’s having multiple delays, discussed here, and numerous times through the Accelerator Model due to silicon, packaging, and backplane issues, that hasn’t stopped Nvidia from continuing their relentless march.

They are bringing to market a brand-new GPU only 6 months after GB200 & B200, titled GB300 & B300. While on the surface it sounds incremental, there’s a lot more than meets the eye.

The changes are especially important because they include a huge boost to reasoning model inference and training performance. There is a special Christmas present from Nvidia to all the hyperscalers, especially Amazon, certain players in the supply chain, memory vendors, and their investors. The entire supply chain is reorganizing and shifting with the move to B300, bringing many winners presents, but also some losers get coal.

B300 & GB300 – Not Just An Incremental Upgrade

The B300 GPU is a brand-new tape out on the TSMC 4NP process node, IE it is a tweaked design, for the compute die. This enables the GPU to deliver 50% higher FLOPS versus the B200 on the product level. Some of this performance gain will come from 200W additional power with TDP going to 1.4KW and 1.2KW for the GB300 and B300 HGX respectively (compared to 1.2KW and 1KW for GB200 and B200).

The rest of the performance increase will come from architectural enhancements and system level enhancements such as power sloshing between CPU & GPU. Power sloshing is when the CPU and GPU dynamically reallocate power between the CPU and GPU  

In addition to more FLOPS, the memory is upgraded to 12-Hi HBM3E from 8-Hi growing the HBM capacity per GPU to 288GB. However, the pin speed will remain the same so memory bandwidth is still 8TB/s per GPU. Note Samsung is receiving coal from Santa, because they have no shot at getting into the GB200 or GB300 for at least another 9 months.

Furthermore, Nvidia, because they are in the Christmas spirit, the pricing of it is quite interesting. This shifts the margins of Blackwell, but more on pricing and margins later. Most important to discuss first is the performance changes.

Built For Reasoning Model Inference

The improvements to memory are key for OpenAI O3 style LLM Reasoning training and inference due to long sequence lengths growing KVCache, limiting critical batch sizes and latency. We explained this in our Scaling Laws defense piece where we discussed reasoning model training, synthetic data, inference, and much more.

The chart below shows improvements to tokenomics through Nvidia’s current generations of GPUs running on 1k input tokens, 19k output tokens, which is similar to a chain of thought in OpenAI’s o1 and o3 models. This demonstrative roofline simulation is run on LLAMA 405B at FP8 as it is the best public model we can simulate, with H100 and H200 GPUs, the GPUs we have access to.

When going from H100 to H200, which is purely only an upgrade with more, faster memory, there are two effects.

43% higher interactivity generally across all comparable batch sizes due to more memory bandwidth (H200 @ 4.8TB/s vs H100 @ 3.35TB/s).
~3x reduction in cost due to H200 running higher batch size then H100, enabling generation of 3x as many tokens per second. This difference is primarily because of KVCache limiting total batch size.
The dynamic of more memory capacity offering a seemingly disproportional benefit on to are massive. The performance and economic difference for the operator between the two GPUs is much larger than what the paper specs suggest:

Reasoning models can be a poor user experience due to significant waiting time between requests and responses. If you can offer significantly faster reasoning time, this will increase the user’s propensity to use and pay for them.
A 3x difference in cost is massive. Hardware delivering 3x with a mid-generation memory upgrade is frankly insane, way faster than Moore’s law, Huang’s Law, or any other pace of hardware improvement we’ve seen.
We have observed that the most capable and differentiated models are able to charge a significant premium over even slightly less capable models. Gross margins on frontier models are north of 70%, but on trailing models with open source competition, margins are below 20%. Reasoning models don’t have to be 1 chain of thought. Search exists and can be scaled up to improve performance as it has in O1 Pro and O3. This enables smarter models that can solve more problems and generate significantly more revenue per GPU.
Nvidia’s not the only one that can increase memory capacity of course. ASICs can do this and in fact AMD may be well positioned due to their higher memory capacity versus Nvidia generally with MI300X’s 192GB, MI325X 256GB, and MI350X 288GB… Well except Santa Huang has a Red-Nosed Reindeer called NVLink.

When we step forward to GB200 NVL72 and GB300 NVL72, the performance and cost for Nvidia based systems improve massively. The key point for using NVL72 in inference is because it enables 72 GPUs to work on the same problem, sharing their memory, at extremely low latency. No other accelerator in the world has all-to-all switched connectivity. No other accelerator in the world can do all reduce through a switch.

Nvidia’s GB200 NVL72 and GB300 NVL72 is incredibly important to enabling a number of key capabilities.

Much higher interactivity enabling lower latency per chain of thought.

72 GPUs to spread KVCache over to enable much longer chains of thought (increased intelligence).
Much better batch size scaling versus the typical 8 GPU servers, enabling much lower cost.
Many more samples to search with working on the same problem to improve accuracy and ultimately model performance.
As such, the tokenomics with NVL72 are more than 10x better, especially on long reasoning chains. KVCache eating up memory is a killer for economics, but NVL72 is the only way to scale reasoning lengths to 100k+ tokens at high batches.

Blackwell Supply Chain Reworked for GB300

With GB300, the supply chain and content that Nvidia supplies drastically changes. For the GB200 Nvidia provides the whole Bianca board (including the Blackwell GPU, Grace CPU, 512GB of LPDDR5X, VRM content all integrated onto one PCB) as well as the switch tray and copper backplane.

For GB300, instead of supplying the whole Bianca board, Nvidia will only supply the B300 on an “SXM Puck” module, the Grace CPU on a BGA package, and the HMC which will be from US based startup Axiado instead of Aspeed for GB200.

End customers will now directly procure the remaining components on the compute board and the second tier of memory will be LPCAMM modules instead of soldered-on LPDDR5X. Micron will be the main supplier of these modules.

The switch tray and copper backplane stays the same with Nvidia supplying these components entirely.

The shift to the SXM Puck opens up opportunities for more OEMs and ODMs to participate in the compute tray. Where previously only Wistron and FII could manufacture the Bianca compute board, now more OEMs and ODMs can. Wistron is the biggest loser in the form of ODMs as they lose share of the Bianca board. For FII, share loss at the Bianca board level is offset by the fact that they are the exclusive manufacturer of the SXM Puck and socket that the SXM Puck sits on. Nvidia is attempting to bring other suppliers for both the Puck and socket, but they have not placed any other orders yet.

Another major shift is with the VRM content. While there is some VRM content on the SXM Puck, much of the on board VRM content will be procured by Hyperscalers/OEMs directly from VRM suppliers. On October 25th for Core Research subscribers, we sent a note on how B300 was reshaping the supply chain specifically around Voltage Regulator Modules (“VRM”). We specifically called out how Monolithic Power Systems would lose market share due to the shift in business model and which new entrants were gaining market share. In the month following our note to 
s, the MPWR fell over 37% due to the market’s realization of the facts in our leading research.

Nvidia also offers the 800G ConnectX-8 NIC on the GB300 platform, offering twice the scale out bandwidth on InfiniBand and Ethernet. Nvidia cancelled ConnectX-8 for GB200 a while ago due to time to market complexities and foregoing enabling PCIe Gen 6 on the Bianca board.

ConnectX-8 offers a huge improvement versus ConnectX-7. Not only does it have 2x bandwidth, but it also has 48 PCIe lanes instead of 32 PCIe lanes, enabling unique architectures such as the air cooled MGX B300A. Furthermore, ConnectX-8 is SpectrumX capable whereas on the prior 400G generation, SpectrumX required much less efficient Bluefield 3 DPUs.

Hyperscaler Impacts with GB300

The hyperscaler impacts from delayed GB200 and GB300 mean that many orders starting in Q3 shift over to Nvidia’s new more expensive GPU. As of last week, all hyperscalers have decided to go forward with GB300. Partially this is due to the increased performance of GB300 due to higher FLOPS and more Memory, but also a portion of this is due to the ability to have control of their destiny.

Due to time to market challenges and significant changes in rack, cooling, and power delivery/density, hyperscalers were not allowed to change the GB200 much at the server level. This resulted in Meta abandoning all hope of being able to multi-source NICs from Broadcom and Nvidia in favor of relying solely on Nvidia. In other cases, such as Google, they abandoned their in-house NIC in favor of only going with Nvidia.

This is like nails on a chalkboard for the multi-thousand people organizations at hyperscalers who are used to cost optimizing everything from CPUs to networking down to screws and sheet metal.

The most egregious example was Amazon, who choose a very sub-optimal configurations that had worse TCO versus the reference design. Amazon specifically has not been able to deploy NVL72 racks like Meta, Google, Microsoft, Oracle, X.AI, and Coreweave due to the use of PCIe switches and less efficient 200G Elastic Fabric Adaptor NICs needing to be air cooled. Amazon due to their internal NICs had to use NVL36 which also costs more per GPU due to higher backplane and switch content. All in all, Amazon’s configuration was sub-optimal, due to their constraints around customization.

Now with GB300, hyperscalers are able to customize the main board, cooling, and much more. This enables Amazon to build their own custom mainboard which is watercooled with previously air-cooled components integrated such as the Astera Labs PCIe Switches. Watercooling more components alongside finally getting to HVM on the K2V6 400G NIC in Q3 25 means that Amazon can move back to NVL72 architecture and greatly improve their TCO.

There is one big downside though, which is that hyperscalers have to design, verify, and validate a ton more. This is easily the most complicated platform hyperscalers have ever had to design (save for Google’s TPU systems). Certain hyperscalers will be able to design this quickly, but others with slower teams are behind. Generally, despite market cancellation reports, we see Microsoft as one of the slowest to deploy GB300 due to design speed, with them still buying some GB200 in Q4.

The total price the customer pays differs a lot as components get pulled out of Nvidia’s margin stacking, onto ODMs. ODM’s revenue is impacted, and most importantly, Nvidia’s gross margin shifts through the year as well. Below we will show these impacts.
    "#
  }
}

test NullTest {
  functions [ExtractIndustryArticle]
  args {
    article_text #"
Title: Google New Custom Silicon Replaces 10 Million Intel CPUs | Google Argos VPU – SemiAnalysis

The trillion dollar tech companies are on a quest to become vertically integrated monsters. Google is no slouch on this front and has a myriad of custom and semi-custom silicon projects from the famous TPU for AI to the Titan security chip to upcoming releases such as Pixel/Chromebook SOCs, Arm Neoverse server CPUs, and Waymo self driving systems. Google has continued along their custom silicon ambitions by creating Argos, a new class of ASIC called VCU (Video Coding Unit). By deploying this custom silicon across their datacenters,  Google replaces millions of x86 CPUs  and enhance their service offerings. This custom silicon has been rolled out for quite some time and Google is already nearing deployment of their second generation VCU which will include enhancements such as AV1 encoding support. The VCU is designed specifically to accelerate video workloads across product offerings such as YouTube, Google Photos, Google Drive, and Stadia Game Streaming. While there is a greater demand for video sharing ability with greater resolutions and more volume, improvements in video processing are slow. Future growth in video acceleration is not sustainable without adopting domain specific hardware accelerators. Google received over 500 hours of YouTube footage every minute in May of 2019. This amounts to a gargantuan amount of data that must be encoded in standard formats, stored, and streamed out to users. Google takes input video and encodes it at every viewable resolution in H264. Additionally, the most viewed videos are also encoded in VP9. VP9 is a more complex video codec that allows a video file to become smaller and maintain the same picture quality. It can also store the video at the same size but be a higher quality video. VP9 allows Google to save large amounts of bandwidth that they stream out of their datacenter to the consumer through their content delivery network. This in turn lowers their costs drastically. If Google could switch entirely to VP9, they can also utilize less storage across their entire library of stored videos. This codec isn’t all positives though, CPUs struggle with encoding this format and are nearly 5x slower. Google provided encoding performance in their disclosure of this product. Using the quoted performance, if we assume that Google’s servers are utilized at 100% (they aren’t), all YouTube/Google Photos/Google Drive footage video is 1080p 30FPS, and the target is H264, the workload would require ~904,000 Intel Skylake server CPUs to encode. Google switching to VP9 with the same set of assumptions would require ~4,193,000 Intel Skylake server CPUs. If the ingest footage is 4k 60FPS, then the number of CPUs required for H264 is ~7,205,000, and VP9 requires ~33,407,000. The need for a purpose-built accelerators is obvious with CPUs simply being inadequate for the task at hand. Many would turn around and ask about GPUs. While they do provide slightly better TCO, they are also going to come with lower utilization rates and less flexibility of workloads for new encoding schemes such as VP9 and AV1. GPUs do not provide enough of an uplift to be worth using for this. This makes then unsuited to the task at hand as well. In comes Google’s Argos VPU, each of the Argos chips is packaged onto a single PCIe Card. 10 of these PCIe cards can be used in each single server. They offer significantly higher performance and power efficiency by being purpose built for the task at hand. One would assume that R&D costs would be huge, but all of the IP except for the encoder core is licensed from third parties. This significantly reduced costs and the time to engineer the solution. It was built using a modern mobile SOC methodology and point of view which allowed the rapid integration of IP from various sources. Core to the solution is hardware-software co-design. The system must be architected to function from the individual hardware encoder cores in each Argos chip all the way from the individual encoder cores and memory to entire chips, PCBAs, server nodes, clusters, and regions. Such deep integration is needed to maximize utilization rates, balance loads, deploy at scale, and be adaptable as the frameworks of the Google services, which are constantly tweaked. Each encoder and decoder core, and VCU memory controller can be divided to ensure full utilization. The hardware software co-design goes both ways. In addition to using an industry standard Electronic Design Automation (EDA) tool from Mentor Graphics’ called Catapult, Google also designed their own in-house tool for integration called Taffel.  Google’s ambitions for silicon independence are so broad they are developing their own EDA tools!  They still rely on the greater EDA industry, but to a lesser degree. Verification is upwards of 50% of costs when designing a chip, so SemiAnalysis believes the in-house tool likely targets this part of the silicon design process. With HLS, there was 5-10x less code to write, review, and maintain compared to a traditional Verilog approach. Google claims they have a flow that is far more efficient than the old tried and true Verilog approach. They also claim that testing throughput was accelerated by 7-8 orders of magnitude. Beyond the scope of this individual chip, Google clearly has long term ambitions to become a semiconductor monster through their vertically integrated, in-house chips. Rolling it all up, Google achieves a 7x improvement in total cost of ownership (TCO) for the infrastructure needed to encode videos on H.264, and a 33.3x improvement in VP9. This TCO improvement accounts for the cost of the chips plus 3 years of operational expenses. R&D costs are accounted for in this calculation for the VCU. Using the same assumptions of 100% utilization rates (which are totally unrealistic), if every video that Google received is encoded in VP9, the total number of Intel Skylake server CPUs required reaches ~4,192,000 assuming 1080p 30FPS quality. Google deploys 2 VCU’s per PCIe card and uses 10 cards per server. These servers still utilize 2 Intel Skylake CPUs as well. In order to encode all the video they receive at 1080p 30FPS quality, Google would need ~21,500 of these servers. These servers would total ~43,000 Intel Skylake server CPUs and ~430,000 of their in house Argos VPUs. That is 4 million fewer server CPUs that Google has to buy from Intel! If you assume the quality of uploaded footage is at 4k 60FPS, the reduction from ~33,407,000 Intel Skylake server CPU is even more mind boggling. They drop down to ~170,000 servers needed with ~340,000 total CPUs and ~3,400,000 Argos VPUs. The job of 33 million CPUs is now gone. We believe the average video uploaded to Google Photos and YouTube are likely not 4k 60FPS, but they also likely average out to higher than 1080P 30FPS. The Google VCU saves between 4 million and 33 million CPU purchases, but our estimate is around 10 million. This takes into account the fact that utilization rates are not 100% and that the average upload is slightly beyond 1080p 30FPS. These huge gains in cost and speed allowed Google to enable VP9 across all platforms, even on rarely watched videos. Storage and bandwidth egress costs are reduced significantly. They also can use VP9 for Google Stadia streaming which allows 4k 60 FPS gameplay streaming. What’s next for Google VCU? The next generation is already under the works according to SemiAnalysis sources. It will be able to encode the AV1 format which would be completely impossible on CPUs or GPUs. Further storage and bandwidth savings will be realized. Furthermore, they are planning to start adding machine learning inference hardware onto the new silicon as well. Lastly, they will also add networking onto the add in cards themselves in order to drive efficiency and reduce communications with the host CPU. This will allow them to automatically generate video captions, check for violations of terms of service, and even allow video search to be enabled on YouTube and Google Photos. The 10 million CPU savings are tangible now, but enabling these next generation features would be absolutely impossible without Google custom silicon. This will drive a tangible lead in video workloads over other tech companies, not just in cost, but also in capabilities. Amazon with Twitch.tv and Facebook/Instagram need to work on their own silicon for this workload or else they will be left in the dust competitively.  TikTok’s owner ByteDance is even working on their own silicon tailored to their video workloads.  Merchant silicon vendors such as Intel, Nvidia, and AMD are going to find themselves completely kicked out of the worlds largest tech companies video based workloads. This article was originally published on SemiAnalysis on June 2nd 2021 . Clients and employees of SemiAnalysis may hold positions in companies referenced in this article."#
    }
}

test DealTest {
  functions [ExtractIndustryArticle]
  args {
    article_text #"
Title: Nvidia to spend $500B to manufacture AI chips in US

The chipmaker will work with TSMC, Foxconn, Amkor and others to produce its Blackwell chip and other AI infrastructure in Arizona and Texas.

Nvidia President and CEO Jensen Huang speaks about the future of artificial intelligence at the Bipartisan Policy Center on Sept. 27, 2024, in Washington, D.C. The company now plans to produce AI chips in the U.S. for the first time.

Nvidia will manufacture some of its artificial intelligence chips in the United States for the first time, the company announced last week.

The chipmaker, which previously produced most of its chips in Taiwan, plans to invest up to $500 billion worth of AI infrastructure in the U.S. over the next four years. Nvidia will partner with contract manufacturers Taiwan Semiconductor Manufacturing Co., Foxconn, Wistron, Amkor and Silicon Precision Industries to build more than a million square feet of production space, and claims the investment will create hundreds of thousands of jobs. 

TSMC has already has begun producing Nvidia’s lauded Blackwell chip at its Arizona factory. Nvidia is partnering with Amkor and SPIL on packaging and testing operations in Arizona. Amkor announced plans in December 2023 to build a $2 billion packaging facility in the state.

Nvidia also is partnering with contract electronics manufacturer Foxconn in Houston and Taiwan-based Wistron in Dallas to build two supercomputer manufacturing plants. Production at both sites is expected to ramp up over the next 12 to 15 months, according to Nvidia.

The chipmaking giant has been teasing additional U.S. investments in recent weeks. Last month, CEO Jensen Huang told the Financial Times that the company planned to invest hundreds of billions of dollars in U.S. manufacturing over the next four years.

“The engines of the world’s AI infrastructure are being built in the United States for the first time,” Huang said in a statement. “Adding American manufacturing helps us better meet the incredible and growing demand for AI chips and supercomputers, strengthens our supply chain and boosts our resiliency.”

The announcement comes as the Trump administration is pushing hard for companies to increase U.S. manufacturing through its tariff regime.

Electronics makers received relief earlier this month, when President Donald Trump announced tariff exemptions for some electronics products, including smartphones, flat panel display modules and a broader list of electronic integrated circuits. The products will fall under a list of 20 harmonized tariff codes that qualify as “semiconductors.”

Electronics manufacturers have made a flurry of investment announcements since Trump took office. TSMC announced plans last month to invest $100 billion in U.S. manufacturing, including building multiple chip factories in Arizona. And Apple, which regularly contracts with Foxconn to produce iPhones and other goods in China, unveiled plans in February to invest $500 billion in U.S. manufacturing.
        "#
    }
}

test DataCentersTest {
  functions [ExtractIndustryArticle]
  args {
    article_text #"
     Title: Oracle to deploy cluster of more than 130,000 AMD MI355X GPUs - DCD

# Oracle to deploy cluster of more than 130,000 AMD MI355X GPUs

Cloud company's GB200 NVL72 supercluster also now available, and other Oracle news
Oracle is set to deploy an AI cluster with up to 131,072 of AMD's new MI355X GPUs.
The company has also made its Nvidia GB200 NVL72 supercluster available, signed a new customer partnership with Seekr, and is joining Nvidia's DGX Cloud Lepton platform.

## Oracle goes big on AMD

Oracle has announced that it will be offering the new AMD Instinct MI355X GPUs via Oracle Cloud Infrastructure (OCI), scalable up to a zettascale AI cluster of 131,072 GPUs.
According to Oracle, this will offer customers more than 2x better price-performance for large-scale AI training and inference workloads compared to the previous AMD GPU generation.
The cluster deployment builds on previous plans to deploy around30,000of the MI355X GPUs.
AMD officiallylaunchedthe MI355X GPUs on June 12 during its Advancing AI conference in San Jose, California.
Built using 3nm technology and based on AMD’s CDNA 4 architecture, the MI350 series offers 288GB of HBM3E and 8Tbps of memory bandwidth. Seventy-two teraflops of FP64 is provided by the MI350X and 79 teraflops for the MI355X, with the GPUs' total board power (TBP) up to 1,000W and 1,400W, respectively.
When compared to Nvidia’s GB200 and B200, AMD claimed its MI355X GPU provides 1.6x more memory capacity, 1x more memory bandwidth, and 2x more peak FP64 performance. The GPUs additionally offer a 4x generation-on-generation AI compute increase and a 35x generational improvement in inferencing.
Oracle claims it will be among the first hyperscalers to offer an AI supercomputer with the chips.
“To support customers that are running the most demanding AI workloads in the cloud, we are dedicated to providing the broadest AI infrastructure offerings,” said Mahesh Thiagarajan, executive vice president, Oracle Cloud Infrastructure. “AMD Instinct GPUs, paired with OCI’s performance, advanced networking, flexibility, security, and scale, will help our customers meet their inference and training needs for AI workloads and new agentic applications.”
“AMD and Oracle have a shared history of providing customers with open solutions to accommodate high performance, efficiency, and greater system design flexibility,” added Forrest Norrod, executive vice president and general manager, Data Center Solutions Business Group, AMD. “The latest generation of AMD Instinct GPUs and Pollara NICs on OCI will help support new use cases in inference, fine-tuning, and training, offering more choice to customers as AI adoption grows.”

## Nvidia GB200 NVL72 systems on OCI Supercluster now available, and more Nvidia news

Oracle has made the Nvidia GB200 NVL72 OCI Supercluster with 131,072 Blackwell GPUs generally available.
Plans for the massive cluster were first revealed inSeptember 2024, and while the GPUs were madeavailableearlier this year via OCI, the full cluster has now been deployed and is available for use.
The NVL72 systems are liquid-cooled. In addition to the Supercluster, the Blackwell GPUS are available via Nvidia DGX Cloud and OCI to run next-generation reasoning models and AI agents.
“Oracle has become the platform of choice for AI training and inferencing, and our work with Nvidia boosts our ability to support customers running some of the world’s most demanding AI workloads,” said Karan Batta, senior vice president, Oracle Cloud Infrastructure. “Combining Nvidia's full-stack AI computing platform with OCI’s performance, security, and deployment flexibility enables us to deliver AI capabilities at scale to help advance AI efforts globally.”
“Developers need the latest AI infrastructure and software to rapidly build and launch innovative solutions,” said Ian Buck, vice president of hyperscale and HPC, Nvidia. “With OCI and Nvidia, they get the performance and tools to bring ideas to life, wherever their work happens.”
Earlier this year, Oracle revealed it planned to deploy64,000Nvidia GB200s at the Stargate data center in Abilene, Texas, by the end of 2026.
Oracle has also revealed that it is joining theNvidia DGX Cloud Lepton, Nvidia's recently announced AI platform, with a compute marketplace that connects developers with a global network of GPU compute.
Other participants include CoreWeave, Crusoe, Firmus, Foxconn, GMI Cloud, Lambda, Nebius, Nscale, SoftBank Corp., and Yotta Data Services.

## Seekr selects Oracle and AMD for AI training

AI company Seekr has signed a multi-year agreement with OCI to use the cloud platform and AMD's MI300X GPUs.
Seekr will use OCI to expand its multi-node training capabilities for the next generation of large language models and AI agents designed for Edge deployments and vision-language foundation model training.
“OCI was the obvious choice as our international infrastructure partner,” said Rob Clark, president, Seekr. “Developing next-generation vision-language foundation models for top satellite providers and nation-states analyzing decades of imagery and sensor data requires massive raw GPU compute capacity. Oracle and AMD both came to the table with the infrastructure, top performance multi-node training compute, international presence, and the mindset that makes this possible.”
“Running multi-node training and inference efficiently, without overspending or sacrificing performance, can be a challenge for AI companies,” said Chris Gandolfo, executive vice president, Oracle Cloud Infrastructure and AI. “With OCI’s purpose-built AI infrastructure, Seekr is able to train LLMs more efficiently at a lower cost. In addition, we’re working closely with Seekr’s team on performance optimization, rapid model iteration, and global infrastructure expansion.”
Seekr and OCI are executing a joint go-to-market strategy.

## More in Cloud & Hyperscale

- Structure research report 2024 – 2025

# Structure research report 2024 – 2025

- 05 Mar 2025Proposal for .8bn data center put forward outside Spartanburg, South Carolina

# Proposal for .8bn data center put forward outside Spartanburg, South Carolina

- EpisodeThe data center energy challenge - What’s the role of investment?

# EpisodeThe data center energy challenge - What’s the role of investment?

## More in HPC & Quantum

- 03 Feb 2025UK's Met Office looks to sell Science Park including data center

# UK's Met Office looks to sell Science Park including data center

- 15 Jan 2025Business case not established for new supercomputer that forms part of UK government AI plan

# Business case not established for new supercomputer that forms part of UK government AI plan

- 29 Apr 2025IBM to spend bn on quantum & mainframes, as part of bn US investment pledge

# IBM to spend bn on quantum & mainframes, as part of bn US investment pledge

### Tags

- AMD Instinct MI355X
- Chris Gandalfo
- Forrest Norrod
- Ian Buck
- Karan Batta
- MI355X
- Mahesh Thiagarajan
- OCI
- Oracle
- Oracle Cloud Infrastructure
- Rob Clark
- Seekr
    "#
  }
}

test WikipediaTest {
    functions [ExtractIndustryArticle]
    args {
        article_text #"Nvidia Corporation ( en-VID-ee-ə) is an American technology company headquartered in Santa Clara, California. Founded in 1993 by Jensen Huang, Chris Malachowsky, and Curtis Priem, it develops graphics processing units (GPUs), system on a chips (SoCs), and application programming interfaces (APIs) for data science, high-performance computing, and mobile and automotive applications.
Originally focused on GPUs for video gaming, Nvidia broadened their use into other markets, including artificial intelligence (AI), professional visualization, and supercomputing. The company's product lines include GeForce GPUs for gaming and creative workloads, and professional GPUs for edge computing, scientific research, and industrial applications. As of the first quarter of 2025, Nvidia held a 92% share of the discrete desktop and laptop GPU market.
In the early 2000s, the company invested over a billion dollars to develop CUDA, a software platform and API that enabled GPUs to run massively parallel programs for a broad range of compute-intensive applications. As a result, as of 2025, Nvidia controlled more than 80% of the market for GPUs used in training and deploying AI models, and provided chips for over 75% of the world's TOP500 supercomputers. The company has also expanded into gaming hardware and services, with products such as the Shield Portable, Shield Tablet, and Shield TV, and operates the GeForce Now cloud gaming service. It also developed the Tegra line of mobile processors for smartphones, tablets, and automotive infotainment systems. 
In 2023, Nvidia became the seventh U.S. company to reach a US trillion valuation. In 2025, it became the first to surpass US trillion in market capitalization, driven by rising global demand for data center hardware in the midst of the AI boom. For its strength, size and market capitalization, Nvidia has been selected to be one of Bloomberg's "Magnificent Seven", the seven biggest companies on the stock market in these regards.

History
Founding
Nvidia was founded on April 5, 1993 as a competitor to AMD, by Jensen Huang (who remains CEO), a Taiwanese-American electrical engineer who was previously the director of CoreWare at LSI Logic and a microprocessor designer at AMD; Chris Malachowsky, an engineer who worked at Sun Microsystems; and Curtis Priem, who was previously a senior staff engineer and graphics chip designer at IBM and Sun Microsystems. At the time, Huang was running his own division at LSI, whereas Malachowsky and Priem were looking to leave their positions.  In late 1992, in a meeting at a Denny's roadside diner on Berryessa Road in East San Jose, the three men agreed to establish Nvidia with Huang as CEO.
The three co-founders envisioned  graphics-based processing as the best trajectory for tackling challenges that had eluded general-purpose computing methods. As Huang later explained: "We also observed that video games were simultaneously one of the most computationally challenging problems and would have incredibly high sales volume."
The founders resigned their previous posts in late 1992 – early 1993 to launch the company.   Huang left LSI and "officially joined Priem on February 17", which was also Huang's 30th birthday, while Malachowsky left Sun in early March.  In early 1993, the three founders began working together on their new start-up in Priem's townhouse in Fremont, California. With ,000 in the bank, the company was born. The company subsequently received  million of venture capital funding from Sequoia Capital, Sutter Hill Ventures and others. Nvidia initially had no name. After considering several names, they settled on ‘Nvidia’, derived from the Latin invidia (‘envy’).
During the late 1990s, Nvidia was one of 70 start-up companies pursuing the idea that graphics acceleration for video games was the path to the future.  Only two survived: Nvidia and ATI Technologies, the latter of which merged into AMD.
After the company outgrew Priem's townhouse, its original headquarters office was in Sunnyvale, California.

First graphics accelerator
Nvidia's first graphics accelerator, the NV1, was designed to process quadrilateral primitives (forward texture mapping), a feature that set it apart from competitors, who preferred triangle primitives. However, when Microsoft introduced the DirectX platform, it chose not to support any other graphics software and announced that its Direct3D API would exclusively support triangles. As a result, the NV1 failed to gain traction in the market.
Nvidia had also entered into a partnership with Sega to supply the graphics chip for the Dreamcast console and worked on the project for about a year. However, Nvidia's technology was already lagging behind competitors. This placed the company in a difficult position: continue working on a chip that was likely doomed to fail or abandon the project, risking financial collapse. In a pivotal moment, Sega's president, Shoichiro Irimajiri, visited Huang in person to inform him that Sega had decided to choose another vendor for the Dreamcast. However, Sega invested  million in Nvidia, providing crucial funding during the company's early financial difficulties.
In 1996, Huang laid off more than half of Nvidia's employees—thereby reducing headcount from 100 to 40—and focused the company's remaining resources on developing a graphics accelerator product optimized for processing triangle primitives: the RIVA 128.  By the time the RIVA 128 was released in August 1997, Nvidia had only enough money left for one month's payroll.
Nvidia sold about a million RIVA 128 units within four months, and used the revenue to fund development of its next generation of products. In 1998, the release of the RIVA TNT helped solidify Nvidia's reputation as a leader in graphics technology.

Public company
Nvidia went public on January 22, 1999.  Investing in Nvidia after it had already failed to deliver on its contract turned out to be Irimajiri's best decision as Sega's president. After Irimajiri left Sega in 2000, Sega sold its Nvidia stock for  million.
In late 1999, Nvidia released the GeForce 256 (NV10), its first product expressly marketed as a GPU, which was most notable for introducing onboard transformation and lighting (T&L) to consumer-level 3D hardware. Running at 120 MHz and featuring four-pixel pipelines, it implemented advanced video acceleration, motion compensation, and hardware sub-picture alpha blending. The GeForce outperformed existing products by a wide margin.
Due to the success of its products, Nvidia won the contract to develop the graphics hardware for Microsoft's Xbox game console, which earned Nvidia a  million advance. However, the project took many of its best engineers away from other projects. In the short term this did not matter, and the GeForce 2 GTS shipped in the summer of 2000. In December 2000, Nvidia reached an agreement to acquire the intellectual assets of its one-time rival 3dfx, a pioneer in consumer 3D graphics technology leading the field from the mid-1990s until 2000. The acquisition process was finalized in April 2002.
In 2001, Standard & Poor's selected Nvidia to replace the departing Enron in the S&P 500 stock index, meaning that index funds would need to hold Nvidia shares going forward.
In July 2002, Nvidia acquired Exluna for an undisclosed sum. Exluna made software-rendering tools and the personnel were merged into the Cg project. In August 2003, Nvidia acquired MediaQ for approximately US million. It launched GoForce the following year. On April 22, 2004, Nvidia acquired iReady, also a provider of high-performance TCP offload engines and iSCSI controllers. In December 2004, it was announced that Nvidia would assist Sony with the design of the graphics processor (RSX) for the PlayStation 3 game console. On December 14, 2005, Nvidia acquired ULI Electronics, which at the time supplied third-party southbridge parts for chipsets to ATI, Nvidia's competitor. In March 2006, Nvidia acquired Hybrid Graphics. In December 2006, Nvidia, along with its main rival in the graphics industry AMD (which had acquired ATI), received subpoenas from the U.S. Department of Justice regarding possible antitrust violations in the graphics card industry.

2007–2014
Forbes named Nvidia its Company of the Year for 2007, citing the accomplishments it made during the said period as well as during the previous five years. On January 5, 2007, Nvidia announced that it had completed the acquisition of PortalPlayer, Inc. In February 2008, Nvidia acquired Ageia, developer of PhysX, a physics engine and physics processing unit. Nvidia announced that it planned to integrate the PhysX technology into its future GPU products.
In July 2008, Nvidia took a write-down of approximately  million on its first-quarter revenue, after reporting that certain mobile chipsets and GPUs produced by the company had "abnormal failure rates" due to manufacturing defects. Nvidia, however, did not reveal the affected products. In September 2008, Nvidia became the subject of a class action lawsuit over the defects, claiming that the faulty GPUs had been incorporated into certain laptop models manufactured by Apple Inc., Dell, and HP. In September 2010, Nvidia reached a settlement, in which it would reimburse owners of the affected laptops for repairs or, in some cases, replacement. On January 10, 2011, Nvidia signed a six-year, .5 billion cross-licensing agreement with Intel, ending all litigation between the two companies.
In November 2011, after initially unveiling it at Mobile World Congress, Nvidia released its ARM-based system on a chip for mobile devices, Tegra 3. Nvidia claimed that the chip featured the first-ever quad-core mobile CPU. In May 2011, it was announced that Nvidia had agreed to acquire Icera, a baseband chip making company in the UK, for  million. In January 2013, Nvidia unveiled the Tegra 4, as well as the Nvidia Shield, an Android-based handheld game console powered by the new system on a chip. On July 29, 2013, Nvidia announced that they acquired PGI from STMicroelectronics.
In February 2013, Nvidia announced its plans to build a new headquarters in the form of two giant triangle-shaped buildings on the other side of San Tomas Expressway (to the west of its existing headquarters complex). The company selected triangles as its design theme. As Huang explained in a blog post, the triangle is "the fundamental building block of computer graphics".
In 2014, Nvidia ported the Valve games Portal and Half Life 2 to its Nvidia Shield Tablet as Lightspeed Studio. Since 2014, Nvidia has diversified its business focusing on three markets: gaming, automotive electronics, and mobile devices.
That same year, Nvidia also prevailed in litigation brought by the trustee of 3dfx's bankruptcy estate to challenge its 2000 acquisition of 3dfx's intellectual assets. On November 6, 2014, in an unpublished memorandum order, the U.S. Court of Appeals for the Ninth Circuit affirmed the "district court's judgment affirming the bankruptcy court's determination that [Nvidia] did not pay less than fair market value for assets purchased from 3dfx shortly before 3dfx filed for bankruptcy".

2016–2018
On May 6, 2016, Nvidia unveiled the first GPUs of the GeForce 10 series, the GTX 1080 and 1070, based on the company's new Pascal microarchitecture. Nvidia claimed that both models outperformed its Maxwell-based Titan X model; the models incorporate GDDR5X and GDDR5 memory respectively, and use a 16 nm manufacturing process. The architecture also supports a new hardware feature known as simultaneous multi-projection (SMP), which is designed to improve the quality of multi-monitor and virtual reality (VR) rendering. Laptops that include these GPUs and are sufficiently thin – as of late 2017, under 0.8 inches (20 mm) – have been designated as meeting Nvidia's "Max-Q" design standard.
In July 2016, Nvidia agreed to a settlement for a false advertising lawsuit regarding its GTX 970 model, as the models were unable to use all of their advertised 4 GB of VRAM due to limitations brought by the design of its hardware. In May 2017, Nvidia announced a partnership with Toyota which would use Nvidia's Drive PX-series artificial intelligence platform for its autonomous vehicles. In July 2017, Nvidia and Chinese search giant Baidu announced a far-reaching AI partnership that includes cloud computing, autonomous driving, consumer devices, and Baidu's open-source AI framework PaddlePaddle. Baidu unveiled that Nvidia's Drive PX 2 AI will be the foundation of its autonomous-vehicle platform.
Nvidia officially released the Titan V on December 7, 2017.
Nvidia officially released the Nvidia Quadro GV100 on March 27, 2018. Nvidia officially released the RTX 2080 GPUs on September 27, 2018. In 2018, Google announced that Nvidia's Tesla P4 graphic cards would be integrated into Google Cloud service's artificial intelligence.
In May 2018, on the Nvidia user forum, a thread was started asking the company to update users when they would release web drivers for its cards installed on legacy Mac Pro machines up to mid-2012 5,1 running the macOS Mojave operating system 10.14. Web drivers are required to enable graphics acceleration and multiple display monitor capabilities of the GPU. On its Mojave update info website, Apple stated that macOS Mojave would run on legacy machines with 'Metal compatible' graphics cards and listed Metal compatible GPUs, including some manufactured by Nvidia. However, this list did not include Metal compatible cards that currently work in macOS High Sierra using Nvidia-developed web drivers. In September, Nvidia responded, "Apple fully controls drivers for macOS. But if Apple allows, our engineers are ready and eager to help Apple deliver great drivers for macOS 10.14 (Mojave)." In October, Nvidia followed this up with another public announcement, "Apple fully controls drivers for macOS. Unfortunately, Nvidia currently cannot release a driver unless it is approved by Apple," suggesting a possible rift between the two companies. By January 2019, with still no sign of the enabling web drivers, Apple Insider weighed into the controversy with a claim that Apple management "doesn't want Nvidia support in macOS". The following month, Apple Insider followed this up with another claim that Nvidia support was abandoned because of "relational issues in the past", and that Apple was developing its own GPU technology. Without Apple-approved Nvidia web drivers, Apple users are faced with replacing their Nvidia cards with a competing supported brand, such as AMD Radeon from the list recommended by Apple.

2019 acquisition of Mellanox Technologies
On March 11, 2019, Nvidia announced a deal to buy Mellanox Technologies for .9 billion to substantially expand its footprint in the high-performance computing market. In May 2019, Nvidia announced new RTX Studio laptops. The creators say that the new laptop is going to be seven times faster than a top-end MacBook Pro with a Core i9 and AMD's Radeon Pro Vega 20 graphics in apps like Maya and RedCine-X Pro. In August 2019, Nvidia announced Minecraft RTX, an official Nvidia-developed patch for the game Minecraft adding real-time DXR ray tracing exclusively to the Windows 10 version of the game. The whole game is, in Nvidia's words, "refit" with path tracing, which dramatically affects the way light, reflections, and shadows work inside the engine.

2020–2023
In May 2020, Nvidia announced it was acquiring Cumulus Networks. Post acquisition the company was absorbed into Nvidia's networking business unit, along with Mellanox.
In May 2020, Nvidia's developed an open-source ventilator to address the shortage resulting from the global coronavirus pandemic. On May 14, 2020, Nvidia officially announced their Ampere GPU microarchitecture and the Nvidia A100 GPU accelerator. In July 2020, it was reported that Nvidia was in talks with SoftBank to buy Arm, a UK-based chip designer, for  billion.
On September 1, 2020, Nvidia officially announced the GeForce 30 series based on the company's new Ampere microarchitecture.
On September 13, 2020, Nvidia announced that they would buy Arm from SoftBank Group for  billion, subject to the usual scrutiny, with the latter retaining a 10% share of Nvidia.

In October 2020, Nvidia announced its plan to build the most powerful computer in Cambridge, England. The computer, called Cambridge-1, launched in July 2021 with a  million investment and will employ AI to support healthcare research. According to Jensen Huang, "The Cambridge-1 supercomputer will serve as a hub of innovation for the UK, and further the groundbreaking work being done by the nation's researchers in critical healthcare and drug discovery."
Also in October 2020, along with the release of the Nvidia RTX A6000, Nvidia announced it is retiring its workstation GPU brand Quadro, shifting its product name to Nvidia RTX for future products and the manufacturing to be Nvidia Ampere architecture-based.
In August 2021, the proposed takeover of Arm was stalled after the UK's Competition and Markets Authority raised "significant competition concerns". In October 2021, the European Commission opened a competition investigation into the takeover. The Commission stated that Nvidia's acquisition could restrict competitors' access to Arm's products and provide Nvidia with too much internal information on its competitors due to their deals with Arm. SoftBank (the parent company of Arm) and Nvidia announced in early February 2022 that they "had agreed not to move forward with the transaction 'because of significant regulatory challenges'". The investigation was set to end on March 15, 2022. That same month, Nvidia was reportedly compromised by a cyberattack. This would have been the largest semiconductor acquisition in history.
In March 2022, Nvidia's CEO Jensen Huang mentioned that they were open to having Intel manufacture their chips in the future. This was the first time the company mentioned that they would work together with Intel's upcoming foundry services.
In April 2022, it was reported that Nvidia planned to open a new research center in Yerevan, Armenia.
In May 2022, Nvidia opened Voyager, the second of the two giant buildings at its new headquarters complex to the west of the old one. Unlike its smaller and older sibling Endeavor, the triangle theming is used more "sparingly" in Voyager.
In September 2022, Nvidia announced its next-generation automotive-grade chip, Drive Thor.
In September 2022, Nvidia announced a collaboration with the Broad Institute of MIT and Harvard related to the entire suite of Nvidia's AI-powered healthcare software suite called Clara, that includes Parabricks and MONAI.
Following U.S. Department of Commerce regulations which placed an embargo on exports to China of advanced microchips, which went into effect in October 2022, Nvidia saw its data center chip added to the export control list. The next month, the company unveiled a new advanced chip in China, called the A800 GPU, that met the export control rules.
In September 2023, Getty Images announced that it was partnering with Nvidia to launch Generative AI by Getty Images, a new tool that lets people create images using Getty's library of licensed photos. Getty will use Nvidia's Edify model, which is available on Nvidia's generative AI model library Picasso.
On September 26, 2023, Denny's CEO Kelli Valade joined Huang in East San Jose to celebrate the founding of Nvidia at Denny's on Berryessa Road, where a plaque was installed to mark the relevant corner booth as the birthplace of a  trillion company. By then, Nvidia's H100 GPUs were in such demand that even other tech giants were beholden to how Nvidia allocated supply. Larry Ellison of Oracle Corporation said that month that during a dinner with Huang at Nobu in Palo Alto, he and Elon Musk of Tesla, Inc. and xAI "were begging" for H100s, "I guess is the best way to describe it. An hour of sushi and begging".
In October 2023, it was reported that Nvidia had quietly begun designing ARM-based central processing units (CPUs) for Microsoft's Windows operating system with a target to start selling them in 2025.

2024–2025
In January 2024, Forbes reported that Nvidia has increased its lobbying presence in Washington, D.C. as American lawmakers consider proposals to regulate artificial intelligence. From 2023 to 2024, the company reportedly hired at least four government affairs with professional backgrounds at agencies including the United States Department of State and the Department of the Treasury. It was noted that the ,000 spent by the company on lobbying in 2023 was small compared to a number of major tech companies in the artificial intelligence space.
In January 2024, Raymond James Financial analysts estimated that Nvidia was selling the H100 GPU in the price range of ,000 to ,000 each, while on eBay, individual H100s cost over ,000. Several major technology companies were purchasing tens or hundreds of thousands of GPUs for their data centers to run generative artificial intelligence projects; simple arithmetic implied that they were committing to billions of dollars in capital expenditures.
In February 2024, it was reported that Nvidia was the "hot employer" in Silicon Valley because it was offering interesting work and good pay at a time when other tech employers were downsizing. Half of Nvidia employees earned over ,000 in 2023. By then, Nvidia GPUs had become so valuable that they needed special security while in transit to data centers. Cisco chief information officer Fletcher Previn explained at a CIO summit: "Those GPUs arrive by armored car".
On March 1, 2024, Nvidia became the third company in the history of the United States to close with a market capitalization in excess of  trillion. Nvidia needed only 180 days to get to  trillion from  trillion, while the first two companies, Apple and Microsoft, each took over 500 days. On March 18, Nvidia announced its new AI chip and microarchitecture Blackwell, named after mathematician David Blackwell.
In April 2024, Reuters reported that China had allegedly acquired banned Nvidia chips and servers from Supermicro and Dell via tenders.
In June 2024, the Federal Trade Commission (FTC) and the Justice Department (DOJ) began antitrust investigations into Nvidia, Microsoft and OpenAI, focusing on their influence in the AI industry. The FTC led the investigations into Microsoft and OpenAI, while the DOJ handled Nvidia. The probes centered on the companies' conduct rather than mergers. This development followed an open letter from OpenAI employees expressing concerns about the rapid AI advancements and lack of oversight.
The company became the world's most valuable, surpassing Microsoft and Apple, on June 18, 2024, after its market capitalization exceeded .3 trillion.
In June 2024, Trend Micro announced a partnership with Nvidia to develop AI-driven security tools, notably to protect the data centers where AI workloads are processed. This collaboration integrates Nvidia NIM and Nvidia Morpheus with Trend Vision One and its Sovereign and Private Cloud solutions to improve data privacy, real-time analysis, and rapid threat mitigation.
In October 2024, Nvidia introduced a family of open-source multimodal large language models called NVLM 1.0, which features a flagship version with 72 billion parameters, designed to improve text-only performance after multimodal training.
In November 2024, the company was added to the Dow Jones Industrial Average.
In November 2024, Morgan Stanley reported that "the entire 2025 production" of all of Nvidia's Blackwell chips was "already sold out".
Also in November 2024, the company bought 1.2 million shares of Nebius Group.
Nvidia was ranked #3 on Forbes' "Best Places to Work" list in 2024.
As of January 7, 2025, Nvidia's .66 trillion market cap was worth more than double of the combined value of AMD, ARM, Broadcom, and Intel.
In January 2025, Nvidia saw the largest one-day loss in market capitalization for a U.S. company in history at  billion. This was due to DeepSeek, a Chinese AI start-up that developed an advanced AI model at a lower cost and computing power. DeepSeek's AI assistant, using the V3 model, surpassed ChatGPT as the highest-rated free app in the U.S. on Apple's App Store.
On April 7, 2025, Nvidia released the Llama-3.1-Nemotron-Ultra-253B-v1 reasoning large language model, under the Nvidia Open Model License. It comes in three sizes: Nano, Super and Ultra.
On May 28, 2025, Nvidia's second-quarter revenue forecast fell short of market estimates due to U.S. export restrictions impacting AI chip sales to China, yet the company's stock rose 5% as investors remained optimistic about long-term AI demand.
In July 2025, it was announced that NVIDIA had acquired CentL, a Canadian-based AI firm. 
On July 10, 2025, Nvidia closed for the first time with a market cap above  trillion, after its market cap briefly touched and then retreated from that number during the previous day.  Nvidia became the first company to reach a market cap of  trillion.  At that point, Nvidia was worth more than the combined value of all publicly traded companies in the United Kingdom.
On July 29, 2025, NVIDIA ordered 300,000 H20 AI chips from Taiwan Semiconductor Manufacturing Company (TSMC) due to strong demand from Chinese tech firms like Tencent and Alibaba.

Fabless manufacturing
Nvidia uses external suppliers for all phases of manufacturing, including wafer fabrication, assembly, testing, and packaging. Nvidia thus avoids most of the investment and production costs and risks associated with chip manufacturing, although it does sometimes directly procure some components and materials used in the production of its products (e.g., memory and substrates). Nvidia focuses its own resources on product design, quality assurance, marketing, and customer support.

Corporate affairs
Leadership
Nvidia's key management as of March 2024 consists of:

Jensen Huang, founder, president and chief executive officer
Chris Malachowsky, founder and Nvidia fellow
Colette Kress, executive vice president and chief financial officer
Jay Puri, executive vice president of worldwide field operations
Debora Shoquist, executive vice president of operations
Tim Teter, executive vice president, general counsel and secretary

Board of directors
As of November 2024, the company's board consisted of the following directors:

Rob Burgess (former chief executive officer of Macromedia Inc.)
Tench Coxe (former managing director of Sutter Hill Ventures)
John Dabiri (engineer and professor at the California Institute of Technology)
Persis Drell (physicist and professor at Stanford University)
Jensen Huang (co-founder, CEO and president of Nvidia)
Dawn Hudson (former Chief Marketing Officer of the National Football League)
Harvey C. Jones (managing partner of Square Wave Ventures)
Melissa B. Lora (former president of Taco Bell International)
Stephen Neal (lead independent director of Nvidia, former CEO and Chairman Emeritus and Senior Counsel of Cooley LLP)
Ellen Ochoa (former director of NASA Johnson Space Center)
Brooke Seawell (venture partner at New Enterprise Associates)
Aarti Shah (former Senior Vice President & Chief Information and Digital Officer at Eli Lilly and Company)
Mark Stevens (managing Partner at S-Cubed Capital)

Finances
For the fiscal year 2020, Nvidia reported earnings of US.796 billion, with an annual revenue of US.918 billion, a decline of 6.8% over the previous fiscal cycle. Nvidia's shares traded at over  per share, and its market capitalization was valued at over US.7 billion in January 2021. 
For the Q2 of 2020, Nvidia reported sales of .87 billion, which was a 50% rise from the same period in 2019. The surge in sales and people's higher demand for computer technology. According to the financial chief of the company, Colette Kress, the effects of the pandemic will "likely reflect this evolution in enterprise workforce trends with a greater focus on technologies, such as Nvidia laptops and virtual workstations, that enable remote work and virtual collaboration." In May 2023, Nvidia crossed  trillion in market valuation during trading hours, and grew to .2 trillion by the following November.

Ownership
The 10 largest shareholders of Nvidia in early 2024 were:

The Vanguard Group (8.280%)
BlackRock (5.623%)
Fidelity Investments (5.161%)
State Street Corporation (3.711%)
Jensen Huang (3.507%)
Geode Capital Management (2.024%)
T. Rowe Price (2.013%)
JPMorgan Chase (1.417%)
BlackRock Life (1.409%)
Eaton Vance (1.337%)

GPU Technology Conference
Nvidia's GPU Technology Conference (GTC) is a series of technical conferences held around the world. It originated in 2009 in San Jose, California, with an initial focus on the potential for solving computing challenges through GPUs. In recent years, the conference's focus has shifted to various applications of artificial intelligence and deep learning; including self-driving cars, healthcare, high-performance computing, and Nvidia Deep Learning Institute (DLI) training. GTC 2018 attracted over 8400 attendees. GTC 2020 was converted to a digital event and drew roughly 59,000 registrants. After several years of remote-only events, GTC in March 2024 returned to an in-person format in San Jose, California.

Product families
Nvidia's product families include graphics processing units, wireless communication devices, and automotive hardware and software, such as:

GeForce, consumer-oriented graphics processing products
RTX, professional visual computing graphics processing products (replacing GTX and Quadro)
NVS, a multi-display business graphics processor
Tegra, a system on a chip series for mobile devices
Tesla, line of dedicated general-purpose GPUs for high-end image generation applications in professional and scientific fields
nForce, a motherboard chipset created by Nvidia for Intel (Celeron, Pentium and Core 2) and AMD (Athlon and Duron) microprocessors
GRID, a set of hardware and services by Nvidia for graphics virtualization
Shield, a range of gaming hardware including the Shield Portable, Shield Tablet and Shield TV
Drive, a range of hardware and software products for designers and manufacturers of autonomous vehicles. The Drive PX-series is a high-performance computer platform aimed at autonomous driving through deep learning, while Driveworks is an operating system for driverless cars.
BlueField, a range of data processing units, initially inherited from their acquisition of Mellanox Technologies
Datacenter/server class CPU, codenamed Grace, released in 2023
DGX, an enterprise platform designed for deep learning applications
Maxine, a platform providing developers a suite of AI-based conferencing software

Open-source software support
Until September 23, 2013, Nvidia had not published any documentation for its advanced hardware, meaning that programmers could not write free and open-source device drivers for its products without resorting to reverse engineering.
Instead, Nvidia provides its own binary GeForce graphics drivers for X.Org and an open-source library that interfaces with the Linux, FreeBSD or Solaris kernels and the proprietary graphics software. Nvidia also provided but stopped supporting an obfuscated open-source driver that only supports two-dimensional hardware acceleration and ships with the X.Org distribution.
The proprietary nature of Nvidia's drivers has generated dissatisfaction within free-software communities. In a 2012 talk, Linus Torvalds gave a middle-finger gesture and criticized Nvidia’s stance toward Linux." Some Linux and BSD users insist on using only open-source drivers and regard Nvidia's insistence on providing nothing more than a binary-only driver as inadequate, given that competing manufacturers such as Intel offer support and documentation for open-source developers, and others like AMD release partial documentation and provide some active development.
Nvidia only provides x86/x64 and ARMv7-A versions of their proprietary driver; as a result, features like CUDA are unavailable on other platforms. Some users claim that Nvidia's Linux drivers impose artificial restrictions, like limiting the number of monitors that can be used at the same time, but the company has not commented on these accusations.
In 2014, with its Maxwell GPUs, Nvidia started to require firmware by them to unlock all features of its graphics cards.
On May 12, 2022, Nvidia announced that they are opensourcing their GPU kernel modules. Support for Nvidia's firmware was implemented in nouveau in 2023, which allows proper power management and GPU reclocking for Turing and newer graphics card generations.
In 21 July 2025, Nvidia announce to extend CUDA support to RISC-V.

List of Nvidia open-source projects
Nouveau
NVDLA
PhysX
VDPAU
Vibrante
GR00T

Deep learning
Nvidia GPUs are used in deep learning, and accelerated analytics due to Nvidia's CUDA software platform and API which allows programmers to utilize the higher number of cores present in GPUs to parallelize BLAS operations which are extensively used in machine learning algorithms. They were included in many Tesla, Inc. vehicles before Musk announced at Tesla Autonomy Day in 2019 that the company developed its own SoC and full self-driving computer now and would stop using Nvidia hardware for their vehicles. These GPUs are used by researchers, laboratories, tech companies and enterprise companies. In 2009, Nvidia was involved in what was called the "big bang" of deep learning, "as deep-learning neural networks were combined with Nvidia graphics processing units (GPUs)". That year, the Google Brain team used Nvidia GPUs to create deep neural networks capable of machine learning, where Andrew Ng determined that GPUs could increase the speed of deep learning systems by about 100 times.

DGX
DGX is a line of supercomputers by Nvidia.
In April 2016, Nvidia produced the DGX-1 based on an 8 GPU cluster, to improve the ability of users to use deep learning by combining GPUs with integrated deep learning software. Nvidia gifted its first DGX-1 to OpenAI in August 2016 to help it train larger and more complex AI models with the capability of reducing processing time from six days to two hours. It also developed Nvidia Tesla K80 and P100 GPU-based virtual machines, which are available through Google Cloud, which Google installed in November 2016. Microsoft added GPU servers in a preview offering of its N series based on Nvidia's Tesla K80s, each containing 4992 processing cores. Later that year, AWS's P2 instance was produced using up to 16 Nvidia Tesla K80 GPUs. That month Nvidia also partnered with IBM to create a software kit that boosts the AI capabilities of Watson, called IBM PowerAI. Nvidia also offers its own Nvidia Deep Learning software development kit. In 2017, the GPUs were also brought online at the Riken Center for Advanced Intelligence Project for Fujitsu. The company's deep learning technology led to a boost in its 2017 earnings.
In 2018, Nvidia researchers demonstrated imitation-learning techniques for industrial robots. They have created a system that, after a short revision and testing, can already be used to control the universal robots of the next generation. In addition to GPU manufacturing, Nvidia provides parallel processing capabilities to researchers and scientists that allow them to efficiently run high-performance applications.

Robotics
In 2020, Nvidia unveiled "Omniverse", a virtual environment designed for engineers. Nvidia also open-sourced Isaac Sim, which makes use of this Omniverse to train robots through simulations that mimic the physics of the robots and the real world.
In 2024, Huang oriented Nvidia's focus towards humanoid robots and self-driving cars, which he expects to gain widespread adoption.
In 2025, Nvidia announced Isaac GR00T N1, an open-source foundation model "designed to expedite the development and capabilities of humanoid robots". Neura Robotics, 1X Technologies and Vention are among the first companies to use the model.

Inception Program
Nvidia's Inception Program was created to support start-ups making exceptional advances in the fields of artificial intelligence and data science. Award winners are announced at Nvidia's GTC Conference. In May 2017, the program had 1,300 companies. As of March 2018, there were 2,800 start-ups in the Inception Program. As of August 2021, the program has over 8,500 members in 90 countries, with cumulative funding of US billion.

Reception
Maxwell advertising dispute
GTX 970 hardware specifications
Issues with the GeForce GTX 970's specifications were first brought up by users when they found out that the cards, while featuring 4 GB of memory, rarely accessed memory over the 3.5 GB boundary. Further testing and investigation eventually led to Nvidia issuing a statement that the card's initially announced specifications had been altered without notice before the card was made commercially available, and that the card took a performance hit once memory over the 3.5 GB limit were put into use.
The card's back-end hardware specifications, initially announced as being identical to those of the GeForce GTX 980, differed in the amount of L2 cache (1.75 MB versus 2 MB in the GeForce GTX 980) and the number of ROPs (56 versus 64 in the 980). Additionally, it was revealed that the card was designed to access its memory as a 3.5 GB section, plus a 0.5 GB one, access to the latter being 7 times slower than the first one. The company then went on to promise a specific driver modification to alleviate the performance issues produced by the cutbacks suffered by the card. However, Nvidia later clarified that the promise had been a miscommunication and there would be no specific driver update for the GTX 970. Nvidia claimed that it would assist customers who wanted refunds in obtaining them. On February 26, 2015, Nvidia CEO Jensen Huang went on record in Nvidia's official blog to apologize for the incident. In February 2015 a class-action lawsuit alleging false advertising was filed against Nvidia and Gigabyte Technology in the U.S. District Court for Northern California.
Nvidia revealed that it is able to disable individual units, each containing 256 KB of L2 cache and 8 ROPs, without disabling whole memory controllers. This comes at the cost of dividing the memory bus into high speed and low speed segments that cannot be accessed at the same time unless one segment is reading while the other segment is writing because the L2/ROP unit managing both of the GDDR5 controllers shares the read return channel and the write data bus between the two GDDR5 controllers and itself. This is used in the GeForce GTX 970, which therefore can be described as having 3.5 GB in its high speed segment on a 224-bit bus and 0.5 GB in a low speed segment on a 32-bit bus.
On July 27, 2016, Nvidia agreed to a preliminary settlement of the U.S. class action lawsuit, offering a  refund on GTX 970 purchases. The agreed upon refund represents the portion of the cost of the storage and performance capabilities the consumers assumed they were obtaining when they purchased the card.

GeForce Partner Program
The Nvidia GeForce Partner Program was a marketing program designed to provide partnering companies with benefits such as public relations support, video game bundling, and marketing development funds. The program proved to be controversial, with complaints about it possibly being an anti-competitive practice.
First announced in a blog post on March 1, 2018, it was canceled on May 4, 2018.

Hardware Unboxed
On December 10, 2020, Nvidia told YouTube tech reviewer Steven Walton of Hardware Unboxed that it would no longer supply him with GeForce Founders Edition graphics card review units. In a Twitter message, Hardware Unboxed said, "Nvidia have officially decided to ban us from receiving GeForce Founders Edition GPU review samples. Their reasoning is that we are focusing on rasterization instead of ray tracing. They have said they will revisit this 'should your editorial direction change.'"

In emails that were disclosed by Walton from Nvidia Senior PR Manager Bryan Del Rizzo, Nvidia had said:...your GPU reviews and recommendations have continued to focus singularly on rasterization performance, and you have largely discounted all of the other technologies we offer gamers. It is very clear from your community commentary that you do not see things the same way that we, gamers, and the rest of the industry do.TechSpot, partner site of Hardware Unboxed, said, "this and other related incidents raise serious questions around journalistic independence and what they are expecting of reviewers when they are sent products for an unbiased opinion."
A number of technology reviewers came out strongly against Nvidia's move. Linus Sebastian, of Linus Tech Tips, titled the episode of his weekly WAN Show, "NVIDIA might ACTUALLY be EVIL..." and was highly critical of the company's move to dictate specific outcomes of technology reviews. The review site Gamers Nexus said it was, "Nvidia's latest decision to shoot both its feet: They've now made it so that any reviewers covering RT will become subject to scrutiny from untrusting viewers who will suspect subversion by the company. Shortsighted self-own from NVIDIA."
Two days later, Nvidia reversed their stance. Hardware Unboxed sent out a Twitter message, "I just received an email from Nvidia apologizing for the previous email & they've now walked everything back." On December 14, Hardware Unboxed released a video explaining the controversy from their viewpoint. Via Twitter, they also shared a second apology sent by Nvidia's Del Rizzo that said "to withhold samples because I didn't agree with your commentary is simply inexcusable and crossed the line."

Improper disclosures about cryptomining
In 2018, Nvidia's chips became popular for cryptomining, the process of obtaining crypto rewards in exchange for verifying transactions on distributed ledgers, the U.S. Securities and Exchange Commission (SEC) said. However, the company failed to disclose that it was a "significant element" of its revenue growth from sales of chips designed for gaming, the SEC further added in a statement and charging order. Those omissions misled investors and analysts who were interested in understanding the impact of cryptomining on Nvidia's business, the SEC emphasized. Nvidia, which did not admit or deny the findings, has agreed to pay .5 million to settle civil charges, according to a statement made by the SEC in May 2022.

French Competition Authority Investigation
On September 26, 2023, Nvidia's French offices were searched by the French Competition Authority. The raid, authorized by a judge, was part of an investigation into suspected anti-competitive practices in the graphics card sector. Nvidia has not publicly commented on the incident.

AI regulation dispute with Anthropic
In July 2025, a public dispute emerged between Nvidia CEO Jensen Huang and Anthropic CEO Dario Amodei over AI regulation and industry practices. The conflict escalated when Amodei vehemently denied Huang's allegations that he sought to control the AI industry through safety concerns, calling Huang's claims an "outrageous lie." The dispute centered on differing philosophies regarding AI development, with Amodei advocating for stronger regulatory oversight and "responsible scaling policies," while Huang promoted open-source development and criticized what Nvidia characterized as "regulatory capture." Nvidia responded by stating that "lobbying for regulatory capture against open source will only stifle innovation, make AI less safe and secure, and less democratic." The controversy highlighted broader tensions within the AI industry between companies favoring rapid development and those emphasizing safety measures and regulation.

Proposed Shanghai facility
In May 2025, U.S. senators Jim Banks and Elizabeth Warren criticized a proposed Nvidia facility in Shanghai, saying that it "raises significant national security and economic security issues that warrant serious review."

See also
Notes
References
Further reading
Witt, Stephen (2025). The Thinking Machine: Jensen Huang, Nvidia, and the World's Most Coveted Microchip. Penguin Publishing Group. ISBN 9780593832691.

External links

Official website 
Nvidia Developer website
Nvidia on OpenSecrets, a website that tracks and publishes data on campaign finance and lobbying 
Business data for Nvidia: 
After Words interview with Stephen Witt on The Thinking Machine: Jensen Huang, Nvidia, and the World's Most Coveted Microchip, April 25, 2025, C-SPAN
GeForce logo history at 1000logos"#
    }
}