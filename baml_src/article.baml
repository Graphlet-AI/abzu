
// This is a BAML config file, which extends the Jinja2 templating language to write LLM functions.

class IndustryArticle {
  
  title string
  @description("Title of the article")

  url string?
  @description("URL of the article")

  source NewsSource?
  @description("Source of the article. This is the news source that published the article.")

  collected_at string?
  @description("Date the article was collected, in ISO-8601 format")
  
  posted_at string?
  @description("Date the article was published, in ISO-8601 format")

  authors Author[]?
  @description("Authors of the article")

  summary string
  @description("Summary of the article")

  companies Company[]?
  @description("Companies mentioned in the article")

  tickers Ticker[]?
  @description("Ticker symbols of the companies mentioned in the article")

  partnerships Partnership[]?
  @description("Partnerships mentioned in the article")

  customers Customer[]?
  @description("Customer relationships mentioned in the article")

  investors Investor[]?
  @description("Investor relationships mentioned in the article")

  products Product[]?
  @description("Products mentioned in the article")

  technologies Technology[]?
  @description("Technologies mentioned in the article. Technologies does not include products")

  deals Deal[]?
  @description("Commercial deals mentioned in the article: sales, acquisitions or investments.")

  cited_sources NewsSource[]?
  @description("News sources mentioned in the article. This is a news source that was quoted or linked to. This is not the source of the article.")
}

class Author {
  name string
  @description("Name of the author")

  profile_url string?
  @description("URL of the author's profile")
}

class Ticker {
  name string
  @description("Name of the company")

  symbol string
  @description("Ticker symbol of the company if publicly traded")

  exchange string?
  @description("Exchange where the company is traded")
}

class Company {
  name string
  @description("Formal name of the company with company suffix")

  ticker Ticker?
  @description("Ticker symbol of the company if publicly traded")

  description string
  @description("Description of the company")

  website_url string?
  @description("URL of the company's website")

  headquarters_location string?
  @description("Location of the company's headquarters")

  revenue_usd int?
  @description("Revenue of the company in USD")

  employees int?
  @description("Number of employees of the company")

  founded_year int?
  @description("Year the company was founded")

  ceo string?
  @description("Name of the company's CEO")

  linkedin_url string?
  @description("LinkedIn URL of the company")
}

class Product {
  name string
  @description("Name of the company's product")

  description string
  @description("Description of the product. What does it do? What is it used for?")

  manufacturer Company
  @description("Name of the company that makes the product")
}

class Technology {
  name string
  @description("Name of the technology")

  developer Company
  @description("Name of the company that invented or developed the technology")

  description string
  @description("Description of the technology. What does it do? What is it used for?")
}

class Partnership {
  src_company Company
  @description("First company in partnership")

  dst_company Company
  @description("Second company in partnership")

  value int
  @description("Value of the partnership in currency. This is the amount of money that will flow through the partnership. This is not the valuation of the company.")

  currency string
  @description("Currency of the value of a partnership. ISO 4217 3-letter currency code")

  description string
  @description("Description of the partnership. What is its purpose?")
}

class Customer {
  src_company Company
  @description("Selling company")

  dst_company Company
  @description("Buying company")

  value int
  @description("Value of the buyer's account in currency to the selling company. This is a valuation of the relationship.")

  currency string
  @description("Currency of the customer relationship's transactions. ISO 4217 3-letter currency code")

  technologies Technology[]?
  @description("Technologies involved in the customer relationship. This is a technology that was bought or sold.")

  products Product[]?
  @description("Products involved in the customer relationship. This is a product that was bought, licensed or sold.")

  description string
  @description("Description of the customer relationship: what is bought or sold? How much?")
}

class Investor {
  src_company Company
  @description("Company making the investment")

  dst_company Company
  @description("Company receiving the investment")

  amount int
  @description("Amount of the investment in currency. This is the amount of money that changed hands in the investment. This is not the valuation of the company.")

  currency string
  @description("Currency of the investment amount. ISO 4217 3-letter currency code")

  description string
  @description("Description of the investment")
}

enum DealType {
  Sale @description("Sale of a product or technology")
  Acquisition @description("Acquisition of a company")
  Investment @description("Investment in a company or country")
}

class Deal {
  src_company Company
  @description("Source company in the deal. This is the company that sold a product or technology (Sale type), acquired another company (Acquisition type) or made an investment (Investment type).")

  dst_company Company?
  @description("Target company in the deal. This is the company that bought a product or technology (Sale type), the company that was acquired (Acquisition type) or received investment (Investment type). Some investments don't have recipients if they relate only to a location.")

  technologies Technology[]?
  @description("Technologies involved in the deal. This is the technology that was sold, acquired or invested in.")

  products Product[]?
  @description("Products involved in the deal. This is the product that was sold, acquired or invested in.")

  type DealType
  @description("Type of the deal: Sale, Acquisition or Investment. No partnerships.")

  description string
  @description("Description of the deal. What was bought, sold or invested in and by who? For how much money in which currency?")

  amount int
  @description("Amount of the deal in currency. This is the amount of money that changed hands in the deal. This is not the valuation of the company. Expand millions, billions or trillions to whole figures.")

  currency string
  @description("Currency of the deal amount. ISO 4217 3-letter currency code")

  country string?
  @description("Country of the deal. This is the country where the deal took place. This may be the country of any dst_company in a Sale, Acquisition or Investment.")

  date string
  @description("Date of the deal in ISO-8601 format")

  quarter string?
  @description("Actual or projected quarter of the deal in ISO-8601 format. This is the quarter of the year when the deal took place or will take place.")
}

class NewsSource {
  name string
  @description("Name of the news source. Newspaper, magazine, blog, etc.")

  url string?
  @description("URL of the web page of the news source")
}

function ExtractIndustryArticle(article_text: string) -> IndustryArticle {
  // see clients.baml
  client CustomGeminiFallback

  // The prompt uses Jinja syntax. Change the models or this text and watch the prompt preview change!
  prompt #"
    Parse the following article, perform information extraction to return a structured representation of the data in the schema below. Include only the information that is explicitly stated in the article except in the description fields, where you can give a generic description of an entity. Skip all fields that would be null, unless they are REQUIRED.

    {# special macro to print the output instructions. #}
    {{ ctx.output_format(hoist_classes=["Company", "Ticker", "Product", "Technology", "Partnership", "Customer", "Investor", "Deal", "NewsSource", "Author"]) }}

    {{ _.role("user") }}
    {{ article_text }}
  "#
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