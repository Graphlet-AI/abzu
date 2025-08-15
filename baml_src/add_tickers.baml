class TickerList {
  tickers Ticker[]
}

function AddTickersToCompanies(company_list: CompanyList, ticker_list: TickerList) -> CompanyList {
  // see clients.baml
  client CustomGeminiFallback

  // The prompt uses Jinja syntax. Change the models or this text and watch the prompt preview change!
  prompt #"
    Examine the following sets of companies and tickers and match the tickers with the companies based on their names representing the same entity. Merge the matched records, adding a Ticker to each Company that matches. If the company name in the ticker differs from the company name, use the full corporate name.

    Return a set of companies with tickers merged into the ticker field.

    {# special macro to print the output instructions. #}
    {{ ctx.output_format(hoist_classes=["Company", "Ticker", "CompanyList"]) }}

    {{ _.role("user") }}

    Company List: {{ company_list }}
    Ticker List: {{ ticker_list }}
  "#
}

test BasicTest {
    functions [AddTickersToCompanies]
    args {
        company_list {
            companies [
                {
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
                }
                {
                    name "AMD"
                    ticker null
                    description "A company that designs and manufactures high-performance computing products, including the Instinct series of GPUs (like the MI355X) for AI and data centers."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                }
                {
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
                }
                {
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
            ]
        }
        ticker_list {
            tickers [
                {
                    name "Advanced Micro Devices Inc"
                    symbol "AMD"
                    exchange "NASDAQ"
                }
                {
                    name "Ares Acquisition Corp"
                    symbol "AAC"
                    exchange "NYSE"
                }
                {
                    name "Armada Acquisition Corp I"
                    symbol "AACI"
                    exchange "NASDAQ"
                }
                {
                    name "Australia Acquisition Corp"
                    symbol "AACPF"
                    exchange "NASDAQ"
                }
                {
                    name "Ares Acquisition Corp Ii"
                    symbol "AACT"
                    exchange "NYSE"
                }
                {
                    name "Airtran Holdings Inc"
                    symbol "AAI"
                    exchange "NASDAQ"
                }
                {
                    name "Aqua Alliance Inc"
                    symbol "AAI1"
                    exchange "NYSEMKT"
                }
                {
                    name "Alabama Aircraft Industries Inc"
                    symbol "AAIIQ"
                    exchange "NASDAQ"
                }
                {
                    name "American Airlines Group Inc"
                    symbol "AAL"
                    exchange "NASDAQ"
                }
                {
                    name "Aa Mission Acquisition Corp"
                    symbol "AAM"
                    exchange "NYSE"
                }
                {
                    name "Amr Corp"
                    symbol "AAMRQ"
                    exchange "NYSE"
                }
                {
                    name "Aaron'S Company Inc"
                    symbol "AAN"
                    exchange "NYSE"
                }
                {
                    name "Applied Optoelectronics Inc"
                    symbol "AAOI"
                    exchange "NASDAQ"
                }
                {
                    name "Apple Inc"
                    symbol "AAPL"
                    exchange "NASDAQ"
                }
                {
                    name "Accelerate Acquisition Corp"
                    symbol "AAQC"
                    exchange "NYSE"
                }
                {
                    name "Autoscope Technologies Corp"
                    symbol "AATC"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Analogic Technologies Inc"
                    symbol "AATI"
                    exchange "NASDAQ"
                }
                {
                    name "Analysis & Technology Inc"
                    symbol "AATI1"
                    exchange "NASDAQ"
                }
                {
                    name "Aavid Thermal Technologies Inc"
                    symbol "AATT"
                    exchange "NASDAQ"
                }
                {
                    name "Advantage Oil & Gas Ltd"
                    symbol "AAVVF"
                    exchange "NYSE"
                }
                {
                    name "Atlas Air Worldwide Holdings Inc"
                    symbol "AAWHQ"
                    exchange "NASDAQ"
                }
                {
                    name "Atlas Air Worldwide Holdings Inc"
                    symbol "AAWW"
                    exchange "NASDAQ"
                }
                {
                    name "Abacan Resource Corp"
                    symbol "ABACQ"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Battery Technologies Inc"
                    symbol "ABAT1"
                    exchange "NASDAQ"
                }
                {
                    name "Abb Ltd"
                    symbol "ABBNY"
                    exchange "NYSE"
                }
                {
                    name "Abc Dispensing Technologies Inc"
                    symbol "ABCC"
                    exchange "NASDAQ"
                }
                {
                    name "Abacus Direct Corp"
                    symbol "ABDR1"
                    exchange "NASDAQ"
                }
                {
                    name "Airborne Inc"
                    symbol "ABF"
                    exchange "NYSE"
                }
                {
                    name "Abengoa Sa"
                    symbol "ABGBY"
                    exchange "NASDAQ"
                }
                {
                    name "Abg Acquisition Corp I"
                    symbol "ABGI"
                    exchange "NASDAQ"
                }
                {
                    name "American Bank Note Holographics Inc"
                    symbol "ABHH"
                    exchange "NYSE"
                }
                {
                    name "Ability Inc"
                    symbol "ABILF"
                    exchange "NASDAQ"
                }
                {
                    name "Abatix Corp"
                    symbol "ABIX"
                    exchange "NASDAQ"
                }
                {
                    name "Abm Industries Inc"
                    symbol "ABM"
                    exchange "NYSE"
                }
                {
                    name "Airbnb Inc"
                    symbol "ABNB"
                    exchange "NASDAQ"
                }
                {
                    name "American Banknote Corp"
                    symbol "ABNTQ"
                    exchange "NYSE"
                }
                {
                    name "Abovenet Communications Inc"
                    symbol "ABOV"
                    exchange "NASDAQ"
                }
                {
                    name "Abr Information Services Inc"
                    symbol "ABRX1"
                    exchange "NASDAQ"
                }
                {
                    name "Absolute Software Corp"
                    symbol "ABST"
                    exchange "NASDAQ"
                }
                {
                    name "Able Telcom Holding Corp"
                    symbol "ABTE"
                    exchange "NASDAQ"
                }
                {
                    name "Arcosa Inc"
                    symbol "ACA"
                    exchange "NYSE"
                }
                {
                    name "Atlantic Coastal Acquisition Corp Ii"
                    symbol "ACAB"
                    exchange "NASDAQ"
                }
                {
                    name "Acri Capital Acquisition Corp"
                    symbol "ACAC"
                    exchange "NASDAQ"
                }
                {
                    name "Atlantic Coastal Acquisition Corp"
                    symbol "ACAH"
                    exchange "NASDAQ"
                }
                {
                    name "Athena Consumer Acquisition Corp"
                    symbol "ACAQ"
                    exchange "NYSE"
                }
                {
                    name "Arctic Cat Inc"
                    symbol "ACAT"
                    exchange "NASDAQ"
                }
                {
                    name "Ace Global Business Acquisition Ltd"
                    symbol "ACBA"
                    exchange "NASDAQ"
                }
                {
                    name "Accord Networks Ltd"
                    symbol "ACCD1"
                    exchange "NASDAQ"
                }
                {
                    name "Accelrys Inc"
                    symbol "ACCL"
                    exchange "NASDAQ"
                }
                {
                    name "Acco Brands Corp"
                    symbol "ACCO"
                    exchange "NYSE"
                }
                {
                    name "Profrac Holding Corp"
                    symbol "ACDC"
                    exchange "NASDAQ"
                }
                {
                    name "Ascendant Digital Acquisition Corp Iii"
                    symbol "ACDI"
                    exchange "NYSE"
                }
                {
                    name "Ace Comm Corp"
                    symbol "ACEC"
                    exchange "NASDAQ"
                }
                {
                    name "Acme Electric Corp"
                    symbol "ACEE"
                    exchange "NASDAQ"
                }
                {
                    name "Acorn Energy Inc"
                    symbol "ACFN"
                    exchange "NASDAQ"
                }
                {
                    name "Archer Aviation Inc"
                    symbol "ACHR"
                    exchange "NYSE"
                }
                {
                    name "Acacia Communications Inc"
                    symbol "ACIA"
                    exchange "NASDAQ"
                }
                {
                    name "Atlas Crest Investment Corp Ii"
                    symbol "ACII"
                    exchange "NYSE"
                }
                {
                    name "Aci Worldwide Inc"
                    symbol "ACIW"
                    exchange "NASDAQ"
                }
                {
                    name "Ackrell Spac Partners I Co"
                    symbol "ACKIU"
                    exchange "NASDAQ"
                }
                {
                    name "Aclara Biosciences Inc"
                    symbol "ACLA"
                    exchange "NASDAQ"
                }
                {
                    name "American Commercial Lines Inc"
                    symbol "ACLI"
                    exchange "NASDAQ"
                }
                {
                    name "Acln Ltd"
                    symbol "ACLNF"
                    exchange "NASDAQ"
                }
                {
                    name "Accelio Corp"
                    symbol "ACLO"
                    exchange "NASDAQ"
                }
                {
                    name "Axcelis Technologies Inc"
                    symbol "ACLS"
                    exchange "NASDAQ"
                }
                {
                    name "Aecom"
                    symbol "ACM"
                    exchange "NYSE"
                }
                {
                    name "Accom Inc"
                    symbol "ACMM"
                    exchange "NASDAQ"
                }
                {
                    name "Acm Research Inc"
                    symbol "ACMR"
                    exchange "NASDAQ"
                }
                {
                    name "Accenture Plc"
                    symbol "ACN"
                    exchange "NYSE"
                }
                {
                    name "Air Canada"
                    symbol "ACNAQ"
                    exchange "NASDAQ"
                }
                {
                    name "Amcol International Corp"
                    symbol "ACO"
                    exchange "NYSE"
                }
                {
                    name "Ancestrycom Inc"
                    symbol "ACOM"
                    exchange "NASDAQ"
                }
                {
                    name "Agency Com Ltd"
                    symbol "ACOM1"
                    exchange "NASDAQ"
                }
                {
                    name "Independence Holdings Corp"
                    symbol "ACQR"
                    exchange "NASDAQ"
                }
                {
                    name "Acropolis Infrastructure Acquisition Corp"
                    symbol "ACRO"
                    exchange "NYSE"
                }
                {
                    name "Acrodyne Communications Inc"
                    symbol "ACRO1"
                    exchange "NASDAQ"
                }
                {
                    name "Accrue Software Inc"
                    symbol "ACRUQ"
                    exchange "NASDAQ"
                }
                {
                    name "Affiliated Computer Services Inc"
                    symbol "ACS"
                    exchange "NYSE"
                }
                {
                    name "Advanced Communication Systems Inc"
                    symbol "ACSC"
                    exchange "NASDAQ"
                }
                {
                    name "Acs - Tech 80 Ltd"
                    symbol "ACSEF"
                    exchange "NASDAQ"
                }
                {
                    name "Actua Corp"
                    symbol "ACTA"
                    exchange "NASDAQ"
                }
                {
                    name "Acacia Research Corp"
                    symbol "ACTG"
                    exchange "NASDAQ"
                }
                {
                    name "Actividentity Corp"
                    symbol "ACTI"
                    exchange "NASDAQ"
                }
                {
                    name "Activcard Sa"
                    symbol "ACTI1"
                    exchange "NASDAQ"
                }
                {
                    name "Actel Corp"
                    symbol "ACTL1"
                    exchange "NASDAQ"
                }
                {
                    name "Acterna Corp"
                    symbol "ACTRQ"
                    exchange "NASDAQ"
                }
                {
                    name "Actions Semiconductor Co Ltd"
                    symbol "ACTS"
                    exchange "NASDAQ"
                }
                {
                    name "Actv Inc"
                    symbol "ACTV1"
                    exchange "NASDAQ"
                }
                {
                    name "Active Network Inc"
                    symbol "ACTV2"
                    exchange "NYSE"
                }
                {
                    name "Active Voice Corp"
                    symbol "ACVC"
                    exchange "NASDAQ"
                }
                {
                    name "Advo Inc"
                    symbol "AD"
                    exchange "NYSE"
                }
                {
                    name "Anthemis Digital Acquisitions I Corp"
                    symbol "ADAL"
                    exchange "NASDAQ"
                }
                {
                    name "Adam Inc"
                    symbol "ADAM"
                    exchange "NASDAQ"
                }
                {
                    name "Adaptive Broadband Corp"
                    symbol "ADAPQ"
                    exchange "NASDAQ"
                }
                {
                    name "Applied Digital Access Inc"
                    symbol "ADAX"
                    exchange "NASDAQ"
                }
                {
                    name "Adobe Inc"
                    symbol "ADBE"
                    exchange "NASDAQ"
                }
                {
                    name "Audible Inc"
                    symbol "ADBL"
                    exchange "NASDAQ"
                }
                {
                    name "Andean Development Corp"
                    symbol "ADCC"
                    exchange "NASDAQ"
                }
                {
                    name "Adc Telecommunications Inc"
                    symbol "ADCT1"
                    exchange "NASDAQ"
                }
                {
                    name "Adeia Inc"
                    symbol "ADEA"
                    exchange "NASDAQ"
                }
                {
                    name "Adept Technology Inc"
                    symbol "ADEP"
                    exchange "NASDAQ"
                }
                {
                    name "26 Capital Acquisition Corp"
                    symbol "ADER"
                    exchange "NASDAQ"
                }
                {
                    name "Ade Corp"
                    symbol "ADEX1"
                    exchange "NASDAQ"
                }
                {
                    name "Adforce Inc"
                    symbol "ADFC"
                    exchange "NASDAQ"
                }
                {
                    name "American Defense Systems Inc"
                    symbol "ADFS"
                    exchange "NYSEMKT"
                }
                {
                    name "Allied Defense Group Inc"
                    symbol "ADGI1"
                    exchange "NYSEMKT"
                }
                {
                    name "Analog Devices Inc"
                    symbol "ADI"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Digital Information Corp"
                    symbol "ADIC"
                    exchange "NASDAQ"
                }
                {
                    name "Allied Digital Technologies Corp"
                    symbol "ADK1"
                    exchange "NYSEMKT"
                }
                {
                    name "Advanced Lighting Technologies Inc"
                    symbol "ADLTQ"
                    exchange "NASDAQ"
                }
                {
                    name "Audience Inc"
                    symbol "ADNC"
                    exchange "NASDAQ"
                }
                {
                    name "Adecco Sa"
                    symbol "ADO"
                    exchange "NYSE"
                }
                {
                    name "Automatic Data Processing Inc"
                    symbol "ADP"
                    exchange "NASDAQ"
                }
                {
                    name "Allied Products Corp"
                    symbol "ADPC"
                    exchange "NYSE"
                }
                {
                    name "Ault Disruptive Technologies Corp"
                    symbol "ADRT"
                    exchange "NYSEMKT"
                }
                {
                    name "Atlantic Data Services Inc"
                    symbol "ADSC"
                    exchange "NASDAQ"
                }
                {
                    name "Ads-Tec Energy Public Ltd Co"
                    symbol "ADSE"
                    exchange "NASDAQ"
                }
                {
                    name "American Disposal Services Inc"
                    symbol "ADSI"
                    exchange "NASDAQ"
                }
                {
                    name "Autodesk Inc"
                    symbol "ADSK"
                    exchange "NASDAQ"
                }
                {
                    name "Adaptive Solutions Inc"
                    symbol "ADSO1"
                    exchange "NASDAQ"
                }
                {
                    name "Ariel Corp"
                    symbol "ADSPQ"
                    exchange "NASDAQ"
                }
                {
                    name "Adstar Inc"
                    symbol "ADST"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Disposal Services Inc"
                    symbol "ADSW"
                    exchange "NYSE"
                }
                {
                    name "Adt Inc"
                    symbol "ADT"
                    exchange "NYSE"
                }
                {
                    name "Adt Corp"
                    symbol "ADT1"
                    exchange "NYSE"
                }
                {
                    name "Advanced Deposition Technologies Inc"
                    symbol "ADTCQ"
                    exchange "NASDAQ"
                }
                {
                    name "Adtran Holdings Inc"
                    symbol "ADTN"
                    exchange "NASDAQ"
                }
                {
                    name "Advent Software Inc"
                    symbol "ADVS"
                    exchange "NASDAQ"
                }
                {
                    name "Adeza Biomedical Corp"
                    symbol "ADZA"
                    exchange "NASDAQ"
                }
                {
                    name "Adams Resources & Energy Inc"
                    symbol "AE"
                    exchange "NYSEMKT"
                }
                {
                    name "Authentic Equity Acquisition Corp"
                    symbol "AEAC"
                    exchange "NASDAQ"
                }
                {
                    name "Altenergy Acquisition Corp"
                    symbol "AEAE"
                    exchange "NASDAQ"
                }
                {
                    name "American Energy Development Corp"
                    symbol "AEDC"
                    exchange "NASDAQ"
                }
                {
                    name "Aegion Corp"
                    symbol "AEGN"
                    exchange "NASDAQ"
                }
                {
                    name "Aehr Test Systems"
                    symbol "AEHR"
                    exchange "NASDAQ"
                }
                {
                    name "Air Express International Corp"
                    symbol "AEIC"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Energy Industries Inc"
                    symbol "AEIS"
                    exchange "NASDAQ"
                }
                {
                    name "Aenza Saa"
                    symbol "AENZ"
                    exchange "NYSE"
                }
                {
                    name "Aep Industries Inc"
                    symbol "AEPI"
                    exchange "NASDAQ"
                }
                {
                    name "Aercap Holdings Nv"
                    symbol "AER"
                    exchange "NYSE"
                }
                {
                    name "Applied Energetics Inc"
                    symbol "AERG"
                    exchange "NASDAQ"
                }
                {
                    name "Aero Systems Engineering Inc"
                    symbol "AERS1"
                    exchange "NASDAQ"
                }
                {
                    name "Aeries Technology Inc"
                    symbol "AERT"
                    exchange "NASDAQ"
                }
                {
                    name "Atlas Energy Solutions Inc"
                    symbol "AESI"
                    exchange "NYSE"
                }
                {
                    name "Aesp Inc"
                    symbol "AESP"
                    exchange "NASDAQ"
                }
                {
                    name "Applied Extrusion Technologies Inc"
                    symbol "AETCQ"
                    exchange "NASDAQ"
                }
                {
                    name "Arc Resources Ltd"
                    symbol "AETUF"
                    exchange "NYSE"
                }
                {
                    name "Audioeye Inc"
                    symbol "AEYE"
                    exchange "NASDAQ"
                }
                {
                    name "Addvantage Technologies Group Inc"
                    symbol "AEYGQ"
                    exchange "NASDAQ"
                }
                {
                    name "American Oil & Gas Inc"
                    symbol "AEZ"
                    exchange "NYSEMKT"
                }
                {
                    name "Arena Fortify Acquisition Corp"
                    symbol "AFAC"
                    exchange "NASDAQ"
                }
                {
                    name "Af Acquisition Corp"
                    symbol "AFAQ"
                    exchange "NASDAQ"
                }
                {
                    name "Aura Fat Projects Acquisition Corp"
                    symbol "AFAR"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Fibre Communications Inc"
                    symbol "AFCI"
                    exchange "NASDAQ"
                }
                {
                    name "Applied Films Corp"
                    symbol "AFCO1"
                    exchange "NASDAQ"
                }
                {
                    name "Afc Cable Systems Inc"
                    symbol "AFCX"
                    exchange "NASDAQ"
                }
                {
                    name "Printrak International Inc"
                    symbol "AFIS"
                    exchange "NASDAQ"
                }
                {
                    name "Aimei Health Technology Co Ltd"
                    symbol "AFJK"
                    exchange "NASDAQ"
                }
                {
                    name "Adflex Solutions Inc"
                    symbol "AFLX"
                    exchange "NASDAQ"
                }
                {
                    name "Alliance Fiber Optic Products Inc"
                    symbol "AFOP"
                    exchange "NASDAQ"
                }
                {
                    name "Affirm Holdings Inc"
                    symbol "AFRM"
                    exchange "NASDAQ"
                }
                {
                    name "Afternext Healthtech Acquisition Corp"
                    symbol "AFTR"
                    exchange "NYSE"
                }
                {
                    name "American Freightways Corp"
                    symbol "AFWY"
                    exchange "NASDAQ"
                }
                {
                    name "African Gold Acquisition Corp"
                    symbol "AGACF"
                    exchange "NYSE"
                }
                {
                    name "Ag Associates Inc"
                    symbol "AGAI"
                    exchange "NASDAQ"
                }
                {
                    name "Acres Gaming Inc"
                    symbol "AGAM1"
                    exchange "NASDAQ"
                }
                {
                    name "U S Aggregates Inc"
                    symbol "AGATQ"
                    exchange "NYSE"
                }
                {
                    name "Altimeter Growth Corp 2"
                    symbol "AGCB"
                    exchange "NYSE"
                }
                {
                    name "Ag-Chem Equipment Co Inc"
                    symbol "AGCH"
                    exchange "NASDAQ"
                }
                {
                    name "Agco Corp"
                    symbol "AGCO"
                    exchange "NYSE"
                }
                {
                    name "Applied Graphics Technologies Inc"
                    symbol "AGD1"
                    exchange "NYSE"
                }
                {
                    name "Agrify Corp"
                    symbol "AGFY"
                    exchange "NASDAQ"
                }
                {
                    name "Agile Growth Corp"
                    symbol "AGGR"
                    exchange "NASDAQ"
                }
                {
                    name "Agile Software Corp"
                    symbol "AGIL1"
                    exchange "NASDAQ"
                }
                {
                    name "Agilethought Inc"
                    symbol "AGILQ"
                    exchange "NASDAQ"
                }
                {
                    name "Aegis Communications Group Inc"
                    symbol "AGIS"
                    exchange "NASDAQ"
                }
                {
                    name "Agm Group Holdings Inc"
                    symbol "AGMH"
                    exchange "NASDAQ"
                }
                {
                    name "Ag&E Holdings Inc"
                    symbol "AGNUQ"
                    exchange "NYSEMKT"
                }
                {
                    name "Agere Systems Inc"
                    symbol "AGR1"
                    exchange "NYSE"
                }
                {
                    name "Saga Systems Inc"
                    symbol "AGS1"
                    exchange "NYSE"
                }
                {
                    name "Argan Inc"
                    symbol "AGX"
                    exchange "NYSE"
                }
                {
                    name "Agilysys Inc"
                    symbol "AGYS"
                    exchange "NASDAQ"
                }
                {
                    name "Alpha Technologies Group Inc"
                    symbol "AHAG"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Health Intelligence Ltd"
                    symbol "AHI"
                    exchange "NASDAQ"
                }
                {
                    name "American Heritage International Inc"
                    symbol "AHII"
                    exchange "NASDAQ"
                }
                {
                    name "Allied Systems Holdings Inc"
                    symbol "AHIZQ"
                    exchange "NYSEMKT"
                }
                {
                    name "Ahl Services Inc"
                    symbol "AHLS"
                    exchange "NASDAQ"
                }
                {
                    name "Atc Healthcare Inc"
                    symbol "AHNA"
                    exchange "NYSEMKT"
                }
                {
                    name "Atchison Casting Corp"
                    symbol "AHNCQ"
                    exchange "NYSE"
                }
                {
                    name "Oracle Corp"
                    symbol "ORCL"
                    exchange "NYSE"
                }
                {
                    name "Ahren Acquisition Corp"
                    symbol "AHRN"
                    exchange "NASDAQ"
                }
                {
                    name "Audio Highway-Com"
                    symbol "AHWY"
                    exchange "NASDAQ"
                }
                {
                    name "C3Ai Inc"
                    symbol "AI"
                    exchange "NYSE"
                }
                {
                    name "Amcast Industrial Corp"
                    symbol "AICOQ"
                    exchange "NYSE"
                }
                {
                    name "Firefly Neuroscience Inc"
                    symbol "AIFF"
                    exchange "NASDAQ"
                }
                {
                    name "Ablest Inc"
                    symbol "AIH1"
                    exchange "NYSEMKT"
                }
                {
                    name "Autologic Information International Inc"
                    symbol "AIII1"
                    exchange "NASDAQ"
                }
                {
                    name "Aixtron Se"
                    symbol "AIIXY"
                    exchange "NASDAQ"
                }
                {
                    name "Ilearningengines Inc"
                    symbol "AILE"
                    exchange "NASDAQ"
                }
                {
                    name "Alpnet Inc"
                    symbol "AILP"
                    exchange "NASDAQ"
                }
                {
                    name "Aerosonic Corp"
                    symbol "AIM1"
                    exchange "NYSEMKT"
                }
                {
                    name "Aimfinity Investment Corp I"
                    symbol "AIMAU"
                    exchange "NASDAQ"
                }
                {
                    name "Altra Industrial Motion Corp"
                    symbol "AIMC"
                    exchange "NASDAQ"
                }
                {
                    name "Arnold Industries Inc"
                    symbol "AIND"
                    exchange "NASDAQ"
                }
                {
                    name "Applied Innovation Inc"
                    symbol "AINN"
                    exchange "NASDAQ"
                }
                {
                    name "Powerfleet Inc"
                    symbol "AIOT"
                    exchange "NASDAQ"
                }
                {
                    name "Arteris Inc"
                    symbol "AIP"
                    exchange "NASDAQ"
                }
                {
                    name "American International Petroleum Corp"
                    symbol "AIPN"
                    exchange "NASDAQ"
                }
                {
                    name "Aar Corp"
                    symbol "AIR"
                    exchange "NYSE"
                }
                {
                    name "Airgain Inc"
                    symbol "AIRG"
                    exchange "NASDAQ"
                }
                {
                    name "Air Industries Group"
                    symbol "AIRI"
                    exchange "NYSEMKT"
                }
                {
                    name "Air Methods Corp"
                    symbol "AIRM"
                    exchange "NASDAQ"
                }
                {
                    name "Aironet Wireless Communications Inc"
                    symbol "AIRO1"
                    exchange "NASDAQ"
                }
                {
                    name "American Aircarriers Support Inc"
                    symbol "AIRS1"
                    exchange "NASDAQ"
                }
                {
                    name "Air T Inc"
                    symbol "AIRT"
                    exchange "NASDAQ"
                }
                {
                    name "Airvana Inc"
                    symbol "AIRV"
                    exchange "NASDAQ"
                }
                {
                    name "Airship Ai Holdings Inc"
                    symbol "AISP"
                    exchange "NASDAQ"
                }
                {
                    name "Applied Industrial Technologies Inc"
                    symbol "AIT"
                    exchange "NYSE"
                }
                {
                    name "Ai Transportation Acquisition Corp"
                    symbol "AITR"
                    exchange "NASDAQ"
                }
                {
                    name "Xiao-I Corp"
                    symbol "AIXI"
                    exchange "NASDAQ"
                }
                {
                    name "Aerojet Rocketdyne Holdings Inc"
                    symbol "AJRD"
                    exchange "NYSE"
                }
                {
                    name "Akamai Technologies Inc"
                    symbol "AKAM"
                    exchange "NASDAQ"
                }
                {
                    name "Sports Ventures Acquisition Corp"
                    symbol "AKIC"
                    exchange "NASDAQ"
                }
                {
                    name "Acclaim Entertainment Inc"
                    symbol "AKLMQ"
                    exchange "NASDAQ"
                }
                {
                    name "Akoustis Technologies Inc"
                    symbol "AKTS"
                    exchange "NASDAQ"
                }
                {
                    name "Air Lease Corp"
                    symbol "AL"
                    exchange "NYSE"
                }
                {
                    name "Astera Labs Inc"
                    symbol "ALAB"
                    exchange "NASDAQ"
                }
                {
                    name "Alberton Acquisition Corp"
                    symbol "ALAC"
                    exchange "NASDAQ"
                }
                {
                    name "Alanco Technologies Inc"
                    symbol "ALAN"
                    exchange "NASDAQ"
                }
                {
                    name "Alarum Technologies Ltd"
                    symbol "ALAR"
                    exchange "NASDAQ"
                }
                {
                    name "Alchemy Investments Acquisition Corp 1"
                    symbol "ALCY"
                    exchange "NASDAQ"
                }
                {
                    name "Aladdin Knowledge Systems Ltd"
                    symbol "ALDN"
                    exchange "NASDAQ"
                }
                {
                    name "Allied Devices Corp"
                    symbol "ALDV1"
                    exchange "NASDAQ"
                }
                {
                    name "Alon Usa Partners Lp"
                    symbol "ALDW"
                    exchange "NYSE"
                }
                {
                    name "Centurion Acquisition Corp"
                    symbol "ALF"
                    exchange "NASDAQ"
                }
                {
                    name "Alfi Inc"
                    symbol "ALFIQ"
                    exchange "NASDAQ"
                }
                {
                    name "Alford Refrigerated Warehouses Inc"
                    symbol "ALFO"
                    exchange "NASDAQ"
                }
                {
                    name "Alamo Group Inc"
                    symbol "ALG"
                    exchange "NYSE"
                }
                {
                    name "Allegro Microsystems Inc"
                    symbol "ALGM"
                    exchange "NASDAQ"
                }
                {
                    name "Allegro Merger Corp"
                    symbol "ALGR"
                    exchange "NASDAQ"
                }
                {
                    name "Allegiant Travel Co"
                    symbol "ALGT"
                    exchange "NASDAQ"
                }
                {
                    name "Alight Inc"
                    symbol "ALIT"
                    exchange "NYSE"
                }
                {
                    name "Alon Usa Energy Inc"
                    symbol "ALJ"
                    exchange "NYSE"
                }
                {
                    name "Alj Regional Holdings Inc"
                    symbol "ALJJ"
                    exchange "NASDAQ"
                }
                {
                    name "Alaska Air Group Inc"
                    symbol "ALK"
                    exchange "NYSE"
                }
                {
                    name "Alkami Technology Inc"
                    symbol "ALKT"
                    exchange "NASDAQ"
                }
                {
                    name "Allegion Plc"
                    symbol "ALLE"
                    exchange "NYSE"
                }
                {
                    name "Allaire Corp"
                    symbol "ALLR1"
                    exchange "NASDAQ"
                }
                {
                    name "Allot Ltd"
                    symbol "ALLT"
                    exchange "NASDAQ"
                }
                {
                    name "Allen Telecom Inc"
                    symbol "ALN1"
                    exchange "NYSE"
                }
                {
                    name "Amerilink Corp"
                    symbol "ALNK"
                    exchange "NASDAQ"
                }
                {
                    name "Allient Inc"
                    symbol "ALNT"
                    exchange "NASDAQ"
                }
                {
                    name "Alsp Orchid Acquisition Corp I"
                    symbol "ALOR"
                    exchange "NASDAQ"
                }
                {
                    name "Astronova Inc"
                    symbol "ALOT"
                    exchange "NASDAQ"
                }
                {
                    name "Alphanet Solutions Inc"
                    symbol "ALPH"
                    exchange "NASDAQ"
                }
                {
                    name "Alpine 4 Holdings Inc"
                    symbol "ALPP"
                    exchange "NASDAQ"
                }
                {
                    name "Alpine Summit Energy Partners Inc"
                    symbol "ALPSQ"
                    exchange "NASDAQ"
                }
                {
                    name "Alternative Resources Corp"
                    symbol "ALRC"
                    exchange "NASDAQ"
                }
                {
                    name "Alarmcom Holdings Inc"
                    symbol "ALRM"
                    exchange "NASDAQ"
                }
                {
                    name "Altron Inc"
                    symbol "ALRN2"
                    exchange "NASDAQ"
                }
                {
                    name "Alpha Star Acquisition Corp"
                    symbol "ALSA"
                    exchange "NASDAQ"
                }
                {
                    name "Alphasmart Inc"
                    symbol "ALSM"
                    exchange "NASDAQ"
                }
                {
                    name "Alta Equipment Group Inc"
                    symbol "ALTG"
                    exchange "NYSE"
                }
                {
                    name "Altair Engineering Inc"
                    symbol "ALTR"
                    exchange "NASDAQ"
                }
                {
                    name "Altera Corp"
                    symbol "ALTR1"
                    exchange "NASDAQ"
                }
                {
                    name "Alt5 Sigma Corp"
                    symbol "ALTS"
                    exchange "NASDAQ"
                }
                {
                    name "Altitude Acquisition Corp"
                    symbol "ALTU"
                    exchange "NASDAQ"
                }
                {
                    name "Alvarion Ltd"
                    symbol "ALVRQ"
                    exchange "NASDAQ"
                }
                {
                    name "Allis Chalmers Energy Inc"
                    symbol "ALY"
                    exchange "NYSE"
                }
                {
                    name "Alithya Group Inc"
                    symbol "ALYAF"
                    exchange "NASDAQ"
                }
                {
                    name "Alysis Technologies Inc"
                    symbol "ALYS"
                    exchange "NASDAQ"
                }
                {
                    name "Antero Midstream Corp"
                    symbol "AM"
                    exchange "NYSE"
                }
                {
                    name "Antero Midstream Partners Lp"
                    symbol "AM2"
                    exchange "NYSE"
                }
                {
                    name "Autonavi Holdings Ltd"
                    symbol "AMAP"
                    exchange "NASDAQ"
                }
                {
                    name "Applied Materials Inc"
                    symbol "AMAT"
                    exchange "NASDAQ"
                }
                {
                    name "Ambarella Inc"
                    symbol "AMBA"
                    exchange "NASDAQ"
                }
                {
                    name "Ambipar Emergency Response"
                    symbol "AMBI"
                    exchange "NYSEMKT"
                }
                {
                    name "Amber Road Inc"
                    symbol "AMBR"
                    exchange "NYSE"
                }
                {
                    name "Applied Micro Circuits Corp"
                    symbol "AMCC"
                    exchange "NASDAQ"
                }
                {
                    name "Andatee China Marine Fuel Services Corp"
                    symbol "AMCF"
                    exchange "NASDAQ"
                }
                {
                    name "Amicas Inc"
                    symbol "AMCS"
                    exchange "NASDAQ"
                }
                {
                    name "American Classic Voyages Co"
                    symbol "AMCVQ"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Micro Devices Inc"
                    symbol "AMD"
                    exchange "NASDAQ"
                }
                {
                    name "Ametek Inc"
                    symbol "AME"
                    exchange "NYSE"
                }
                {
                    name "American Educational Products Inc"
                    symbol "AMEP"
                    exchange "NASDAQ"
                }
                {
                    name "Amec Foster Wheeler Plc"
                    symbol "AMFW"
                    exchange "NYSE"
                }
                {
                    name "American Midstream Partners Lp"
                    symbol "AMID1"
                    exchange "NYSE"
                }
                {
                    name "Ambassadors International Inc"
                    symbol "AMIEQ"
                    exchange "NASDAQ"
                }
                {
                    name "Acme Metals Inc"
                    symbol "AMIIQ"
                    exchange "NYSE"
                }
                {
                    name "Amis Holdings Inc"
                    symbol "AMIS"
                    exchange "NASDAQ"
                }
                {
                    name "American Technical Ceramics Corp"
                    symbol "AMK1"
                    exchange "NYSEMKT"
                }
                {
                    name "Amkor Technology Inc"
                    symbol "AMKR"
                    exchange "NASDAQ"
                }
                {
                    name "Aml Communications Inc"
                    symbol "AMLJ"
                    exchange "NASDAQ"
                }
                {
                    name "American Noble Gas Inc"
                    symbol "AMNI"
                    exchange "NASDAQ"
                }
                {
                    name "Act Manufacturing Inc"
                    symbol "AMNUQ"
                    exchange "NASDAQ"
                }
                {
                    name "Amp Inc"
                    symbol "AMP1"
                    exchange "NYSE"
                }
                {
                    name "Amplitech Group Inc"
                    symbol "AMPG"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Merger Partners Inc"
                    symbol "AMPI"
                    exchange "NYSE"
                }
                {
                    name "Amplitude Inc"
                    symbol "AMPL"
                    exchange "NASDAQ"
                }
                {
                    name "Amprius Technologies Inc"
                    symbol "AMPX"
                    exchange "NYSE"
                }
                {
                    name "Ampex Corp"
                    symbol "AMPXQ"
                    exchange "NASDAQ"
                }
                {
                    name "Amplify Energy Corp"
                    symbol "AMPY"
                    exchange "NYSE"
                }
                {
                    name "Ameresco Inc"
                    symbol "AMRC"
                    exchange "NYSE"
                }
                {
                    name "Alta Mesa Resources Inc"
                    symbol "AMRQQ"
                    exchange "NASDAQ"
                }
                {
                    name "American Superconductor Corp"
                    symbol "AMSC"
                    exchange "NASDAQ"
                }
                {
                    name "Artemis International Solutions Corp"
                    symbol "AMSI"
                    exchange "NASDAQ"
                }
                {
                    name "Apache Medical Systems Inc"
                    symbol "AMSI1"
                    exchange "NASDAQ"
                }
                {
                    name "Amesite Inc"
                    symbol "AMST"
                    exchange "NASDAQ"
                }
                {
                    name "Amentum Holdings Inc"
                    symbol "AMTM"
                    exchange "NYSE"
                }
                {
                    name "Aemetis Inc"
                    symbol "AMTX"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Machine Vision Corp"
                    symbol "AMVC"
                    exchange "NASDAQ"
                }
                {
                    name "Amx Corp"
                    symbol "AMXC"
                    exchange "NASDAQ"
                }
                {
                    name "Amoco Corp"
                    symbol "AN1"
                    exchange "NYSE"
                }
                {
                    name "Arctos Northstar Acquisition Corp"
                    symbol "ANAC"
                    exchange "NYSE"
                }
                {
                    name "Anadigics Inc"
                    symbol "ANAD"
                    exchange "NASDAQ"
                }
                {
                    name "Airnet Communications Corp"
                    symbol "ANCCQ"
                    exchange "NASDAQ"
                }
                {
                    name "Anc Rental Corp"
                    symbol "ANCJQ"
                    exchange "NASDAQ"
                }
                {
                    name "Ancor Communications Inc"
                    symbol "ANCR"
                    exchange "NASDAQ"
                }
                {
                    name "Andataco Inc"
                    symbol "ANDA1"
                    exchange "NASDAQ"
                }
                {
                    name "Andina Acquisition Corp Ii"
                    symbol "ANDA2"
                    exchange "NASDAQ"
                }
                {
                    name "Andover Net Inc"
                    symbol "ANDN1"
                    exchange "NASDAQ"
                }
                {
                    name "Andrea Electronics Corp"
                    symbol "ANDR"
                    exchange "NYSEMKT"
                }
                {
                    name "Andeavor"
                    symbol "ANDV"
                    exchange "NYSE"
                }
                {
                    name "Andrew Corp"
                    symbol "ANDW"
                    exchange "NASDAQ"
                }
                {
                    name "Andeavor Logistics Lp"
                    symbol "ANDX"
                    exchange "NYSE"
                }
                {
                    name "Anaren  Inc"
                    symbol "ANEN"
                    exchange "NASDAQ"
                }
                {
                    name "Arista Networks Inc"
                    symbol "ANET"
                    exchange "NYSE"
                }
                {
                    name "Act Networks Inc"
                    symbol "ANET2"
                    exchange "NASDAQ"
                }
                {
                    name "Audio Communications Network Inc"
                    symbol "ANI"
                    exchange "NYSEMKT"
                }
                {
                    name "Anicom Inc"
                    symbol "ANIC"
                    exchange "NASDAQ"
                }
                {
                    name "Analogy Inc"
                    symbol "ANLG"
                    exchange "NASDAQ"
                }
                {
                    name "Analysts International Corp"
                    symbol "ANLY"
                    exchange "NASDAQ"
                }
                {
                    name "Anacomp Inc"
                    symbol "ANMP"
                    exchange "NASDAQ"
                }
                {
                    name "Airnet Systems Inc"
                    symbol "ANS"
                    exchange "NYSEMKT"
                }
                {
                    name "Agriculture & Natural Solutions Acquisition Corp"
                    symbol "ANSC"
                    exchange "NASDAQ"
                }
                {
                    name "Ansys Inc"
                    symbol "ANSS"
                    exchange "NASDAQ"
                }
                {
                    name "Ansoft Corp"
                    symbol "ANST"
                    exchange "NASDAQ"
                }
                {
                    name "Answers Corp"
                    symbol "ANSW"
                    exchange "NASDAQ"
                }
                {
                    name "Anteon International Corp"
                    symbol "ANT"
                    exchange "NYSE"
                }
                {
                    name "Phazar Corp"
                    symbol "ANTP"
                    exchange "NASDAQ"
                }
                {
                    name "Aeroquip-Vickers Inc"
                    symbol "ANV1"
                    exchange "NYSE"
                }
                {
                    name "Aegean Marine Petroleum Network Inc"
                    symbol "ANWWQ"
                    exchange "NYSE"
                }
                {
                    name "Sphere 3D Corp"
                    symbol "ANY"
                    exchange "NASDAQ"
                }
                {
                    name "Arogo Capital Acquisition Corp"
                    symbol "AOGO"
                    exchange "NASDAQ"
                }
                {
                    name "Aurora Oil & Gas Corp"
                    symbol "AOGSQ"
                    exchange "NYSEMKT"
                }
                {
                    name "Aol Inc"
                    symbol "AOL"
                    exchange "NYSE"
                }
                {
                    name "A123 Systems Inc"
                    symbol "AONEQ"
                    exchange "NASDAQ"
                }
                {
                    name "Allen Organ Co"
                    symbol "AORGB"
                    exchange "NASDAQ"
                }
                {
                    name "Smith A O Corp"
                    symbol "AOS"
                    exchange "NYSE"
                }
                {
                    name "Alpha & Omega Semiconductor Ltd"
                    symbol "AOSL"
                    exchange "NASDAQ"
                }
                {
                    name "American Outdoor Brands Inc"
                    symbol "AOUT"
                    exchange "NASDAQ"
                }
                {
                    name "Ampco Pittsburgh Corp"
                    symbol "AP"
                    exchange "NYSE"
                }
                {
                    name "Apa Corp"
                    symbol "APA"
                    exchange "NASDAQ"
                }
                {
                    name "Apac Customer Services Inc"
                    symbol "APAC1"
                    exchange "NASDAQ"
                }
                {
                    name "Apco Oil & Gas International Inc"
                    symbol "APAGF"
                    exchange "NASDAQ"
                }
                {
                    name "Anadarko Petroleum Corp"
                    symbol "APC"
                    exchange "NYSE"
                }
                {
                    name "Ap Acquisition Corp"
                    symbol "APCA"
                    exchange "NYSE"
                }
                {
                    name "American Power Conversion Corp"
                    symbol "APCC"
                    exchange "NASDAQ"
                }
                {
                    name "Apptech Payments Corp"
                    symbol "APCX"
                    exchange "NASDAQ"
                }
                {
                    name "Apex Inc"
                    symbol "APEX1"
                    exchange "NASDAQ"
                }
                {
                    name "Api Group Corp"
                    symbol "APG"
                    exchange "NYSE"
                }
                {
                    name "Apollo Strategic Growth Capital Ii"
                    symbol "APGB"
                    exchange "NYSE"
                }
                {
                    name "Amphenol Corp"
                    symbol "APH"
                    exchange "NYSE"
                }
                {
                    name "Agora Inc"
                    symbol "API"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Photonix Inc"
                    symbol "API1"
                    exchange "NYSEMKT"
                }
                {
                    name "Apigee Corp"
                    symbol "APIC"
                    exchange "NASDAQ"
                }
                {
                    name "Acme Packet Inc"
                    symbol "APKT"
                    exchange "NASDAQ"
                }
                {
                    name "Atlas Pipeline Partners Lp"
                    symbol "APL"
                    exchange "NYSE"
                }
                {
                    name "Archrock Partners Lp"
                    symbol "APLP"
                    exchange "NASDAQ"
                }
                {
                    name "Applix Inc"
                    symbol "APLX"
                    exchange "NASDAQ"
                }
                {
                    name "Applied Magnetics Corp"
                    symbol "APM1"
                    exchange "NYSE"
                }
                {
                    name "Applied Microsystems Corp"
                    symbol "APMC"
                    exchange "NASDAQ"
                }
                {
                    name "Axonprime Infrastructure Acquisition Corp"
                    symbol "APMI"
                    exchange "NASDAQ"
                }
                {
                    name "Apeiron Capital Investment Corp"
                    symbol "APNC"
                    exchange "NYSE"
                }
                {
                    name "Alpine Group Inc"
                    symbol "APNI"
                    exchange "NYSE"
                }
                {
                    name "Appnet Inc"
                    symbol "APNT1"
                    exchange "NASDAQ"
                }
                {
                    name "Applovin Corp"
                    symbol "APP"
                    exchange "NASDAQ"
                }
                {
                    name "American Apparel Inc"
                    symbol "APPCQ"
                    exchange "NYSEMKT"
                }
                {
                    name "Appfolio Inc"
                    symbol "APPF"
                    exchange "NASDAQ"
                }
                {
                    name "Appian Corp"
                    symbol "APPN"
                    exchange "NASDAQ"
                }
                {
                    name "Digital Turbine Inc"
                    symbol "APPS"
                    exchange "NASDAQ"
                }
                {
                    name "Appiant Technologies Inc"
                    symbol "APPS1"
                    exchange "NASDAQ"
                }
                {
                    name "Asia Pacific Resources Ltd"
                    symbol "APQCF"
                    exchange "NASDAQ"
                }
                {
                    name "American Precision Industries Inc"
                    symbol "APR1"
                    exchange "NYSE"
                }
                {
                    name "Apropos Technology Inc"
                    symbol "APRS"
                    exchange "NASDAQ"
                }
                {
                    name "Applied Signal Technology Inc"
                    symbol "APSG1"
                    exchange "NASDAQ"
                }
                {
                    name "Apptio Inc"
                    symbol "APTI"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Power Technology Inc"
                    symbol "APTI1"
                    exchange "NASDAQ"
                }
                {
                    name "Aptimus Inc"
                    symbol "APTM1"
                    exchange "NASDAQ"
                }
                {
                    name "Apw Ltd"
                    symbol "APW"
                    exchange "NYSE"
                }
                {
                    name "Asia Pacific Wire & Cable Corp Ltd"
                    symbol "APWC"
                    exchange "NASDAQ"
                }
                {
                    name "A-Power Energy Generation Systems Ltd"
                    symbol "APWR1"
                    exchange "NASDAQ"
                }
                {
                    name "Astropower Inc"
                    symbol "APWRQ"
                    exchange "NASDAQ"
                }
                {
                    name "Apx Acquisition Corp I"
                    symbol "APXI"
                    exchange "NASDAQ"
                }
                {
                    name "Aquantia Corp"
                    symbol "AQ"
                    exchange "NYSE"
                }
                {
                    name "Acquity Group Ltd"
                    symbol "AQ1"
                    exchange "NYSEMKT"
                }
                {
                    name "Aqua Care Systems Inc"
                    symbol "AQCR"
                    exchange "NASDAQ"
                }
                {
                    name "Aqua Metals Inc"
                    symbol "AQMS"
                    exchange "NASDAQ"
                }
                {
                    name "Aquantive Inc"
                    symbol "AQNT"
                    exchange "NASDAQ"
                }
                {
                    name "Aquila Gas Pipeline Corp"
                    symbol "AQP"
                    exchange "NYSE"
                }
                {
                    name "Aquaron Acquisition Corp"
                    symbol "AQU"
                    exchange "NASDAQ"
                }
                {
                    name "Evoqua Water Technologies Corp"
                    symbol "AQUA"
                    exchange "NYSE"
                }
                {
                    name "Antero Resources Corp"
                    symbol "AR"
                    exchange "NYSE"
                }
                {
                    name "Arbitron Inc"
                    symbol "ARB1"
                    exchange "NYSE"
                }
                {
                    name "Ariba Inc"
                    symbol "ARBA"
                    exchange "NASDAQ"
                }
                {
                    name "Arb Iot Group Ltd"
                    symbol "ARBB"
                    exchange "NASDAQ"
                }
                {
                    name "Arbe Robotics Ltd"
                    symbol "ARBE"
                    exchange "NASDAQ"
                }
                {
                    name "Aequi Acquisition Corp"
                    symbol "ARBG"
                    exchange "NASDAQ"
                }
                {
                    name "Arbinet Corp"
                    symbol "ARBX"
                    exchange "NASDAQ"
                }
                {
                    name "Arc Document Solutions Inc"
                    symbol "ARC"
                    exchange "NYSE"
                }
                {
                    name "Atlantic Richfield Co"
                    symbol "ARC1"
                    exchange "NYSE"
                }
                {
                    name "Arcbest Corp"
                    symbol "ARCB"
                    exchange "NASDAQ"
                }
                {
                    name "Arbor Rapha Capital Bioholdings Corp I"
                    symbol "ARCK"
                    exchange "NASDAQ"
                }
                {
                    name "Arc Group Worldwide Inc"
                    symbol "ARCW"
                    exchange "NASDAQ"
                }
                {
                    name "Arc Logistics Partners Lp"
                    symbol "ARCX"
                    exchange "NYSE"
                }
                {
                    name "Arena Resources Inc"
                    symbol "ARD1"
                    exchange "NYSE"
                }
                {
                    name "@Road Inc"
                    symbol "ARDI"
                    exchange "NASDAQ"
                }
                {
                    name "Ardent Software Inc"
                    symbol "ARDT1"
                    exchange "NASDAQ"
                }
                {
                    name "Aremissoft Corp"
                    symbol "AREM1"
                    exchange "NASDAQ"
                }
                {
                    name "Approach Resources Inc"
                    symbol "AREXQ"
                    exchange "NASDAQ"
                }
                {
                    name "Airgas Inc"
                    symbol "ARG"
                    exchange "NYSE"
                }
                {
                    name "Argus Capital Corp"
                    symbol "ARGU"
                    exchange "NASDAQ"
                }
                {
                    name "American Railcar Industries Inc"
                    symbol "ARII"
                    exchange "NASDAQ"
                }
                {
                    name "Arel Communications & Software Ltd"
                    symbol "ARLCF"
                    exchange "NASDAQ"
                }
                {
                    name "Arm Holdings Plc"
                    symbol "ARM"
                    exchange "NASDAQ"
                }
                {
                    name "Arm Holdings Plc"
                    symbol "ARMH"
                    exchange "NASDAQ"
                }
                {
                    name "Aramark"
                    symbol "ARMK"
                    exchange "NYSE"
                }
                {
                    name "Arconic Corp"
                    symbol "ARNC"
                    exchange "NYSE"
                }
                {
                    name "Archrock Inc"
                    symbol "AROC"
                    exchange "NYSE"
                }
                {
                    name "Atlas Resource Partners Lp"
                    symbol "ARPJQ"
                    exchange "NYSE"
                }
                {
                    name "Arq Inc"
                    symbol "ARQ"
                    exchange "NASDAQ"
                }
                {
                    name "Arqit Quantum Inc"
                    symbol "ARQQ"
                    exchange "NASDAQ"
                }
                {
                    name "Arris International Plc"
                    symbol "ARRS"
                    exchange "NASDAQ"
                }
                {
                    name "Array Technologies Inc"
                    symbol "ARRY"
                    exchange "NASDAQ"
                }
                {
                    name "American Residential Services Inc"
                    symbol "ARS1"
                    exchange "NYSE"
                }
                {
                    name "Arcsight Inc"
                    symbol "ARST"
                    exchange "NASDAQ"
                }
                {
                    name "Acnielsen Corp"
                    symbol "ART1"
                    exchange "NYSE"
                }
                {
                    name "Artemis Strategic Investment Corp"
                    symbol "ARTE"
                    exchange "NASDAQ"
                }
                {
                    name "Artecon Inc"
                    symbol "ARTE1"
                    exchange "NASDAQ"
                }
                {
                    name "Art Technology Group Inc"
                    symbol "ARTG"
                    exchange "NASDAQ"
                }
                {
                    name "Artisan Components Inc"
                    symbol "ARTI1"
                    exchange "NASDAQ"
                }
                {
                    name "Arts Way Manufacturing Co Inc"
                    symbol "ARTW"
                    exchange "NASDAQ"
                }
                {
                    name "Arotech Corp"
                    symbol "ARTX"
                    exchange "NASDAQ"
                }
                {
                    name "Aruba Networks Inc"
                    symbol "ARUN"
                    exchange "NASDAQ"
                }
                {
                    name "Aerovox Inc"
                    symbol "ARVX"
                    exchange "NASDAQ"
                }
                {
                    name "Arrow Electronics Inc"
                    symbol "ARW"
                    exchange "NYSE"
                }
                {
                    name "Arowana Inc"
                    symbol "ARWA"
                    exchange "NASDAQ"
                }
                {
                    name "Aeroflex Holding Corp"
                    symbol "ARX"
                    exchange "NYSE"
                }
                {
                    name "Aeroflex Inc"
                    symbol "ARXX"
                    exchange "NASDAQ"
                }
                {
                    name "Arya Sciences Acquisition Corp V"
                    symbol "ARYE"
                    exchange "NASDAQ"
                }
                {
                    name "Asa Holdings Inc"
                    symbol "ASAI1"
                    exchange "NASDAQ"
                }
                {
                    name "Asa International Ltd"
                    symbol "ASAL"
                    exchange "NASDAQ"
                }
                {
                    name "Asahi America Inc"
                    symbol "ASAM1"
                    exchange "NASDAQ"
                }
                {
                    name "Asana Inc"
                    symbol "ASAN"
                    exchange "NYSE"
                }
                {
                    name "Waitr Holdings Inc"
                    symbol "ASAPQ"
                    exchange "NASDAQ"
                }
                {
                    name "Atlantic Avenue Acquisition Corp"
                    symbol "ASAQ"
                    exchange "NYSE"
                }
                {
                    name "Astrea Acquisition Corp"
                    symbol "ASAX"
                    exchange "NASDAQ"
                }
                {
                    name "Ardmore Shipping Corp"
                    symbol "ASC"
                    exchange "NYSE"
                }
                {
                    name "Aspac Ii Acquisition Corp"
                    symbol "ASCBF"
                    exchange "NASDAQ"
                }
                {
                    name "Ascential Software Corp"
                    symbol "ASCL"
                    exchange "NASDAQ"
                }
                {
                    name "Ascent Capital Group Inc"
                    symbol "ASCMA"
                    exchange "NASDAQ"
                }
                {
                    name "Advanced Switching Communications Inc"
                    symbol "ASCX"
                    exchange "NASDAQ"
                }
                {
                    name "Asd Group Inc"
                    symbol "ASDG"
                    exchange "NASDAQ"
                }
                {
                    name "Ascendant Solutions Inc"
                    symbol "ASDS"
                    exchange "NASDAQ"
                }
                {
                    name "Aspect Development Inc"
                    symbol "ASDV"
                    exchange "NASDAQ"
                }
                {
                    name "Aseco Corp"
                    symbol "ASEC"
                    exchange "NASDAQ"
                }
                {
                    name "Asgn Inc"
                    symbol "ASGN"
                    exchange "NYSE"
                }
                {
                    name "Asche Transportation Services Inc"
                    symbol "ASHE"
                    exchange "NASDAQ"
                }
                {
                    name "Asiainfo-Linkage Inc"
                    symbol "ASIA1"
                    exchange "NASDAQ"
                }
                {
                    name "Ansaldo Signal Nv"
                    symbol "ASIGF1"
                    exchange "NASDAQ"
                }
                {
                    name "Asi Solutions Inc"
                    symbol "ASIS"
                    exchange "NASDAQ"
                }
                {
                    name "Ask Jeeves Inc"
                    symbol "ASKJ"
                    exchange "NASDAQ"
                }
                {
                    name "Aersale Corp"
                    symbol "ASLE"
                    exchange "NASDAQ"
                }
                {
                    name "Asm International N V"
                    symbol "ASMIY"
                    exchange "NASDAQ"
                }
                {
                    name "Asml Holding Nv"
                    symbol "ASML"
                    exchange "NASDAQ"
                }
                {
                    name "Ascend Communications Inc"
                    symbol "ASND1"
                    exchange "NASDAQ"
                }
                {
                    name "Actelis Networks Inc"
                    symbol "ASNS"
                    exchange "NASDAQ"
                }
                {
                    name "Anangel American Shipholdings Ltd"
                    symbol "ASPIY"
                    exchange "NASDAQ"
                }
                {
                    name "Aspect Communications Corp"
                    symbol "ASPT"
                    exchange "NASDAQ"
                }
                {
                    name "Auspex Systems Inc"
                    symbol "ASPXQ"
                    exchange "NASDAQ"
                }
                {
                    name "Southeast Airport Group"
                    symbol "ASR"
                    exchange "NYSE"
                }
                {
                    name "Astrotech Corp"
                    symbol "ASTC"
                    exchange "NASDAQ"
                }
                {
                    name "Astec Industries Inc"
                    symbol "ASTE"
                    exchange "NASDAQ"
                }
                {
                    name "Ascent Solar Technologies Inc"
                    symbol "ASTI"
                    exchange "NASDAQ"
                }
                {
                    name "Astra Space Inc"
                    symbol "ASTR"
                    exchange "NASDAQ"
                }
                {
                    name "Ast Spacemobile Inc"
                    symbol "ASTS"
                    exchange "NASDAQ"
                }
                {
                    name "Asat Holdings Ltd"
                    symbol "ASTTY"
                    exchange "NASDAQ"
                }
                {
                    name "Applied Science & Technology Inc"
                    symbol "ASTX1"
                    exchange "NASDAQ"
                }
                {
                    name "Asure Software Inc"
                    symbol "ASUR"
                    exchange "NASDAQ"
                }
                {
                    name "Asv Holdings Inc"
                    symbol "ASV"
                    exchange "NASDAQ"
                }
                {
                    name "Asv Inc"
                    symbol "ASVI"
                    exchange "NASDAQ"
                }
                {
                    name "Audits & Surveys Worldwide Inc"
                    symbol "ASW1"
                    exchange "NYSEMKT"
                }
                {
                    name "Active Software Inc"
                    symbol "ASWX"
                    exchange "NASDAQ"
                }
                {
                    name "Ase Technology Holding Co Ltd"
                    symbol "ASX"
                    exchange "NYSE"
                }
                {
                    name "Amtech Systems Inc"
                    symbol "ASYS"
                    exchange "NASDAQ"
                }
                {
                    name "Asyst Technologies Inc"
                    symbol "ASYTQ"
                    exchange "NASDAQ"
                }
                {
                    name "Austerlitz Acquisition Corp Ii"
                    symbol "ASZ"
                    exchange "NYSE"
                }
                {
                    name "Americas Technology Acquisition Corp"
                    symbol "ATA"
                    exchange "NYSE"
                }
                {
                    name "Atc Technology Corp"
                    symbol "ATAC1"
                    exchange "NASDAQ"
                }
                {
                    name "Ata Holdings Corp"
                    symbol "ATAHQ"
                    exchange "NASDAQ"
                }
                {
                    name "Altimar Acquisition Corp Iii"
                    symbol "ATAQ"
                    exchange "NYSE"
                }
                {
                    name "Atari Inc"
                    symbol "ATAR1"
                    exchange "NASDAQ"
                }
                {
                    name "Arlington Tankers Ltd"
                    symbol "ATB"
                    exchange "NYSE"
                }
                {
                    name "Atotech Ltd"
                    symbol "ATC"
                    exchange "NYSE"
                }
                {
                    name "Atlasclear Holdings Inc"
                    symbol "ATCH"
                    exchange "NYSEMKT"
                }
                {
                    name "Arthur Treachers Inc"
                    symbol "ATCH1"
                    exchange "NASDAQ"
                }
                {
                    name "At Comm Corp"
                    symbol "ATCM"
                    exchange "NASDAQ"
                }
                {
                    name "Atlas Technical Consultants Inc"
                    symbol "ATCX"
                    exchange "NASDAQ"
                }
                {
                    name "Astea International Inc"
                    symbol "ATEA"
                    exchange "NASDAQ"
                }
                {
                    name "Athena Technology Acquisition Corp Ii"
                    symbol "ATEK"
                    exchange "NYSEMKT"
                }
                {
                    name "American Telecom Services Inc"
                    symbol "ATEL"
                    exchange "NYSEMKT"
                }
                {
                    name "A10 Networks Inc"
                    symbol "ATEN"
                    exchange "NYSE"
                }
                {
                    name "Advantest Corp"
                    symbol "ATEYY"
                    exchange "NYSE"
                }
                {
                    name "Atg Inc"
                    symbol "ATGCQ"
                    exchange "NASDAQ"
                }
                {
                    name "Alpha Technology Group Ltd"
                    symbol "ATGL"
                    exchange "NASDAQ"
                }
                {
                    name "Altigen Communications Inc"
                    symbol "ATGN"
                    exchange "NASDAQ"
                }
                {
                    name "Athlon Energy Inc"
                    symbol "ATHL"
                    exchange "NYSE"
                }
                {
                    name "Atheros Communications Inc"
                    symbol "ATHR"
                    exchange "NASDAQ"
                }
                {
                    name "Appliedtheory Corp"
                    symbol "ATHYQ"
                    exchange "NASDAQ"
                }
                {
                    name "Ati Inc"
                    symbol "ATI"
                    exchange "NYSE"
                }
                {
                    name "Attis Industries Inc"
                    symbol "ATIS"
                    exchange "NASDAQ"
                }
                {
                    name "Atkore Inc"
                    symbol "ATKR"
                    exchange "NYSE"
                }
                {
                    name "Atl Products Inc"
                    symbol "ATLPA"
                    exchange "NASDAQ"
                }
                {
                    name "Atlas Energy Group Llc"
                    symbol "ATLS"
                    exchange "NYSE"
                }
                {
                    name "Atlas Energy Lp"
                    symbol "ATLS1"
                    exchange "NYSE"
                }
                {
                    name "Atlas Energy Inc"
                    symbol "ATLS2"
                    exchange "NYSE"
                }
                {
                    name "Alphatime Acquisition Corp"
                    symbol "ATMC"
                    exchange "NASDAQ"
                }
                {
                    name "Atmel Corp"
                    symbol "ATML"
                    exchange "NASDAQ"
                }
                {
                    name "Atmus Filtration Technologies Inc"
                    symbol "ATMU"
                    exchange "NYSE"
                }
                {
                    name "Alphavest Acquisition Corp"
                    symbol "ATMV"
                    exchange "NASDAQ"
                }
                {
                    name "Atlas Energy Resources Llc"
                    symbol "ATN"
                    exchange "NYSE"
                }
                {
                    name "Action Performance Companies Inc"
                    symbol "ATN1"
                    exchange "NYSE"
                }
                {
                    name "Api Technologies Corp"
                    symbol "ATNY"
                    exchange "NASDAQ"
                }
                {
                    name "Atomera Inc"
                    symbol "ATOM"
                    exchange "NASDAQ"
                }
                {
                    name "Alteon Websystems Inc"
                    symbol "ATON"
                    exchange "NASDAQ"
                }
                {
                    name "Atp Oil & Gas Corp"
                    symbol "ATPAQ"
                    exchange "NASDAQ"
                }
                {
                    name "Atlantis Plastics Inc"
                    symbol "ATPL"
                    exchange "NASDAQ"
                }
                {
                    name "Astronics Corp"
                    symbol "ATRO"
                    exchange "NASDAQ"
                }
                {
                    name "Altiris Inc"
                    symbol "ATRS1"
                    exchange "NASDAQ"
                }
                {
                    name "Ats Corp"
                    symbol "ATS"
                    exchange "NYSE"
                }
                {
                    name "Ats Corp"
                    symbol "ATSC1"
                    exchange "NYSEMKT"
                }
                {
                    name "Air Transport Services Group Inc"
                    symbol "ATSG"
                    exchange "NASDAQ"
                }
                {
                    name "Artesyn Technologies Inc"
                    symbol "ATSN"
                    exchange "NASDAQ"
                }
                {
                    name "Atento Sa"
                    symbol "ATTOF"
                    exchange "NYSE"
                }
                {
                    name "Attunity Ltd"
                    symbol "ATTU"
                    exchange "NASDAQ"
                }
                {
                    name "1-800 Attorney Inc"
                    symbol "ATTY"
                    exchange "NASDAQ"
                }
                {
                    name "Atwood Oceanics Inc"
                    symbol "ATW"
                    exchange "NYSE"
                }
                {
                    name "Costa Inc"
                    symbol "ATX"
                    exchange "NASDAQ"
                }
                {
                    name "Addentax Group Corp"
                    symbol "ATXG"
                    exchange "NASDAQ"
                }
                {
                    name "Atrix International Inc"
                    symbol "ATXI1"
                    exchange "NASDAQ"
                }
                {
                    name "Ati Technologies Inc"
                    symbol "ATYT"
                    exchange "NASDAQ"
                }
                {
                    name "Audiocodes Ltd"
                    symbol "AUDC"
                    exchange "NASDAQ"
                }
                {
                    name "Augment Systems Inc"
                    symbol "AUGS"
                    exchange "NASDAQ"
                }
                {
                    name "August Technology Corp"
                    symbol "AUGT1"
                    exchange "NASDAQ"
                }
                {
                    name "Authid Inc"
                    symbol "AUID"
                    exchange "NASDAQ"
                }
                {
                    name "Ault Inc"
                    symbol "AULT1"
                    exchange "NASDAQ"
                }
                {
                    name "Au Optronics Corp"
                    symbol "AUOTY"
                    exchange "NYSE"
                }
                {
                    name "Aurora Innovation Inc"
                    symbol "AUR"
                    exchange "NASDAQ"
                }
                {
                    name "Aura Systems Inc"
                    symbol "AURAQ"
                    exchange "NASDAQ"
                }
                {
                    name "Austerlitz Acquisition Corp I"
                    symbol "AUS"
                    exchange "NYSE"
                }
                {
                    name "Access Plans Usa Inc"
                    symbol "AUSA"
                    exchange "NASDAQ"
                }
                {
                    name "Austral Pacific Energy Ltd"
                    symbol "AUSPF"
                    exchange "NYSEMKT"
                }
                {
                    name "Authentec Inc"
                    symbol "AUTH"
                    exchange "NASDAQ"
                }
                {
                    name "Autonomy Corp Plc"
                    symbol "AUTNY"
                    exchange "NASDAQ"
                }
                {
                    name "Autoinfo Inc"
                    symbol "AUTO1"
                    exchange "NASDAQ"
                }
                {
                    name "Auddia Inc"
                    symbol "AUUD"
                    exchange "NASDAQ"
                }
                {
                    name "Authoriszor Inc"
                    symbol "AUZR"
                    exchange "NASDAQ"
                }
                {
                    name "Avaya Inc"
                    symbol "AV1"
                    exchange "NYSE"
                }
                {
                    name "Avanti Acquisition Corp"
                    symbol "AVAN"
                    exchange "NYSE"
                }
                {
                    name "Aerovironment Inc"
                    symbol "AVAV"
                    exchange "NASDAQ"
                }
                {
                    name "Audio Visual Services Corp"
                    symbol "AVC"
                    exchange "NYSE"
                }
                {
                    name "Avocent Corp"
                    symbol "AVCT1"
                    exchange "NASDAQ"
                }
                {
                    name "American Virtual Cloud Technologies Inc"
                    symbol "AVCTQ"
                    exchange "NASDAQ"
                }
                {
                    name "Avalon Digital Marketing Systems Inc"
                    symbol "AVDS1"
                    exchange "NASDAQ"
                }
                {
                    name "Avidxchange Holdings Inc"
                    symbol "AVDX"
                    exchange "NASDAQ"
                }
                {
                    name "Aviation General Inc"
                    symbol "AVGE1"
                    exchange "NASDAQ"
                }
                {
                    name "Broadcom Inc"
                    symbol "AVGO"
                    exchange "NASDAQ"
                }
                {
                    name "Avantgo Inc"
                    symbol "AVGO1"
                    exchange "NASDAQ"
                }
                {
                    name "Avg Technologies Nv"
                    symbol "AVGTF"
                    exchange "NYSE"
                }
                {
                    name "Achari Ventures Holdings Corp I"
                    symbol "AVHI"
                    exchange "NASDAQ"
                }
                {
                    name "Avianca Holdings Sa"
                    symbol "AVHOQ"
                    exchange "NYSE"
                }
                {
                    name "Avis Group Holdings Inc"
                    symbol "AVI"
                    exchange "NYSE"
                }
                {
                    name "Avid Technology Inc"
                    symbol "AVID"
                    exchange "NASDAQ"
                }
                {
                    name "Aviall Inc"
                    symbol "AVL1"
                    exchange "NYSEMKT"
                }
                {
                    name "Avalara Inc"
                    symbol "AVLR"
                    exchange "NYSE"
                }
                {
                    name "Avinci Media Corp"
                    symbol "AVMC1"
                    exchange "NASDAQ"
                }
                {
                    name "Avant Corp"
                    symbol "AVNT1"
                    exchange "NASDAQ"
                }
                {
                    name "Aviat Networks Inc"
                    symbol "AVNW"
                    exchange "NASDAQ"
                }
                {
                    name "Avanex Corp"
                    symbol "AVNX"
                    exchange "NASDAQ"
                }
                {
                    name "Avolon Holdings Ltd"
                    symbol "AVOL"
                    exchange "NYSE"
                }
                {
                    name "Avepoint Inc"
                    symbol "AVPT"
                    exchange "NASDAQ"
                }
                {
                    name "Avistar Communications Corp"
                    symbol "AVSR"
                    exchange "NASDAQ"
                }
                {
                    name "Avnet Inc"
                    symbol "AVT"
                    exchange "NASDAQ"
                }
                {
                    name "Avteam Inc"
                    symbol "AVTMQ"
                    exchange "NASDAQ"
                }
                {
                    name "Aviva Petroleum Inc"
                    symbol "AVV"
                    exchange "NYSEMKT"
                }
                {
                    name "Avx Corp"
                    symbol "AVX"
                    exchange "NYSE"
                }
                {
                    name "Avaya Holdings Corp"
                    symbol "AVYAQ"
                    exchange "NYSE"
                }
                {
                    name "Aviza Technology Inc"
                    symbol "AVZAQ"
                    exchange "NASDAQ"
                }
                {
                    name "Allied Waste Industries Inc"
                    symbol "AW"
                    exchange "NYSE"
                }
                {
                    name "America West Holdings Corp"
                    symbol "AWA"
                    exchange "NYSE"
                }
                {
                    name "Homeaway Inc"
                    symbol "AWAY1"
                    exchange "NASDAQ"
                }
                {
                    name "Aerwins Technologies Inc"
                    symbol "AWIN"
                    exchange "NASDAQ"
                }
                {
                    name "Aware Inc"
                    symbol "AWRE"
                    exchange "NASDAQ"
                }
                {
                    name "Avalon Holdings Corp"
                    symbol "AWX"
                    exchange "NYSEMKT"
                }
                {
                    name "Axios Sustainable Growth Acquisition Corp"
                    symbol "AXAC"
                    exchange "NYSE"
                }
                {
                    name "Axar Acquisition Corp"
                    symbol "AXAR"
                    exchange "NASDAQ"
                }
                {
                    name "Abraxas Petroleum Corp"
                    symbol "AXAS"
                    exchange "NASDAQ"
                }
                {
                    name "Anixter International Inc"
                    symbol "AXE"
                    exchange "NYSE"
                }
                {
                    name "Industrial Human Capital Inc"
                    symbol "AXHI"
                    exchange "NYSE"
                }
                {
                    name "Axiohm Transaction Solutions Inc"
                    symbol "AXHM"
                    exchange "NASDAQ"
                }
                {
                    name "Axil Brands Inc"
                    symbol "AXIL"
                    exchange "NYSEMKT"
                }
                {
                    name "Axent Technologies Inc"
                    symbol "AXNT"
                    exchange "NASDAQ"
                }
                {
                    name "Axon Enterprise Inc"
                    symbol "AXON"
                    exchange "NASDAQ"
                }
                {
                    name "Axion Power International Inc"
                    symbol "AXPWQ"
                    exchange "NASDAQ"
                }
                {
                    name "Axcess International Inc"
                    symbol "AXSI"
                    exchange "NASDAQ"
                }
                {
                    name "Axs One Inc"
                    symbol "AXSO"
                    exchange "NYSEMKT"
                }
                {
                    name "Axesstel Inc"
                    symbol "AXST"
                    exchange "NASDAQ"
                }
                {
                    name "Axtive Corp"
                    symbol "AXTC"
                    exchange "NASDAQ"
                }
                {
                    name "Axt Inc"
                    symbol "AXTI"
                    exchange "NASDAQ"
                }
                {
                    name "Axsys Technologies Inc"
                    symbol "AXYS"
                    exchange "NASDAQ"
                }
                {
                    name "Aydin Corp"
                    symbol "AYD"
                    exchange "NYSE"
                }
                {
                    name "Acuity Brands Inc"
                    symbol "AYI"
                    exchange "NYSE"
                }
                {
                    name "Aircastle Ltd"
                    symbol "AYR"
                    exchange "NYSE"
                }
                {
                    name "Acsys Inc"
                    symbol "AYS"
                    exchange "NYSEMKT"
                }
                {
                    name "Alteryx Inc"
                    symbol "AYX"
                    exchange "NYSE"
                }
                {
                    name "A2Z Smart Technologies Corp"
                    symbol "AZ"
                    exchange "NASDAQ"
                }
                {
                    name "Arizona Instrument Corp"
                    symbol "AZIC"
                    exchange "NASDAQ"
                }
                {
                    name "Aspen Technology Inc"
                    symbol "AZPN"
                    exchange "NASDAQ"
                }
                {
                    name "Aspen Technology Inc"
                    symbol "AZPN1"
                    exchange "NASDAQ"
                }
                {
                    name "Azul Sa"
                    symbol "AZUL"
                    exchange "NYSE"
                }
                {
                    name "Azure Midstream Partners Lp"
                    symbol "AZURQ"
                    exchange "NASDAQ"
                }
                {
                    name "Azz Inc"
                    symbol "AZZ"
                    exchange "NYSE"
                }
                {
                    name "Barnes Group Inc"
                    symbol "B"
                    exchange "NYSE"
                }
                {
                    name "Boeing Co"
                    symbol "BA"
                    exchange "NYSE"
                }
                {
                    name "Baan Co N V"
                    symbol "BAANF"
                    exchange "NASDAQ"
                }
                {
                    name "Berenson Acquisition Corp I"
                    symbol "BACA"
                    exchange "NYSE"
                }
                {
                    name "Bridger Aerospace Group Holdings Inc"
                    symbol "BAER"
                    exchange "NASDAQ"
                }
                {
                    name "Booz Allen Hamilton Holding Corp"
                    symbol "BAH"
                    exchange "NYSE"
                }
                {
                    name "Baltic Trading Ltd"
                    symbol "BALT2"
                    exchange "NYSE"
                }
                {
                    name "Bandwidth Inc"
                    symbol "BAND"
                    exchange "NASDAQ"
                }
                {
                    name "Cbl International Ltd"
                    symbol "BANL"
                    exchange "NASDAQ"
                }
                {
                    name "Banner Aerospace Inc"
                    symbol "BAR1"
                    exchange "NYSE"
                }
                {
                    name "Couchbase Inc"
                    symbol "BASE"
                    exchange "NASDAQ"
                }
                {
                    name "Base Ten Systems Inc"
                    symbol "BASEA"
                    exchange "NASDAQ"
                }
                {
                    name "Basic Energy Services Inc"
                    symbol "BASXQ"
                    exchange "NYSE"
                }
                {
                    name "Battalion Oil Corp"
                    symbol "BATL"
                    exchange "NYSEMKT"
                }
                {
                    name "Talisman Enterprise Inc"
                    symbol "BATT1"
                    exchange "NASDAQ"
                }
                {
                    name "Bay Networks Inc"
                    symbol "BAY1"
                    exchange "NYSE"
                }
                {
                    name "Bayview Acquisition Corp"
                    symbol "BAYA"
                    exchange "NASDAQ"
                }
                {
                    name "Blackberry Ltd"
                    symbol "BB"
                    exchange "NYSE"
                }
                {
                    name "Bigbearai Holdings Inc"
                    symbol "BBAI"
                    exchange "NYSE"
                }
                {
                    name "Blackboard Inc"
                    symbol "BBBB"
                    exchange "NASDAQ"
                }
                {
                    name "Concrete Pumping Holdings Inc"
                    symbol "BBCP"
                    exchange "NASDAQ"
                }
                {
                    name "Breitburn Energy Partners Lp"
                    symbol "BBEPQ"
                    exchange "NASDAQ"
                }
                {
                    name "Bill Barrett Corp"
                    symbol "BBG"
                    exchange "NYSE"
                }
                {
                    name "Britannia Bulk Holdings Inc"
                    symbol "BBLKF"
                    exchange "NYSE"
                }
                {
                    name "Blue Earth Inc"
                    symbol "BBLUQ"
                    exchange "NASDAQ"
                }
                {
                    name "Bigband Networks Inc"
                    symbol "BBND"
                    exchange "NASDAQ"
                }
                {
                    name "Black Box Corp"
                    symbol "BBOX"
                    exchange "NASDAQ"
                }
                {
                    name "Burr Brown Corp"
                    symbol "BBRC1"
                    exchange "NASDAQ"
                }
                {
                    name "Barrett Business Services Inc"
                    symbol "BBSI"
                    exchange "NASDAQ"
                }
                {
                    name "Broadbase Software Inc"
                    symbol "BBSW"
                    exchange "NASDAQ"
                }
                {
                    name "Brookfield Business Partners Lp"
                    symbol "BBU"
                    exchange "NYSE"
                }
                {
                    name "Femto Technologies Inc"
                    symbol "BCAN"
                    exchange "NASDAQ"
                }
                {
                    name "Broadcaster Inc"
                    symbol "BCAS"
                    exchange "NASDAQ"
                }
                {
                    name "Bcd Semiconductor Manufacturing Ltd"
                    symbol "BCDS1"
                    exchange "NASDAQ"
                }
                {
                    name "Brinks Co"
                    symbol "BCO"
                    exchange "NYSE"
                }
                {
                    name "Brightcove Inc"
                    symbol "BCOV"
                    exchange "NASDAQ"
                }
                {
                    name "Blockchain Coinvestors Acquisition Corp I"
                    symbol "BCSA"
                    exchange "NASDAQ"
                }
                {
                    name "Blue Coat Systems Inc"
                    symbol "BCSI"
                    exchange "NASDAQ"
                }
                {
                    name "Broadcast International Inc"
                    symbol "BCST"
                    exchange "NASDAQ"
                }
                {
                    name "Bct International Inc"
                    symbol "BCTI"
                    exchange "NASDAQ"
                }
                {
                    name "Belden Inc"
                    symbol "BDC"
                    exchange "NYSE"
                }
                {
                    name "Blue Dolphin Energy Co"
                    symbol "BDCO"
                    exchange "NASDAQ"
                }
                {
                    name "Bois D Arc Energy Inc"
                    symbol "BDE1"
                    exchange "NASDAQ"
                }
                {
                    name "Budget Group Inc"
                    symbol "BDGPA"
                    exchange "NYSE"
                }
                {
                    name "Bayard Drilling Technologies Inc"
                    symbol "BDI"
                    exchange "NYSEMKT"
                }
                {
                    name "Black & Decker Corp"
                    symbol "BDK"
                    exchange "NASDAQ"
                }
                {
                    name "Brilliant Digital Entertainment Inc"
                    symbol "BDLN"
                    exchange "NASDAQ"
                }
                {
                    name "Boundless Corp"
                    symbol "BDLSQ"
                    exchange "NYSEMKT"
                }
                {
                    name "Bdm International Inc"
                    symbol "BDMI"
                    exchange "NASDAQ"
                }
                {
                    name "Blonder Tongue Laboratories Inc"
                    symbol "BDRL"
                    exchange "NYSEMKT"
                }
                {
                    name "Bloom Energy Corp"
                    symbol "BE"
                    exchange "NYSE"
                }
                {
                    name "Bea Systems Inc"
                    symbol "BEAS"
                    exchange "NASDAQ"
                }
                {
                    name "Beacon Roofing Supply Inc"
                    symbol "BECN"
                    exchange "NASDAQ"
                }
                {
                    name "Beam Global"
                    symbol "BEEM"
                    exchange "NASDAQ"
                }
                {
                    name "Mobile Infrastructure Corp"
                    symbol "BEEP"
                    exchange "NYSEMKT"
                }
                {
                    name "Berg Electronics Corp"
                    symbol "BEI1"
                    exchange "NYSE"
                }
                {
                    name "Bei Technologies Inc"
                    symbol "BEIQ"
                    exchange "NASDAQ"
                }
                {
                    name "Bel Fuse Inc"
                    symbol "BELFA"
                    exchange "NASDAQ"
                }
                {
                    name "Bell Microproducts Inc"
                    symbol "BELM"
                    exchange "NASDAQ"
                }
                {
                    name "Benessere Capital Acquisition Corp"
                    symbol "BENE"
                    exchange "NASDAQ"
                }
                {
                    name "Be Inc"
                    symbol "BEOSZ"
                    exchange "NASDAQ"
                }
                {
                    name "Best Inc"
                    symbol "BEST"
                    exchange "NYSE"
                }
                {
                    name "Best Software Inc"
                    symbol "BEST1"
                    exchange "NASDAQ"
                }
                {
                    name "Bethlehem Corp"
                    symbol "BET"
                    exchange "NYSEMKT"
                }
                {
                    name "Brigham Exploration Co"
                    symbol "BEXP"
                    exchange "NASDAQ"
                }
                {
                    name "Baldor Electric Co"
                    symbol "BEZ"
                    exchange "NYSE"
                }
                {
                    name "Battery Future Acquisition Corp"
                    symbol "BFAC"
                    exchange "NYSE"
                }
                {
                    name "Browning Ferris Industries Inc"
                    symbol "BFI1"
                    exchange "NYSE"
                }
                {
                    name "Be Free Inc"
                    symbol "BFRE1"
                    exchange "NASDAQ"
                }
                {
                    name "Bam Entertainment Inc"
                    symbol "BFUN"
                    exchange "NASDAQ"
                }
                {
                    name "Bfx Hospitality Group Inc"
                    symbol "BFX1"
                    exchange "NYSEMKT"
                }
                {
                    name "General Cable Corp"
                    symbol "BGC2"
                    exchange "NYSE"
                }
                {
                    name "Big Flower Holdings Inc"
                    symbol "BGF"
                    exchange "NYSE"
                }
                {
                    name "Briggs & Stratton Corp"
                    symbol "BGGSQ"
                    exchange "NYSE"
                }
                {
                    name "Buckeye Gp Holdings Lp"
                    symbol "BGH1"
                    exchange "NYSE"
                }
                {
                    name "Bearingpoint Inc"
                    symbol "BGPTQ"
                    exchange "NYSE"
                }
                {
                    name "Berger Holdings Ltd"
                    symbol "BGRH"
                    exchange "NASDAQ"
                }
                {
                    name "Berkshire Grey Inc"
                    symbol "BGRY"
                    exchange "NASDAQ"
                }
                {
                    name "Bgsf Inc"
                    symbol "BGSF"
                    exchange "NYSE"
                }
                {
                    name "Build Acquisition Corp"
                    symbol "BGSX"
                    exchange "NYSE"
                }
                {
                    name "Focus Impact Bh3 Acquisition Co"
                    symbol "BHAC"
                    exchange "NASDAQ"
                }
                {
                    name "Barington/Hilco Acquisition Corp"
                    symbol "BHAC1"
                    exchange "NASDAQ"
                }
                {
                    name "Bha Group Inc"
                    symbol "BHAG"
                    exchange "NASDAQ"
                }
                {
                    name "Benchmark Electronics Inc"
                    symbol "BHE"
                    exchange "NYSE"
                }
                {
                    name "Baker Hughes Inc"
                    symbol "BHI"
                    exchange "NYSE"
                }
                {
                    name "B Plus H Ocean Carriers Ltd"
                    symbol "BHODQ"
                    exchange "NYSEMKT"
                }
                {
                    name "Bidzcom Inc"
                    symbol "BIDZ"
                    exchange "NASDAQ"
                }
                {
                    name "Bigcommerce Holdings Inc"
                    symbol "BIGC"
                    exchange "NASDAQ"
                }
                {
                    name "Bill Holdings Inc"
                    symbol "BILL"
                    exchange "NYSE"
                }
                {
                    name "Bioplus Acquisition Corp"
                    symbol "BIOS"
                    exchange "NASDAQ"
                }
                {
                    name "Biotech Acquisition Co"
                    symbol "BIOT"
                    exchange "NASDAQ"
                }
                {
                    name "Actuate Corp"
                    symbol "BIRT"
                    exchange "NASDAQ"
                }
                {
                    name "Baltic International Usa Inc"
                    symbol "BISA"
                    exchange "NASDAQ"
                }
                {
                    name "Bitstream Inc"
                    symbol "BITS1"
                    exchange "NASDAQ"
                }
                {
                    name "Biznessonline Com Inc"
                    symbol "BIZZ1"
                    exchange "NASDAQ"
                }
                {
                    name "Bj Services Co"
                    symbol "BJS"
                    exchange "NYSE"
                }
                {
                    name "Blueknight Energy Partners Lp"
                    symbol "BKEP"
                    exchange "NASDAQ"
                }
                {
                    name "Black Hawk Acquisition Corp"
                    symbol "BKHA"
                    exchange "NASDAQ"
                }
                {
                    name "Black Knight Inc"
                    symbol "BKI"
                    exchange "NYSE"
                }
                {
                    name "Bakkt Holdings Inc"
                    symbol "BKKT"
                    exchange "NYSE"
                }
                {
                    name "Booking Holdings Inc"
                    symbol "BKNG"
                    exchange "NASDAQ"
                }
                {
                    name "Baker Hughes Co"
                    symbol "BKR"
                    exchange "NASDAQ"
                }
                {
                    name "Blacksky Technology Inc"
                    symbol "BKSY"
                    exchange "NYSE"
                }
                {
                    name "Bk Technologies Corp"
                    symbol "BKTI"
                    exchange "NYSEMKT"
                }
                {
                    name "Bkv Corp"
                    symbol "BKV"
                    exchange "NYSE"
                }
                {
                    name "Bio Key International Inc"
                    symbol "BKYI"
                    exchange "NASDAQ"
                }
                {
                    name "Blackline Inc"
                    symbol "BL"
                    exchange "NASDAQ"
                }
                {
                    name "Bellevue Life Sciences Acquisition Corp"
                    symbol "BLAC"
                    exchange "NASDAQ"
                }
                {
                    name "Blackboxstocks Inc"
                    symbol "BLBX"
                    exchange "NASDAQ"
                }
                {
                    name "Topbuild Corp"
                    symbol "BLD"
                    exchange "NYSE"
                }
                {
                    name "Baldwin Technology Co Inc"
                    symbol "BLD1"
                    exchange "NYSEMKT"
                }
                {
                    name "Blade Air Mobility Inc"
                    symbol "BLDE"
                    exchange "NASDAQ"
                }
                {
                    name "Ballard Power Systems Inc"
                    symbol "BLDP"
                    exchange "NASDAQ"
                }
                {
                    name "Bleuacacia Ltd"
                    symbol "BLEU"
                    exchange "NASDAQ"
                }
                {
                    name "Bridgeline Digital Inc"
                    symbol "BLIN"
                    exchange "NASDAQ"
                }
                {
                    name "Blackbaud Inc"
                    symbol "BLKB"
                    exchange "NASDAQ"
                }
                {
                    name "Blend Labs Inc"
                    symbol "BLND"
                    exchange "NYSE"
                }
                {
                    name "Belong Acquisition Corp"
                    symbol "BLNG"
                    exchange "NASDAQ"
                }
                {
                    name "Blink Charging Co"
                    symbol "BLNK"
                    exchange "NASDAQ"
                }
                {
                    name "Bladelogic Inc"
                    symbol "BLOG"
                    exchange "NASDAQ"
                }
                {
                    name "Infoblox Inc"
                    symbol "BLOX"
                    exchange "NYSE"
                }
                {
                    name "Boron Lepore & Associates Inc"
                    symbol "BLPG1"
                    exchange "NASDAQ"
                }
                {
                    name "Bcls Acquisition Corp"
                    symbol "BLSA"
                    exchange "NASDAQ"
                }
                {
                    name "Bluestone Software Inc"
                    symbol "BLSW1"
                    exchange "NASDAQ"
                }
                {
                    name "Blount International Inc"
                    symbol "BLT"
                    exchange "NYSE"
                }
                {
                    name "Bright Lights Acquisition Corp"
                    symbol "BLTS"
                    exchange "NASDAQ"
                }
                {
                    name "Blueriver Acquisition Corp"
                    symbol "BLUAF"
                    exchange "NYSE"
                }
                {
                    name "Blue Martini Software Inc"
                    symbol "BLUE1"
                    exchange "NASDAQ"
                }
                {
                    name "Boulevard Acquisition Corp Ii"
                    symbol "BLVD"
                    exchange "NASDAQ"
                }
                {
                    name "Backblaze Inc"
                    symbol "BLZE"
                    exchange "NASDAQ"
                }
                {
                    name "Blaze Software Inc"
                    symbol "BLZE1"
                    exchange "NASDAQ"
                }
                {
                    name "Black Mountain Acquisition Corp"
                    symbol "BMAC"
                    exchange "NYSE"
                }
                {
                    name "Birman Managed Care Inc"
                    symbol "BMAN"
                    exchange "NASDAQ"
                }
                {
                    name "Blockchain Moon Acquisition Corp"
                    symbol "BMAQ"
                    exchange "NASDAQ"
                }
                {
                    name "Bumble Inc"
                    symbol "BMBL"
                    exchange "NASDAQ"
                }
                {
                    name "Bmc Software Inc"
                    symbol "BMC"
                    exchange "NASDAQ"
                }
                {
                    name "Badger Meter Inc"
                    symbol "BMI"
                    exchange "NYSE"
                }
                {
                    name "Beamr Imaging Ltd"
                    symbol "BMR"
                    exchange "NASDAQ"
                }
                {
                    name "Benchmarq Microelectronics Inc"
                    symbol "BMRQ"
                    exchange "NASDAQ"
                }
                {
                    name "Bright Mountain Media Inc"
                    symbol "BMTM"
                    exchange "NASDAQ"
                }
                {
                    name "Bm Technologies Inc"
                    symbol "BMTX"
                    exchange "NYSEMKT"
                }
                {
                    name "Banta Corp"
                    symbol "BN1"
                    exchange "NASDAQ"
                }
                {
                    name "Brand Engagement Network Inc"
                    symbol "BNAI"
                    exchange "NASDAQ"
                }
                {
                    name "Bowne & Co Inc"
                    symbol "BNE1"
                    exchange "NASDAQ"
                }
                {
                    name "Benefitfocus Inc"
                    symbol "BNFT"
                    exchange "NASDAQ"
                }
                {
                    name "Burlington Northern Santa Fe Corp"
                    symbol "BNI"
                    exchange "NASDAQ"
                }
                {
                    name "Bannix Acquisition Corp"
                    symbol "BNIX"
                    exchange "NASDAQ"
                }
                {
                    name "Banner Acquisition Corp"
                    symbol "BNNR"
                    exchange "NASDAQ"
                }
                {
                    name "Bonso Electronics International Inc"
                    symbol "BNSOF"
                    exchange "NASDAQ"
                }
                {
                    name "Banzai International Inc"
                    symbol "BNZI"
                    exchange "NASDAQ"
                }
                {
                    name "Bluescape Opportunities Acquisition Corp"
                    symbol "BOAC"
                    exchange "NYSE"
                }
                {
                    name "Business Objects Sa"
                    symbol "BOBJY"
                    exchange "NASDAQ"
                }
                {
                    name "Blue Ocean Acquisition Corp"
                    symbol "BOCN"
                    exchange "NASDAQ"
                }
                {
                    name "Belco Oil & Gas Corp"
                    symbol "BOG"
                    exchange "NYSE"
                }
                {
                    name "Bolder Technologies Corp"
                    symbol "BOLDQ"
                    exchange "NASDAQ"
                }
                {
                    name "Bolt Technology Corp"
                    symbol "BOLT1"
                    exchange "NASDAQ"
                }
                {
                    name "Boole & Babbage Inc"
                    symbol "BOOL"
                    exchange "NASDAQ"
                }
                {
                    name "Dmc Global Inc"
                    symbol "BOOM"
                    exchange "NASDAQ"
                }
                {
                    name "Boise Cascade Office Products Corp"
                    symbol "BOP"
                    exchange "NYSE"
                }
                {
                    name "Burns International Services Corp"
                    symbol "BOR"
                    exchange "NYSE"
                }
                {
                    name "Borland Software Corp"
                    symbol "BORL"
                    exchange "NASDAQ"
                }
                {
                    name "Borr Drilling Ltd"
                    symbol "BORR"
                    exchange "NYSE"
                }
                {
                    name "Boston Acoustics Inc"
                    symbol "BOSA"
                    exchange "NASDAQ"
                }
                {
                    name "Bos Better Online Solutions Ltd"
                    symbol "BOSC"
                    exchange "NASDAQ"
                }
                {
                    name "Bowen Acquisition Corp"
                    symbol "BOWN"
                    exchange "NASDAQ"
                }
                {
                    name "Box Inc"
                    symbol "BOX"
                    exchange "NYSE"
                }
                {
                    name "Seacube Container Leasing Ltd"
                    symbol "BOX1"
                    exchange "NYSE"
                }
                {
                    name "Boxlight Corp"
                    symbol "BOXL"
                    exchange "NASDAQ"
                }
                {
                    name "Boyd Bros Transportation Inc"
                    symbol "BOYD1"
                    exchange "NASDAQ"
                }
                {
                    name "Bp Plc"
                    symbol "BP"
                    exchange "NYSE"
                }
                {
                    name "Bullpen Parlay Acquisition Co"
                    symbol "BPAC"
                    exchange "NASDAQ"
                }
                {
                    name "Baldwin Piano & Organ Co"
                    symbol "BPAO"
                    exchange "NASDAQ"
                }
                {
                    name "Ba Merchant Services Inc"
                    symbol "BPI.A"
                    exchange "NYSE"
                }
                {
                    name "Bpi Energy Holdings Inc"
                    symbol "BPIGF"
                    exchange "NYSEMKT"
                }
                {
                    name "Buckeye Partners Lp"
                    symbol "BPL"
                    exchange "NYSE"
                }
                {
                    name "Bp Midstream Partners Lp"
                    symbol "BPMP"
                    exchange "NYSE"
                }
                {
                    name "Bpo Management Services"
                    symbol "BPOM"
                    exchange "NASDAQ"
                }
                {
                    name "Bp Prudhoe Bay Royalty Trust"
                    symbol "BPT"
                    exchange "NYSE"
                }
                {
                    name "Bridgeport Machines Inc"
                    symbol "BPTM"
                    exchange "NASDAQ"
                }
                {
                    name "Brandpartners Group Inc"
                    symbol "BPTR"
                    exchange "NASDAQ"
                }
                {
                    name "Bpz Resources Inc"
                    symbol "BPZRQ"
                    exchange "NYSE"
                }
                {
                    name "Broadridge Financial Solutions Inc"
                    symbol "BR"
                    exchange "NYSE"
                }
                {
                    name "Burlington Resources Inc"
                    symbol "BR1"
                    exchange "NYSE"
                }
                {
                    name "Broad Capital Acquisition Corp"
                    symbol "BRAC"
                    exchange "NASDAQ"
                }
                {
                    name "Baran Group Ltd"
                    symbol "BRANF"
                    exchange "NASDAQ"
                }
                {
                    name "Brady Corp"
                    symbol "BRC"
                    exchange "NYSE"
                }
                {
                    name "Brocade Communications Systems Inc"
                    symbol "BRCD"
                    exchange "NASDAQ"
                }
                {
                    name "Broadcom Corp"
                    symbol "BRCM"
                    exchange "NASDAQ"
                }
                {
                    name "Beard Energy Transition Acquisition Corp"
                    symbol "BRD"
                    exchange "NYSE"
                }
                {
                    name "Bridge Technology Inc"
                    symbol "BRDG1"
                    exchange "NASDAQ"
                }
                {
                    name "Borderfree Inc"
                    symbol "BRDR"
                    exchange "NASDAQ"
                }
                {
                    name "Bird Global Inc"
                    symbol "BRDSQ"
                    exchange "NYSE"
                }
                {
                    name "Brek Energy Corp"
                    symbol "BREK"
                    exchange "NASDAQ"
                }
                {
                    name "Breeze Holdings Acquisition Corp"
                    symbol "BREZ"
                    exchange "NASDAQ"
                }
                {
                    name "Brio Software Inc"
                    symbol "BRIO"
                    exchange "NASDAQ"
                }
                {
                    name "B Riley Principal 250 Merger Corp"
                    symbol "BRIV"
                    exchange "NASDAQ"
                }
                {
                    name "Bracknell Corp"
                    symbol "BRKC1"
                    exchange "NASDAQ"
                }
                {
                    name "Burtech Acquisition Corp"
                    symbol "BRKH"
                    exchange "NASDAQ"
                }
                {
                    name "Brooktrout Inc"
                    symbol "BRKT"
                    exchange "NASDAQ"
                }
                {
                    name "Syntax-Brillian Corp"
                    symbol "BRLCQ"
                    exchange "NASDAQ"
                }
                {
                    name "Borealis Technology Corp"
                    symbol "BRLS1"
                    exchange "NASDAQ"
                }
                {
                    name "Barnwell Industries Inc"
                    symbol "BRN"
                    exchange "NYSEMKT"
                }
                {
                    name "Bronco Drilling Company Inc"
                    symbol "BRNC"
                    exchange "NASDAQ"
                }
                {
                    name "Braun Consulting Inc"
                    symbol "BRNC1"
                    exchange "NASDAQ"
                }
                {
                    name "Broderbund Software Inc"
                    symbol "BROD1"
                    exchange "NASDAQ"
                }
                {
                    name "Brooge Energy Ltd"
                    symbol "BROG"
                    exchange "NASDAQ"
                }
                {
                    name "Borqs Technologies Inc"
                    symbol "BRQSF"
                    exchange "NASDAQ"
                }
                {
                    name "Acr Group Inc"
                    symbol "BRR"
                    exchange "NYSEMKT"
                }
                {
                    name "Barrett Resources Corp"
                    symbol "BRR1"
                    exchange "NYSE"
                }
                {
                    name "Global Brass & Copper Holdings Inc"
                    symbol "BRSS"
                    exchange "NYSE"
                }
                {
                    name "Burst Com Inc"
                    symbol "BRST1"
                    exchange "NASDAQ"
                }
                {
                    name "Bristow Group Inc"
                    symbol "BRSWQ"
                    exchange "NYSE"
                }
                {
                    name "Berry Corp (Bry)"
                    symbol "BRY"
                    exchange "NASDAQ"
                }
                {
                    name "Berry Petroleum Co"
                    symbol "BRY1"
                    exchange "NYSE"
                }
                {
                    name "Braze Inc"
                    symbol "BRZE"
                    exchange "NASDAQ"
                }
                {
                    name "Broadsoft Inc"
                    symbol "BSFT"
                    exchange "NASDAQ"
                }
                {
                    name "Black Spade Acquisition Ii Co"
                    symbol "BSIIU"
                    exchange "NASDAQ"
                }
                {
                    name "Big Sky Growth Partners Inc"
                    symbol "BSKY"
                    exchange "NASDAQ"
                }
                {
                    name "Black Stone Minerals Lp"
                    symbol "BSM"
                    exchange "NYSE"
                }
                {
                    name "Basin Exploration Inc"
                    symbol "BSNX"
                    exchange "NASDAQ"
                }
                {
                    name "Bsquare Corp"
                    symbol "BSQR"
                    exchange "NASDAQ"
                }
                {
                    name "Bestway Inc"
                    symbol "BSTW"
                    exchange "NASDAQ"
                }
                {
                    name "Bentley Systems Inc"
                    symbol "BSY"
                    exchange "NASDAQ"
                }
                {
                    name "Burgundy Technology Acquisition Corp"
                    symbol "BTAQ"
                    exchange "NASDAQ"
                }
                {
                    name "Banctec Inc"
                    symbol "BTC1"
                    exchange "NYSE"
                }
                {
                    name "Bit Mining Ltd"
                    symbol "BTCM"
                    exchange "NYSE"
                }
                {
                    name "Bitdeer Technologies Group"
                    symbol "BTDR"
                    exchange "NASDAQ"
                }
                {
                    name "Baytex Energy Corp"
                    symbol "BTE"
                    exchange "NYSE"
                }
                {
                    name "Bt Office Products International Inc"
                    symbol "BTF1"
                    exchange "NYSE"
                }
                {
                    name "Btg Inc"
                    symbol "BTGI"
                    exchange "NASDAQ"
                }
                {
                    name "Brocker Technology Group Ltd"
                    symbol "BTGL"
                    exchange "NASDAQ"
                }
                {
                    name "Blyth Inc"
                    symbol "BTH"
                    exchange "NYSE"
                }
                {
                    name "Benthos Inc"
                    symbol "BTHS"
                    exchange "NASDAQ"
                }
                {
                    name "Brunswick Technologies Inc"
                    symbol "BTIC"
                    exchange "NASDAQ"
                }
                {
                    name "Armlogi Holding Corp"
                    symbol "BTOC"
                    exchange "NASDAQ"
                }
                {
                    name "Btrs Holdings Inc"
                    symbol "BTRS"
                    exchange "NASDAQ"
                }
                {
                    name "Brightstar Information Technology Group Inc"
                    symbol "BTSR"
                    exchange "NASDAQ"
                }
                {
                    name "Btu International Inc"
                    symbol "BTUI"
                    exchange "NASDAQ"
                }
                {
                    name "Bucyrus International Inc"
                    symbol "BUCY"
                    exchange "NASDAQ"
                }
                {
                    name "Bukit Jalil Global Acquisition 1 Ltd"
                    symbol "BUJA"
                    exchange "NASDAQ"
                }
                {
                    name "Nuburu Inc"
                    symbol "BURU"
                    exchange "NYSEMKT"
                }
                {
                    name "Busybox Com Inc"
                    symbol "BUSY"
                    exchange "NASDAQ"
                }
                {
                    name "Butler International Inc"
                    symbol "BUTLQ"
                    exchange "NASDAQ"
                }
                {
                    name "Brightview Holdings Inc"
                    symbol "BV"
                    exchange "NYSE"
                }
                {
                    name "Bazaarvoice Inc"
                    symbol "BV1"
                    exchange "NASDAQ"
                }
                {
                    name "Bindview Development Corp"
                    symbol "BVEW"
                    exchange "NASDAQ"
                }
                {
                    name "Brite Voice Systems Inc"
                    symbol "BVSI"
                    exchange "NASDAQ"
                }
                {
                    name "Broadvision Inc"
                    symbol "BVSN"
                    exchange "NASDAQ"
                }
                {
                    name "Babcock & Wilcox Enterprises Inc"
                    symbol "BW"
                    exchange "NYSE"
                }
                {
                    name "Better World Acquisition Corp"
                    symbol "BWAC"
                    exchange "NASDAQ"
                }
                {
                    name "Breakaway Solutions Inc"
                    symbol "BWAY1"
                    exchange "NASDAQ"
                }
                {
                    name "Blue Whale Acquisition Corp I"
                    symbol "BWC"
                    exchange "NASDAQ"
                }
                {
                    name "Belden Inc"
                    symbol "BWC1"
                    exchange "NYSE"
                }
                {
                    name "Backweb Technologies Ltd"
                    symbol "BWEBF"
                    exchange "NASDAQ"
                }
                {
                    name "Broadwind Inc"
                    symbol "BWEN"
                    exchange "NASDAQ"
                }
                {
                    name "Bw Lpg Ltd"
                    symbol "BWLP"
                    exchange "NYSE"
                }
                {
                    name "Bowman Consulting Group Ltd"
                    symbol "BWMN"
                    exchange "NASDAQ"
                }
                {
                    name "Wowjoint Holdings Ltd"
                    symbol "BWOWF"
                    exchange "NASDAQ"
                }
                {
                    name "Boardwalk Pipeline Partners Lp"
                    symbol "BWP"
                    exchange "NYSE"
                }
                {
                    name "Blue Wave Systems Inc"
                    symbol "BWSI"
                    exchange "NASDAQ"
                }
                {
                    name "Bwx Technologies Inc"
                    symbol "BWXT"
                    exchange "NYSE"
                }
                {
                    name "Bluelinx Holdings Inc"
                    symbol "BXC"
                    exchange "NYSE"
                }
                {
                    name "Bellatrix Exploration Ltd"
                    symbol "BXEFF"
                    exchange "NYSE"
                }
                {
                    name "Bally Technologies Inc"
                    symbol "BYI"
                    exchange "NYSE"
                }
                {
                    name "Beyond Com Corp"
                    symbol "BYNDQ"
                    exchange "NASDAQ"
                }
                {
                    name "Bynordic Acquisition Corp"
                    symbol "BYNO"
                    exchange "NASDAQ"
                }
                {
                    name "Byrna Technologies Inc"
                    symbol "BYRN"
                    exchange "NASDAQ"
                }
                {
                    name "Kanzhun Ltd"
                    symbol "BZ"
                    exchange "NASDAQ"
                }
                {
                    name "Breeze-Eastern Corp"
                    symbol "BZC"
                    exchange "NYSEMKT"
                }
                {
                    name "Ca Inc"
                    symbol "CA1"
                    exchange "NASDAQ"
                }
                {
                    name "Corporacion America Airports Sa"
                    symbol "CAAP"
                    exchange "NYSE"
                }
                {
                    name "Cameron Ashley Building Products Inc"
                    symbol "CAB1"
                    exchange "NYSE"
                }
                {
                    name "Chart Acquisition Corp"
                    symbol "CACGU"
                    exchange "NASDAQ"
                }
                {
                    name "Caci International Inc"
                    symbol "CACI"
                    exchange "NYSE"
                }
                {
                    name "Carrier Access Corp"
                    symbol "CACS"
                    exchange "NASDAQ"
                }
                {
                    name "Cam Commerce Solutions Inc"
                    symbol "CADA"
                    exchange "NASDAQ"
                }
                {
                    name "Cade Industries Inc"
                    symbol "CADE2"
                    exchange "NASDAQ"
                }
                {
                    name "Cae Inc"
                    symbol "CAE"
                    exchange "NYSE"
                }
                {
                    name "Caere Corp"
                    symbol "CAER"
                    exchange "NASDAQ"
                }
                {
                    name "Cai International Inc"
                    symbol "CAI"
                    exchange "NYSE"
                }
                {
                    name "Capital Associates Inc"
                    symbol "CAII"
                    exchange "NASDAQ"
                }
                {
                    name "Corsair Communications Inc"
                    symbol "CAIR"
                    exchange "NASDAQ"
                }
                {
                    name "Cais Internet Inc"
                    symbol "CAIS"
                    exchange "NASDAQ"
                }
                {
                    name "Canon Inc"
                    symbol "CAJPY"
                    exchange "NYSE"
                }
                {
                    name "United Airlines Inc"
                    symbol "CAL1"
                    exchange "NYSE"
                }
                {
                    name "Catalina Lighting Inc"
                    symbol "CALAQ"
                    exchange "NASDAQ"
                }
                {
                    name "Callidus Software Inc"
                    symbol "CALD"
                    exchange "NASDAQ"
                }
                {
                    name "Calix Inc"
                    symbol "CALX"
                    exchange "NYSE"
                }
                {
                    name "Cameron International Corp"
                    symbol "CAM"
                    exchange "NYSE"
                }
                {
                    name "Camco International Inc"
                    symbol "CAM1"
                    exchange "NYSE"
                }
                {
                    name "Cambridge Capital Acquisition Corp"
                    symbol "CAMB"
                    exchange "NASDAQ"
                }
                {
                    name "Cambio Inc"
                    symbol "CAMBA"
                    exchange "NASDAQ"
                }
                {
                    name "California Micro Devices Corp"
                    symbol "CAMD"
                    exchange "NASDAQ"
                }
                {
                    name "Calamp Corp"
                    symbol "CAMPQ"
                    exchange "NASDAQ"
                }
                {
                    name "Camtek Ltd"
                    symbol "CAMT"
                    exchange "NASDAQ"
                }
                {
                    name "Caminus Corp"
                    symbol "CAMZ"
                    exchange "NASDAQ"
                }
                {
                    name "Canaan Inc"
                    symbol "CAN"
                    exchange "NASDAQ"
                }
                {
                    name "Carreker Corp"
                    symbol "CANI"
                    exchange "NASDAQ"
                }
                {
                    name "Cano Petroleum Inc"
                    symbol "CANOQ1"
                    exchange "NYSEMKT"
                }
                {
                    name "Canisco Resources Inc"
                    symbol "CANR1"
                    exchange "NASDAQ"
                }
                {
                    name "Canargo Energy Corp"
                    symbol "CANRQ"
                    exchange "NYSEMKT"
                }
                {
                    name "Captaris Inc"
                    symbol "CAPA1"
                    exchange "NASDAQ"
                }
                {
                    name "Caprius Inc"
                    symbol "CAPI"
                    exchange "NASDAQ"
                }
                {
                    name "Crossamerica Partners Lp"
                    symbol "CAPL"
                    exchange "NYSE"
                }
                {
                    name "Cayson Acquisition Corp"
                    symbol "CAPNU"
                    exchange "NASDAQ"
                }
                {
                    name "Captivision Inc"
                    symbol "CAPT"
                    exchange "NASDAQ"
                }
                {
                    name "Avis Budget Group Inc"
                    symbol "CAR"
                    exchange "NASDAQ"
                }
                {
                    name "Carbonite Inc"
                    symbol "CARB"
                    exchange "NASDAQ"
                }
                {
                    name "Chazak Value Corp"
                    symbol "CARD1"
                    exchange "NASDAQ"
                }
                {
                    name "Carescience Inc"
                    symbol "CARE1"
                    exchange "NASDAQ"
                }
                {
                    name "Careinsite Inc"
                    symbol "CARI"
                    exchange "NASDAQ"
                }
                {
                    name "Carleton Corp"
                    symbol "CARL1"
                    exchange "NASDAQ"
                }
                {
                    name "Cascade Acquisition Corp"
                    symbol "CAS"
                    exchange "NYSE"
                }
                {
                    name "Cascade Corp"
                    symbol "CASC1"
                    exchange "NYSE"
                }
                {
                    name "Cass Information Systems Inc"
                    symbol "CASS"
                    exchange "NASDAQ"
                }
                {
                    name "Casa Systems Inc"
                    symbol "CASSQ"
                    exchange "NASDAQ"
                }
                {
                    name "Citation Corp"
                    symbol "CAST1"
                    exchange "NASDAQ"
                }
                {
                    name "Caterpillar Inc"
                    symbol "CAT"
                    exchange "NYSE"
                }
                {
                    name "Cardtronics Plc"
                    symbol "CATM"
                    exchange "NASDAQ"
                }
                {
                    name "Cambridge Technology Partners Massachusetts Inc"
                    symbol "CATP"
                    exchange "NASDAQ"
                }
                {
                    name "Catalyst Semiconductor Inc"
                    symbol "CATS1"
                    exchange "NASDAQ"
                }
                {
                    name "Catapult Communications Corp"
                    symbol "CATT"
                    exchange "NASDAQ"
                }
                {
                    name "C Ats Software Inc"
                    symbol "CATX1"
                    exchange "NASDAQ"
                }
                {
                    name "Computer Access Technology Corp"
                    symbol "CATZ"
                    exchange "NASDAQ"
                }
                {
                    name "Collective Audience Inc"
                    symbol "CAUD"
                    exchange "NASDAQ"
                }
                {
                    name "Cavium Inc"
                    symbol "CAVM"
                    exchange "NASDAQ"
                }
                {
                    name "Cavion Technologies Inc"
                    symbol "CAVN"
                    exchange "NASDAQ"
                }
                {
                    name "Cavico Corp"
                    symbol "CAVO"
                    exchange "NASDAQ"
                }
                {
                    name "Cayenne Software Inc"
                    symbol "CAYN"
                    exchange "NASDAQ"
                }
                {
                    name "Cbak Energy Technology Inc"
                    symbol "CBAT"
                    exchange "NASDAQ"
                }
                {
                    name "Cooper Industries Plc"
                    symbol "CBE"
                    exchange "NYSE"
                }
                {
                    name "China Integrated Energy Inc"
                    symbol "CBEH"
                    exchange "NASDAQ"
                }
                {
                    name "Chicago Bridge & Iron Co N V"
                    symbol "CBI"
                    exchange "NYSE"
                }
                {
                    name "C Bridge Internet Solutions Inc"
                    symbol "CBIS1"
                    exchange "NASDAQ"
                }
                {
                    name "Carbon Black Inc"
                    symbol "CBLK"
                    exchange "NASDAQ"
                }
                {
                    name "Cobalt Group Inc"
                    symbol "CBLT"
                    exchange "NASDAQ"
                }
                {
                    name "Cubic Energy Inc"
                    symbol "CBNRQ"
                    exchange "NYSEMKT"
                }
                {
                    name "Chain Bridge I"
                    symbol "CBRG"
                    exchange "NASDAQ"
                }
                {
                    name "Ciber Inc"
                    symbol "CBRI"
                    exchange "NYSE"
                }
                {
                    name "Cybex Computer Products Corp"
                    symbol "CBXC"
                    exchange "NASDAQ"
                }
                {
                    name "Cbiz Inc"
                    symbol "CBZ"
                    exchange "NYSE"
                }
                {
                    name "Cort Business Services Corp"
                    symbol "CBZ2"
                    exchange "NYSE"
                }
                {
                    name "Corrections Corp Of America"
                    symbol "CCA1"
                    exchange "NYSE"
                }
                {
                    name "Cascadia Acquisition Corp"
                    symbol "CCAI"
                    exchange "NASDAQ"
                }
                {
                    name "Ccair Inc"
                    symbol "CCAR"
                    exchange "NASDAQ"
                }
                {
                    name "C-Cor Inc"
                    symbol "CCBL"
                    exchange "NASDAQ"
                }
                {
                    name "Ccc Intelligent Solutions Holdings Inc"
                    symbol "CCCS"
                    exchange "NASDAQ"
                }
                {
                    name "Capital Clean Energy Carriers Corp"
                    symbol "CCEC"
                    exchange "NASDAQ"
                }
                {
                    name "China Cgame Inc"
                    symbol "CCGM"
                    exchange "NASDAQ"
                }
                {
                    name "Churchill Capital Corp Ix"
                    symbol "CCIX"
                    exchange "NASDAQ"
                }
                {
                    name "Coleman Cable Inc"
                    symbol "CCIX2"
                    exchange "NASDAQ"
                }
                {
                    name "Carnival Corp"
                    symbol "CCL"
                    exchange "NYSE"
                }
                {
                    name "Commodore Holdings Ltd"
                    symbol "CCLN"
                    exchange "NASDAQ"
                }
                {
                    name "Csi Compressco Lp"
                    symbol "CCLP"
                    exchange "NASDAQ"
                }
                {
                    name "Cmc Materials Inc"
                    symbol "CCMP"
                    exchange "NASDAQ"
                }
                {
                    name "Cabletel Communications Corp"
                    symbol "CCMTF"
                    exchange "NYSEMKT"
                }
                {
                    name "Cardconnect Corp"
                    symbol "CCN"
                    exchange "NASDAQ"
                }
                {
                    name "China Customer Relations Centers Inc"
                    symbol "CCRC"
                    exchange "NASDAQ"
                }
                {
                    name "Corecard Corp"
                    symbol "CCRD"
                    exchange "NYSE"
                }
                {
                    name "Concord Communications Inc"
                    symbol "CCRD1"
                    exchange "NASDAQ"
                }
                {
                    name "Coherent Communications Systems Corp"
                    symbol "CCSC1"
                    exchange "NASDAQ"
                }
                {
                    name "Consensus Cloud Solutions Inc"
                    symbol "CCSI"
                    exchange "NASDAQ"
                }
                {
                    name "Ccsc Technology International Holdings Ltd"
                    symbol "CCTG"
                    exchange "NASDAQ"
                }
                {
                    name "Cactus Acquisition Corp 1 Ltd"
                    symbol "CCTS"
                    exchange "NASDAQ"
                }
                {
                    name "Cfi Proservices Inc"
                    symbol "CCTX"
                    exchange "NASDAQ"
                }
                {
                    name "Ccur Holdings Inc"
                    symbol "CCUR"
                    exchange "NASDAQ"
                }
                {
                    name "Churchill Capital Corp V"
                    symbol "CCV"
                    exchange "NYSE"
                }
                {
                    name "Churchill Capital Corp Vi"
                    symbol "CCVI"
                    exchange "NYSE"
                }
                {
                    name "Chindata Group Holdings Ltd"
                    symbol "CD"
                    exchange "NASDAQ"
                }
                {
                    name "Compass Digital Acquisition Corp"
                    symbol "CDAQ"
                    exchange "NASDAQ"
                }
                {
                    name "Cdc Corp"
                    symbol "CDCAQ"
                    exchange "NASDAQ"
                }
                {
                    name "Caredata Com Inc"
                    symbol "CDCM"
                    exchange "NASDAQ"
                }
                {
                    name "Cidco Inc"
                    symbol "CDCO1"
                    exchange "NASDAQ"
                }
                {
                    name "Cdc Software Corp"
                    symbol "CDCSY"
                    exchange "NASDAQ"
                }
                {
                    name "Compudyne Corp"
                    symbol "CDCY"
                    exchange "NASDAQ"
                }
                {
                    name "Cordant Technologies Inc"
                    symbol "CDD"
                    exchange "NYSE"
                }
                {
                    name "Constellation 3D Inc"
                    symbol "CDDDQ"
                    exchange "NASDAQ"
                }
                {
                    name "C 3D Digital Inc"
                    symbol "CDDT"
                    exchange "NYSEMKT"
                }
                {
                    name "Cliffs Drilling Co"
                    symbol "CDG"
                    exchange "NYSE"
                }
                {
                    name "Cdi Corp"
                    symbol "CDI"
                    exchange "NYSE"
                }
                {
                    name "Cd International Enterprises Inc"
                    symbol "CDIIQ"
                    exchange "NASDAQ"
                }
                {
                    name "Cdk Global Inc"
                    symbol "CDK"
                    exchange "NASDAQ"
                }
                {
                    name "Cadeler A"
                    symbol "CDLR"
                    exchange "NYSE"
                }
                {
                    name "Cadmus Communications Corp"
                    symbol "CDMS"
                    exchange "NASDAQ"
                }
                {
                    name "Cadence Design Systems Inc"
                    symbol "CDNS"
                    exchange "NASDAQ"
                }
                {
                    name "Comps Com Inc"
                    symbol "CDOT"
                    exchange "NASDAQ"
                }
                {
                    name "Code Rebel Corp"
                    symbol "CDRBQ"
                    exchange "NASDAQ"
                }
                {
                    name "Cadre Holdings Inc"
                    symbol "CDRE"
                    exchange "NYSE"
                }
                {
                    name "Cold Spring Capital Inc"
                    symbol "CDS2"
                    exchange "NYSEMKT"
                }
                {
                    name "Cumetrix Data Systems Corp"
                    symbol "CDSC"
                    exchange "NASDAQ"
                }
            ]
        }
    }
}
