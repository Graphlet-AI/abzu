class TickerList {
  tickers Ticker[]
}

function AddTickersToCompanies(company_list: CompanyList, ticker_list: TickerList) -> CompanyList {
  // see clients.baml
  client GeminiFallback

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
                    id 1
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
                    id 2
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
                    id 3
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
                    id 4
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
                    symbol "AMD"
                    exchange "NASDAQ"
                }
                {
                    symbol "AAC"
                    exchange "NYSE"
                }
                {
                    symbol "AACI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AACPF"
                    exchange "NASDAQ"
                }
                {
                    symbol "AACT"
                    exchange "NYSE"
                }
                {
                    symbol "AAI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AAI1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AAIIQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AAL"
                    exchange "NASDAQ"
                }
                {
                    symbol "AAM"
                    exchange "NYSE"
                }
                {
                    symbol "AAMRQ"
                    exchange "NYSE"
                }
                {
                    symbol "AAN"
                    exchange "NYSE"
                }
                {
                    symbol "AAOI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AAPL"
                    exchange "NASDAQ"
                }
                {
                    symbol "AAQC"
                    exchange "NYSE"
                }
                {
                    symbol "AATC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AATI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AATI1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AATT"
                    exchange "NASDAQ"
                }
                {
                    symbol "AAVVF"
                    exchange "NYSE"
                }
                {
                    symbol "AAWHQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AAWW"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABACQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABAT1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABBNY"
                    exchange "NYSE"
                }
                {
                    symbol "ABCC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABDR1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABF"
                    exchange "NYSE"
                }
                {
                    symbol "ABGBY"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABGI"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABHH"
                    exchange "NYSE"
                }
                {
                    symbol "ABILF"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABIX"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABM"
                    exchange "NYSE"
                }
                {
                    symbol "ABNB"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABNTQ"
                    exchange "NYSE"
                }
                {
                    symbol "ABOV"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABRX1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABST"
                    exchange "NASDAQ"
                }
                {
                    symbol "ABTE"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACA"
                    exchange "NYSE"
                }
                {
                    symbol "ACAB"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACAC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACAH"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACAQ"
                    exchange "NYSE"
                }
                {
                    symbol "ACAT"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACBA"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACCD1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACCL"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACCO"
                    exchange "NYSE"
                }
                {
                    symbol "ACDC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACDI"
                    exchange "NYSE"
                }
                {
                    symbol "ACEC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACEE"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACFN"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACHR"
                    exchange "NYSE"
                }
                {
                    symbol "ACIA"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACII"
                    exchange "NYSE"
                }
                {
                    symbol "ACIW"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACKIU"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACLA"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACLI"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACLNF"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACLO"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACLS"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACM"
                    exchange "NYSE"
                }
                {
                    symbol "ACMM"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACMR"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACN"
                    exchange "NYSE"
                }
                {
                    symbol "ACNAQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACO"
                    exchange "NYSE"
                }
                {
                    symbol "ACOM"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACOM1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACQR"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACRO"
                    exchange "NYSE"
                }
                {
                    symbol "ACRO1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACRUQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACS"
                    exchange "NYSE"
                }
                {
                    symbol "ACSC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACSEF"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACTA"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACTG"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACTI"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACTI1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACTL1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACTRQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACTS"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACTV1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ACTV2"
                    exchange "NYSE"
                }
                {
                    symbol "ACVC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AD"
                    exchange "NYSE"
                }
                {
                    symbol "ADAL"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADAM"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADAPQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADAX"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADBE"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADBL"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADCC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADCT1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADEA"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADEP"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADER"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADEX1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADFC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADFS"
                    exchange "NYSEMKT"
                }
                {
                    symbol "ADGI1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "ADI"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADIC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADK1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "ADLTQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADNC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADO"
                    exchange "NYSE"
                }
                {
                    symbol "ADP"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADPC"
                    exchange "NYSE"
                }
                {
                    symbol "ADRT"
                    exchange "NYSEMKT"
                }
                {
                    symbol "ADSC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADSE"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADSI"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADSK"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADSO1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADSPQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADST"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADSW"
                    exchange "NYSE"
                }
                {
                    symbol "ADT"
                    exchange "NYSE"
                }
                {
                    symbol "ADT1"
                    exchange "NYSE"
                }
                {
                    symbol "ADTCQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADTN"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADVS"
                    exchange "NASDAQ"
                }
                {
                    symbol "ADZA"
                    exchange "NASDAQ"
                }
                {
                    symbol "AE"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AEAC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AEAE"
                    exchange "NASDAQ"
                }
                {
                    symbol "AEDC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AEGN"
                    exchange "NASDAQ"
                }
                {
                    symbol "AEHR"
                    exchange "NASDAQ"
                }
                {
                    symbol "AEIC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AEIS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AENZ"
                    exchange "NYSE"
                }
                {
                    symbol "AEPI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AER"
                    exchange "NYSE"
                }
                {
                    symbol "AERG"
                    exchange "NASDAQ"
                }
                {
                    symbol "AERS1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AERT"
                    exchange "NASDAQ"
                }
                {
                    symbol "AESI"
                    exchange "NYSE"
                }
                {
                    symbol "AESP"
                    exchange "NASDAQ"
                }
                {
                    symbol "AETCQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AETUF"
                    exchange "NYSE"
                }
                {
                    symbol "AEYE"
                    exchange "NASDAQ"
                }
                {
                    symbol "AEYGQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AEZ"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AFAC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AFAQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AFAR"
                    exchange "NASDAQ"
                }
                {
                    symbol "AFCI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AFCO1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AFCX"
                    exchange "NASDAQ"
                }
                {
                    symbol "AFIS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AFJK"
                    exchange "NASDAQ"
                }
                {
                    symbol "AFLX"
                    exchange "NASDAQ"
                }
                {
                    symbol "AFOP"
                    exchange "NASDAQ"
                }
                {
                    symbol "AFRM"
                    exchange "NASDAQ"
                }
                {
                    symbol "AFTR"
                    exchange "NYSE"
                }
                {
                    symbol "AFWY"
                    exchange "NASDAQ"
                }
                {
                    symbol "AGACF"
                    exchange "NYSE"
                }
                {
                    symbol "AGAI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AGAM1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AGATQ"
                    exchange "NYSE"
                }
                {
                    symbol "AGCB"
                    exchange "NYSE"
                }
                {
                    symbol "AGCH"
                    exchange "NASDAQ"
                }
                {
                    symbol "AGCO"
                    exchange "NYSE"
                }
                {
                    symbol "AGD1"
                    exchange "NYSE"
                }
                {
                    symbol "AGFY"
                    exchange "NASDAQ"
                }
                {
                    symbol "AGGR"
                    exchange "NASDAQ"
                }
                {
                    symbol "AGIL1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AGILQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AGIS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AGMH"
                    exchange "NASDAQ"
                }
                {
                    symbol "AGNUQ"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AGR1"
                    exchange "NYSE"
                }
                {
                    symbol "AGS1"
                    exchange "NYSE"
                }
                {
                    symbol "AGX"
                    exchange "NYSE"
                }
                {
                    symbol "AGYS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AHAG"
                    exchange "NASDAQ"
                }
                {
                    symbol "AHI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AHII"
                    exchange "NASDAQ"
                }
                {
                    symbol "AHIZQ"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AHLS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AHNA"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AHNCQ"
                    exchange "NYSE"
                }
                {
                    symbol "ORCL"
                    exchange "NYSE"
                }
                {
                    symbol "AHRN"
                    exchange "NASDAQ"
                }
                {
                    symbol "AHWY"
                    exchange "NASDAQ"
                }
                {
                    symbol "AI"
                    exchange "NYSE"
                }
                {
                    symbol "AICOQ"
                    exchange "NYSE"
                }
                {
                    symbol "AIFF"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIH1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AIII1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIIXY"
                    exchange "NASDAQ"
                }
                {
                    symbol "AILE"
                    exchange "NASDAQ"
                }
                {
                    symbol "AILP"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIM1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AIMAU"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIMC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIND"
                    exchange "NASDAQ"
                }
                {
                    symbol "AINN"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIOT"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIP"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIPN"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIR"
                    exchange "NYSE"
                }
                {
                    symbol "AIRG"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIRI"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AIRM"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIRO1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIRS1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIRT"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIRV"
                    exchange "NASDAQ"
                }
                {
                    symbol "AISP"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIT"
                    exchange "NYSE"
                }
                {
                    symbol "AITR"
                    exchange "NASDAQ"
                }
                {
                    symbol "AIXI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AJRD"
                    exchange "NYSE"
                }
                {
                    symbol "AKAM"
                    exchange "NASDAQ"
                }
                {
                    symbol "AKIC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AKLMQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AKTS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AL"
                    exchange "NYSE"
                }
                {
                    symbol "ALAB"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALAC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALAN"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALAR"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALCY"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALDN"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALDV1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALDW"
                    exchange "NYSE"
                }
                {
                    symbol "ALF"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALFIQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALFO"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALG"
                    exchange "NYSE"
                }
                {
                    symbol "ALGM"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALGR"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALGT"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALIT"
                    exchange "NYSE"
                }
                {
                    symbol "ALJ"
                    exchange "NYSE"
                }
                {
                    symbol "ALJJ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALK"
                    exchange "NYSE"
                }
                {
                    symbol "ALKT"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALLE"
                    exchange "NYSE"
                }
                {
                    symbol "ALLR1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALLT"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALN1"
                    exchange "NYSE"
                }
                {
                    symbol "ALNK"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALNT"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALOR"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALOT"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALPH"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALPP"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALPSQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALRC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALRM"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALRN2"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALSA"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALSM"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALTG"
                    exchange "NYSE"
                }
                {
                    symbol "ALTR"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALTR1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALTS"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALTU"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALVRQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALY"
                    exchange "NYSE"
                }
                {
                    symbol "ALYAF"
                    exchange "NASDAQ"
                }
                {
                    symbol "ALYS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AM"
                    exchange "NYSE"
                }
                {
                    symbol "AM2"
                    exchange "NYSE"
                }
                {
                    symbol "AMAP"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMAT"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMBA"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMBI"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AMBR"
                    exchange "NYSE"
                }
                {
                    symbol "AMCC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMCF"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMCS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMCVQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMD"
                    exchange "NASDAQ"
                }
                {
                    symbol "AME"
                    exchange "NYSE"
                }
                {
                    symbol "AMEP"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMFW"
                    exchange "NYSE"
                }
                {
                    symbol "AMID1"
                    exchange "NYSE"
                }
                {
                    symbol "AMIEQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMIIQ"
                    exchange "NYSE"
                }
                {
                    symbol "AMIS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMK1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AMKR"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMLJ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMNI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMNUQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMP1"
                    exchange "NYSE"
                }
                {
                    symbol "AMPG"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMPI"
                    exchange "NYSE"
                }
                {
                    symbol "AMPL"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMPX"
                    exchange "NYSE"
                }
                {
                    symbol "AMPXQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMPY"
                    exchange "NYSE"
                }
                {
                    symbol "AMRC"
                    exchange "NYSE"
                }
                {
                    symbol "AMRQQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMSC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMSI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMSI1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMST"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMTM"
                    exchange "NYSE"
                }
                {
                    symbol "AMTX"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMVC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AMXC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AN1"
                    exchange "NYSE"
                }
                {
                    symbol "ANAC"
                    exchange "NYSE"
                }
                {
                    symbol "ANAD"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANCCQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANCJQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANCR"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANDA1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANDA2"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANDN1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANDR"
                    exchange "NYSEMKT"
                }
                {
                    symbol "ANDV"
                    exchange "NYSE"
                }
                {
                    symbol "ANDW"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANDX"
                    exchange "NYSE"
                }
                {
                    symbol "ANEN"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANET"
                    exchange "NYSE"
                }
                {
                    symbol "ANET2"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANI"
                    exchange "NYSEMKT"
                }
                {
                    symbol "ANIC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANLG"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANLY"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANMP"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANS"
                    exchange "NYSEMKT"
                }
                {
                    symbol "ANSC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANSS"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANST"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANSW"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANT"
                    exchange "NYSE"
                }
                {
                    symbol "ANTP"
                    exchange "NASDAQ"
                }
                {
                    symbol "ANV1"
                    exchange "NYSE"
                }
                {
                    symbol "ANWWQ"
                    exchange "NYSE"
                }
                {
                    symbol "ANY"
                    exchange "NASDAQ"
                }
                {
                    symbol "AOGO"
                    exchange "NASDAQ"
                }
                {
                    symbol "AOGSQ"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AOL"
                    exchange "NYSE"
                }
                {
                    symbol "AONEQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AORGB"
                    exchange "NASDAQ"
                }
                {
                    symbol "AOS"
                    exchange "NYSE"
                }
                {
                    symbol "AOSL"
                    exchange "NASDAQ"
                }
                {
                    symbol "AOUT"
                    exchange "NASDAQ"
                }
                {
                    symbol "AP"
                    exchange "NYSE"
                }
                {
                    symbol "APA"
                    exchange "NASDAQ"
                }
                {
                    symbol "APAC1"
                    exchange "NASDAQ"
                }
                {
                    symbol "APAGF"
                    exchange "NASDAQ"
                }
                {
                    symbol "APC"
                    exchange "NYSE"
                }
                {
                    symbol "APCA"
                    exchange "NYSE"
                }
                {
                    symbol "APCC"
                    exchange "NASDAQ"
                }
                {
                    symbol "APCX"
                    exchange "NASDAQ"
                }
                {
                    symbol "APEX1"
                    exchange "NASDAQ"
                }
                {
                    symbol "APG"
                    exchange "NYSE"
                }
                {
                    symbol "APGB"
                    exchange "NYSE"
                }
                {
                    symbol "APH"
                    exchange "NYSE"
                }
                {
                    symbol "API"
                    exchange "NASDAQ"
                }
                {
                    symbol "API1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "APIC"
                    exchange "NASDAQ"
                }
                {
                    symbol "APKT"
                    exchange "NASDAQ"
                }
                {
                    symbol "APL"
                    exchange "NYSE"
                }
                {
                    symbol "APLP"
                    exchange "NASDAQ"
                }
                {
                    symbol "APLX"
                    exchange "NASDAQ"
                }
                {
                    symbol "APM1"
                    exchange "NYSE"
                }
                {
                    symbol "APMC"
                    exchange "NASDAQ"
                }
                {
                    symbol "APMI"
                    exchange "NASDAQ"
                }
                {
                    symbol "APNC"
                    exchange "NYSE"
                }
                {
                    symbol "APNI"
                    exchange "NYSE"
                }
                {
                    symbol "APNT1"
                    exchange "NASDAQ"
                }
                {
                    symbol "APP"
                    exchange "NASDAQ"
                }
                {
                    symbol "APPCQ"
                    exchange "NYSEMKT"
                }
                {
                    symbol "APPF"
                    exchange "NASDAQ"
                }
                {
                    symbol "APPN"
                    exchange "NASDAQ"
                }
                {
                    symbol "APPS"
                    exchange "NASDAQ"
                }
                {
                    symbol "APPS1"
                    exchange "NASDAQ"
                }
                {
                    symbol "APQCF"
                    exchange "NASDAQ"
                }
                {
                    symbol "APR1"
                    exchange "NYSE"
                }
                {
                    symbol "APRS"
                    exchange "NASDAQ"
                }
                {
                    symbol "APSG1"
                    exchange "NASDAQ"
                }
                {
                    symbol "APTI"
                    exchange "NASDAQ"
                }
                {
                    symbol "APTI1"
                    exchange "NASDAQ"
                }
                {
                    symbol "APTM1"
                    exchange "NASDAQ"
                }
                {
                    symbol "APW"
                    exchange "NYSE"
                }
                {
                    symbol "APWC"
                    exchange "NASDAQ"
                }
                {
                    symbol "APWR1"
                    exchange "NASDAQ"
                }
                {
                    symbol "APWRQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "APXI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AQ"
                    exchange "NYSE"
                }
                {
                    symbol "AQ1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AQCR"
                    exchange "NASDAQ"
                }
                {
                    symbol "AQMS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AQNT"
                    exchange "NASDAQ"
                }
                {
                    symbol "AQP"
                    exchange "NYSE"
                }
                {
                    symbol "AQU"
                    exchange "NASDAQ"
                }
                {
                    symbol "AQUA"
                    exchange "NYSE"
                }
                {
                    symbol "AR"
                    exchange "NYSE"
                }
                {
                    symbol "ARB1"
                    exchange "NYSE"
                }
                {
                    symbol "ARBA"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARBB"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARBE"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARBG"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARBX"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARC"
                    exchange "NYSE"
                }
                {
                    symbol "ARC1"
                    exchange "NYSE"
                }
                {
                    symbol "ARCB"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARCK"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARCW"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARCX"
                    exchange "NYSE"
                }
                {
                    symbol "ARD1"
                    exchange "NYSE"
                }
                {
                    symbol "ARDI"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARDT1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AREM1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AREXQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARG"
                    exchange "NYSE"
                }
                {
                    symbol "ARGU"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARII"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARLCF"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARM"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARMH"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARMK"
                    exchange "NYSE"
                }
                {
                    symbol "ARNC"
                    exchange "NYSE"
                }
                {
                    symbol "AROC"
                    exchange "NYSE"
                }
                {
                    symbol "ARPJQ"
                    exchange "NYSE"
                }
                {
                    symbol "ARQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARQQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARRS"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARRY"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARS1"
                    exchange "NYSE"
                }
                {
                    symbol "ARST"
                    exchange "NASDAQ"
                }
                {
                    symbol "ART1"
                    exchange "NYSE"
                }
                {
                    symbol "ARTE"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARTE1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARTG"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARTI1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARTW"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARTX"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARUN"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARVX"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARW"
                    exchange "NYSE"
                }
                {
                    symbol "ARWA"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARX"
                    exchange "NYSE"
                }
                {
                    symbol "ARXX"
                    exchange "NASDAQ"
                }
                {
                    symbol "ARYE"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASAI1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASAL"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASAM1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASAN"
                    exchange "NYSE"
                }
                {
                    symbol "ASAPQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASAQ"
                    exchange "NYSE"
                }
                {
                    symbol "ASAX"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASC"
                    exchange "NYSE"
                }
                {
                    symbol "ASCBF"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASCL"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASCMA"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASCX"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASDG"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASDS"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASDV"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASEC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASGN"
                    exchange "NYSE"
                }
                {
                    symbol "ASHE"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASIA1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASIGF1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASIS"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASKJ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASLE"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASMIY"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASML"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASND1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASNS"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASPIY"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASPT"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASPXQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASR"
                    exchange "NYSE"
                }
                {
                    symbol "ASTC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASTE"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASTI"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASTR"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASTS"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASTTY"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASTX1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASUR"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASV"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASVI"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASW1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "ASWX"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASX"
                    exchange "NYSE"
                }
                {
                    symbol "ASYS"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASYTQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ASZ"
                    exchange "NYSE"
                }
                {
                    symbol "ATA"
                    exchange "NYSE"
                }
                {
                    symbol "ATAC1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATAHQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATAQ"
                    exchange "NYSE"
                }
                {
                    symbol "ATAR1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATB"
                    exchange "NYSE"
                }
                {
                    symbol "ATC"
                    exchange "NYSE"
                }
                {
                    symbol "ATCH"
                    exchange "NYSEMKT"
                }
                {
                    symbol "ATCH1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATCM"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATCX"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATEA"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATEK"
                    exchange "NYSEMKT"
                }
                {
                    symbol "ATEL"
                    exchange "NYSEMKT"
                }
                {
                    symbol "ATEN"
                    exchange "NYSE"
                }
                {
                    symbol "ATEYY"
                    exchange "NYSE"
                }
                {
                    symbol "ATGCQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATGL"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATGN"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATHL"
                    exchange "NYSE"
                }
                {
                    symbol "ATHR"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATHYQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATI"
                    exchange "NYSE"
                }
                {
                    symbol "ATIS"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATKR"
                    exchange "NYSE"
                }
                {
                    symbol "ATLPA"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATLS"
                    exchange "NYSE"
                }
                {
                    symbol "ATLS1"
                    exchange "NYSE"
                }
                {
                    symbol "ATLS2"
                    exchange "NYSE"
                }
                {
                    symbol "ATMC"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATML"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATMU"
                    exchange "NYSE"
                }
                {
                    symbol "ATMV"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATN"
                    exchange "NYSE"
                }
                {
                    symbol "ATN1"
                    exchange "NYSE"
                }
                {
                    symbol "ATNY"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATOM"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATON"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATPAQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATPL"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATRO"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATRS1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATS"
                    exchange "NYSE"
                }
                {
                    symbol "ATSC1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "ATSG"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATSN"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATTOF"
                    exchange "NYSE"
                }
                {
                    symbol "ATTU"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATTY"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATW"
                    exchange "NYSE"
                }
                {
                    symbol "ATX"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATXG"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATXI1"
                    exchange "NASDAQ"
                }
                {
                    symbol "ATYT"
                    exchange "NASDAQ"
                }
                {
                    symbol "AUDC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AUGS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AUGT1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AUID"
                    exchange "NASDAQ"
                }
                {
                    symbol "AULT1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AUOTY"
                    exchange "NYSE"
                }
                {
                    symbol "AUR"
                    exchange "NASDAQ"
                }
                {
                    symbol "AURAQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AUS"
                    exchange "NYSE"
                }
                {
                    symbol "AUSA"
                    exchange "NASDAQ"
                }
                {
                    symbol "AUSPF"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AUTH"
                    exchange "NASDAQ"
                }
                {
                    symbol "AUTNY"
                    exchange "NASDAQ"
                }
                {
                    symbol "AUTO1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AUUD"
                    exchange "NASDAQ"
                }
                {
                    symbol "AUZR"
                    exchange "NASDAQ"
                }
                {
                    symbol "AV1"
                    exchange "NYSE"
                }
                {
                    symbol "AVAN"
                    exchange "NYSE"
                }
                {
                    symbol "AVAV"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVC"
                    exchange "NYSE"
                }
                {
                    symbol "AVCT1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVCTQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVDS1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVDX"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVGE1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVGO"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVGO1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVGTF"
                    exchange "NYSE"
                }
                {
                    symbol "AVHI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVHOQ"
                    exchange "NYSE"
                }
                {
                    symbol "AVI"
                    exchange "NYSE"
                }
                {
                    symbol "AVID"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVL1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AVLR"
                    exchange "NYSE"
                }
                {
                    symbol "AVMC1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVNT1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVNW"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVNX"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVOL"
                    exchange "NYSE"
                }
                {
                    symbol "AVPT"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVSR"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVT"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVTMQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AVV"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AVX"
                    exchange "NYSE"
                }
                {
                    symbol "AVYAQ"
                    exchange "NYSE"
                }
                {
                    symbol "AVZAQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AW"
                    exchange "NYSE"
                }
                {
                    symbol "AWA"
                    exchange "NYSE"
                }
                {
                    symbol "AWAY1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AWIN"
                    exchange "NASDAQ"
                }
                {
                    symbol "AWRE"
                    exchange "NASDAQ"
                }
                {
                    symbol "AWX"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AXAC"
                    exchange "NYSE"
                }
                {
                    symbol "AXAR"
                    exchange "NASDAQ"
                }
                {
                    symbol "AXAS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AXE"
                    exchange "NYSE"
                }
                {
                    symbol "AXHI"
                    exchange "NYSE"
                }
                {
                    symbol "AXHM"
                    exchange "NASDAQ"
                }
                {
                    symbol "AXIL"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AXNT"
                    exchange "NASDAQ"
                }
                {
                    symbol "AXON"
                    exchange "NASDAQ"
                }
                {
                    symbol "AXPWQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AXSI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AXSO"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AXST"
                    exchange "NASDAQ"
                }
                {
                    symbol "AXTC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AXTI"
                    exchange "NASDAQ"
                }
                {
                    symbol "AXYS"
                    exchange "NASDAQ"
                }
                {
                    symbol "AYD"
                    exchange "NYSE"
                }
                {
                    symbol "AYI"
                    exchange "NYSE"
                }
                {
                    symbol "AYR"
                    exchange "NYSE"
                }
                {
                    symbol "AYS"
                    exchange "NYSEMKT"
                }
                {
                    symbol "AYX"
                    exchange "NYSE"
                }
                {
                    symbol "AZ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AZIC"
                    exchange "NASDAQ"
                }
                {
                    symbol "AZPN"
                    exchange "NASDAQ"
                }
                {
                    symbol "AZPN1"
                    exchange "NASDAQ"
                }
                {
                    symbol "AZUL"
                    exchange "NYSE"
                }
                {
                    symbol "AZURQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "AZZ"
                    exchange "NYSE"
                }
                {
                    symbol "B"
                    exchange "NYSE"
                }
                {
                    symbol "BA"
                    exchange "NYSE"
                }
                {
                    symbol "BAANF"
                    exchange "NASDAQ"
                }
                {
                    symbol "BACA"
                    exchange "NYSE"
                }
                {
                    symbol "BAER"
                    exchange "NASDAQ"
                }
                {
                    symbol "BAH"
                    exchange "NYSE"
                }
                {
                    symbol "BALT2"
                    exchange "NYSE"
                }
                {
                    symbol "BAND"
                    exchange "NASDAQ"
                }
                {
                    symbol "BANL"
                    exchange "NASDAQ"
                }
                {
                    symbol "BAR1"
                    exchange "NYSE"
                }
                {
                    symbol "BASE"
                    exchange "NASDAQ"
                }
                {
                    symbol "BASEA"
                    exchange "NASDAQ"
                }
                {
                    symbol "BASXQ"
                    exchange "NYSE"
                }
                {
                    symbol "BATL"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BATT1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BAY1"
                    exchange "NYSE"
                }
                {
                    symbol "BAYA"
                    exchange "NASDAQ"
                }
                {
                    symbol "BB"
                    exchange "NYSE"
                }
                {
                    symbol "BBAI"
                    exchange "NYSE"
                }
                {
                    symbol "BBBB"
                    exchange "NASDAQ"
                }
                {
                    symbol "BBCP"
                    exchange "NASDAQ"
                }
                {
                    symbol "BBEPQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BBG"
                    exchange "NYSE"
                }
                {
                    symbol "BBLKF"
                    exchange "NYSE"
                }
                {
                    symbol "BBLUQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BBND"
                    exchange "NASDAQ"
                }
                {
                    symbol "BBOX"
                    exchange "NASDAQ"
                }
                {
                    symbol "BBRC1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BBSI"
                    exchange "NASDAQ"
                }
                {
                    symbol "BBSW"
                    exchange "NASDAQ"
                }
                {
                    symbol "BBU"
                    exchange "NYSE"
                }
                {
                    symbol "BCAN"
                    exchange "NASDAQ"
                }
                {
                    symbol "BCAS"
                    exchange "NASDAQ"
                }
                {
                    symbol "BCDS1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BCO"
                    exchange "NYSE"
                }
                {
                    symbol "BCOV"
                    exchange "NASDAQ"
                }
                {
                    symbol "BCSA"
                    exchange "NASDAQ"
                }
                {
                    symbol "BCSI"
                    exchange "NASDAQ"
                }
                {
                    symbol "BCST"
                    exchange "NASDAQ"
                }
                {
                    symbol "BCTI"
                    exchange "NASDAQ"
                }
                {
                    symbol "BDC"
                    exchange "NYSE"
                }
                {
                    symbol "BDCO"
                    exchange "NASDAQ"
                }
                {
                    symbol "BDE1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BDGPA"
                    exchange "NYSE"
                }
                {
                    symbol "BDI"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BDK"
                    exchange "NASDAQ"
                }
                {
                    symbol "BDLN"
                    exchange "NASDAQ"
                }
                {
                    symbol "BDLSQ"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BDMI"
                    exchange "NASDAQ"
                }
                {
                    symbol "BDRL"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BE"
                    exchange "NYSE"
                }
                {
                    symbol "BEAS"
                    exchange "NASDAQ"
                }
                {
                    symbol "BECN"
                    exchange "NASDAQ"
                }
                {
                    symbol "BEEM"
                    exchange "NASDAQ"
                }
                {
                    symbol "BEEP"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BEI1"
                    exchange "NYSE"
                }
                {
                    symbol "BEIQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BELFA"
                    exchange "NASDAQ"
                }
                {
                    symbol "BELM"
                    exchange "NASDAQ"
                }
                {
                    symbol "BENE"
                    exchange "NASDAQ"
                }
                {
                    symbol "BEOSZ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BEST"
                    exchange "NYSE"
                }
                {
                    symbol "BEST1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BET"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BEXP"
                    exchange "NASDAQ"
                }
                {
                    symbol "BEZ"
                    exchange "NYSE"
                }
                {
                    symbol "BFAC"
                    exchange "NYSE"
                }
                {
                    symbol "BFI1"
                    exchange "NYSE"
                }
                {
                    symbol "BFRE1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BFUN"
                    exchange "NASDAQ"
                }
                {
                    symbol "BFX1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BGC2"
                    exchange "NYSE"
                }
                {
                    symbol "BGF"
                    exchange "NYSE"
                }
                {
                    symbol "BGGSQ"
                    exchange "NYSE"
                }
                {
                    symbol "BGH1"
                    exchange "NYSE"
                }
                {
                    symbol "BGPTQ"
                    exchange "NYSE"
                }
                {
                    symbol "BGRH"
                    exchange "NASDAQ"
                }
                {
                    symbol "BGRY"
                    exchange "NASDAQ"
                }
                {
                    symbol "BGSF"
                    exchange "NYSE"
                }
                {
                    symbol "BGSX"
                    exchange "NYSE"
                }
                {
                    symbol "BHAC"
                    exchange "NASDAQ"
                }
                {
                    symbol "BHAC1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BHAG"
                    exchange "NASDAQ"
                }
                {
                    symbol "BHE"
                    exchange "NYSE"
                }
                {
                    symbol "BHI"
                    exchange "NYSE"
                }
                {
                    symbol "BHODQ"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BIDZ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BIGC"
                    exchange "NASDAQ"
                }
                {
                    symbol "BILL"
                    exchange "NYSE"
                }
                {
                    symbol "BIOS"
                    exchange "NASDAQ"
                }
                {
                    symbol "BIOT"
                    exchange "NASDAQ"
                }
                {
                    symbol "BIRT"
                    exchange "NASDAQ"
                }
                {
                    symbol "BISA"
                    exchange "NASDAQ"
                }
                {
                    symbol "BITS1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BIZZ1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BJS"
                    exchange "NYSE"
                }
                {
                    symbol "BKEP"
                    exchange "NASDAQ"
                }
                {
                    symbol "BKHA"
                    exchange "NASDAQ"
                }
                {
                    symbol "BKI"
                    exchange "NYSE"
                }
                {
                    symbol "BKKT"
                    exchange "NYSE"
                }
                {
                    symbol "BKNG"
                    exchange "NASDAQ"
                }
                {
                    symbol "BKR"
                    exchange "NASDAQ"
                }
                {
                    symbol "BKSY"
                    exchange "NYSE"
                }
                {
                    symbol "BKTI"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BKV"
                    exchange "NYSE"
                }
                {
                    symbol "BKYI"
                    exchange "NASDAQ"
                }
                {
                    symbol "BL"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLAC"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLBX"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLD"
                    exchange "NYSE"
                }
                {
                    symbol "BLD1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BLDE"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLDP"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLEU"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLIN"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLKB"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLND"
                    exchange "NYSE"
                }
                {
                    symbol "BLNG"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLNK"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLOG"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLOX"
                    exchange "NYSE"
                }
                {
                    symbol "BLPG1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLSA"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLSW1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLT"
                    exchange "NYSE"
                }
                {
                    symbol "BLTS"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLUAF"
                    exchange "NYSE"
                }
                {
                    symbol "BLUE1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLVD"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLZE"
                    exchange "NASDAQ"
                }
                {
                    symbol "BLZE1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BMAC"
                    exchange "NYSE"
                }
                {
                    symbol "BMAN"
                    exchange "NASDAQ"
                }
                {
                    symbol "BMAQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BMBL"
                    exchange "NASDAQ"
                }
                {
                    symbol "BMC"
                    exchange "NASDAQ"
                }
                {
                    symbol "BMI"
                    exchange "NYSE"
                }
                {
                    symbol "BMR"
                    exchange "NASDAQ"
                }
                {
                    symbol "BMRQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BMTM"
                    exchange "NASDAQ"
                }
                {
                    symbol "BMTX"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BN1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BNAI"
                    exchange "NASDAQ"
                }
                {
                    symbol "BNE1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BNFT"
                    exchange "NASDAQ"
                }
                {
                    symbol "BNI"
                    exchange "NASDAQ"
                }
                {
                    symbol "BNIX"
                    exchange "NASDAQ"
                }
                {
                    symbol "BNNR"
                    exchange "NASDAQ"
                }
                {
                    symbol "BNSOF"
                    exchange "NASDAQ"
                }
                {
                    symbol "BNZI"
                    exchange "NASDAQ"
                }
                {
                    symbol "BOAC"
                    exchange "NYSE"
                }
                {
                    symbol "BOBJY"
                    exchange "NASDAQ"
                }
                {
                    symbol "BOCN"
                    exchange "NASDAQ"
                }
                {
                    symbol "BOG"
                    exchange "NYSE"
                }
                {
                    symbol "BOLDQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BOLT1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BOOL"
                    exchange "NASDAQ"
                }
                {
                    symbol "BOOM"
                    exchange "NASDAQ"
                }
                {
                    symbol "BOP"
                    exchange "NYSE"
                }
                {
                    symbol "BOR"
                    exchange "NYSE"
                }
                {
                    symbol "BORL"
                    exchange "NASDAQ"
                }
                {
                    symbol "BORR"
                    exchange "NYSE"
                }
                {
                    symbol "BOSA"
                    exchange "NASDAQ"
                }
                {
                    symbol "BOSC"
                    exchange "NASDAQ"
                }
                {
                    symbol "BOWN"
                    exchange "NASDAQ"
                }
                {
                    symbol "BOX"
                    exchange "NYSE"
                }
                {
                    symbol "BOX1"
                    exchange "NYSE"
                }
                {
                    symbol "BOXL"
                    exchange "NASDAQ"
                }
                {
                    symbol "BOYD1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BP"
                    exchange "NYSE"
                }
                {
                    symbol "BPAC"
                    exchange "NASDAQ"
                }
                {
                    symbol "BPAO"
                    exchange "NASDAQ"
                }
                {
                    symbol "BPI.A"
                    exchange "NYSE"
                }
                {
                    symbol "BPIGF"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BPL"
                    exchange "NYSE"
                }
                {
                    symbol "BPMP"
                    exchange "NYSE"
                }
                {
                    symbol "BPOM"
                    exchange "NASDAQ"
                }
                {
                    symbol "BPT"
                    exchange "NYSE"
                }
                {
                    symbol "BPTM"
                    exchange "NASDAQ"
                }
                {
                    symbol "BPTR"
                    exchange "NASDAQ"
                }
                {
                    symbol "BPZRQ"
                    exchange "NYSE"
                }
                {
                    symbol "BR"
                    exchange "NYSE"
                }
                {
                    symbol "BR1"
                    exchange "NYSE"
                }
                {
                    symbol "BRAC"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRANF"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRC"
                    exchange "NYSE"
                }
                {
                    symbol "BRCD"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRCM"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRD"
                    exchange "NYSE"
                }
                {
                    symbol "BRDG1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRDR"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRDSQ"
                    exchange "NYSE"
                }
                {
                    symbol "BREK"
                    exchange "NASDAQ"
                }
                {
                    symbol "BREZ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRIO"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRIV"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRKC1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRKH"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRKT"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRLCQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRLS1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRN"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BRNC"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRNC1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BROD1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BROG"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRQSF"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRR"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BRR1"
                    exchange "NYSE"
                }
                {
                    symbol "BRSS"
                    exchange "NYSE"
                }
                {
                    symbol "BRST1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRSWQ"
                    exchange "NYSE"
                }
                {
                    symbol "BRY"
                    exchange "NASDAQ"
                }
                {
                    symbol "BRY1"
                    exchange "NYSE"
                }
                {
                    symbol "BRZE"
                    exchange "NASDAQ"
                }
                {
                    symbol "BSFT"
                    exchange "NASDAQ"
                }
                {
                    symbol "BSIIU"
                    exchange "NASDAQ"
                }
                {
                    symbol "BSKY"
                    exchange "NASDAQ"
                }
                {
                    symbol "BSM"
                    exchange "NYSE"
                }
                {
                    symbol "BSNX"
                    exchange "NASDAQ"
                }
                {
                    symbol "BSQR"
                    exchange "NASDAQ"
                }
                {
                    symbol "BSTW"
                    exchange "NASDAQ"
                }
                {
                    symbol "BSY"
                    exchange "NASDAQ"
                }
                {
                    symbol "BTAQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BTC1"
                    exchange "NYSE"
                }
                {
                    symbol "BTCM"
                    exchange "NYSE"
                }
                {
                    symbol "BTDR"
                    exchange "NASDAQ"
                }
                {
                    symbol "BTE"
                    exchange "NYSE"
                }
                {
                    symbol "BTF1"
                    exchange "NYSE"
                }
                {
                    symbol "BTGI"
                    exchange "NASDAQ"
                }
                {
                    symbol "BTGL"
                    exchange "NASDAQ"
                }
                {
                    symbol "BTH"
                    exchange "NYSE"
                }
                {
                    symbol "BTHS"
                    exchange "NASDAQ"
                }
                {
                    symbol "BTIC"
                    exchange "NASDAQ"
                }
                {
                    symbol "BTOC"
                    exchange "NASDAQ"
                }
                {
                    symbol "BTRS"
                    exchange "NASDAQ"
                }
                {
                    symbol "BTSR"
                    exchange "NASDAQ"
                }
                {
                    symbol "BTUI"
                    exchange "NASDAQ"
                }
                {
                    symbol "BUCY"
                    exchange "NASDAQ"
                }
                {
                    symbol "BUJA"
                    exchange "NASDAQ"
                }
                {
                    symbol "BURU"
                    exchange "NYSEMKT"
                }
                {
                    symbol "BUSY"
                    exchange "NASDAQ"
                }
                {
                    symbol "BUTLQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BV"
                    exchange "NYSE"
                }
                {
                    symbol "BV1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BVEW"
                    exchange "NASDAQ"
                }
                {
                    symbol "BVSI"
                    exchange "NASDAQ"
                }
                {
                    symbol "BVSN"
                    exchange "NASDAQ"
                }
                {
                    symbol "BW"
                    exchange "NYSE"
                }
                {
                    symbol "BWAC"
                    exchange "NASDAQ"
                }
                {
                    symbol "BWAY1"
                    exchange "NASDAQ"
                }
                {
                    symbol "BWC"
                    exchange "NASDAQ"
                }
                {
                    symbol "BWC1"
                    exchange "NYSE"
                }
                {
                    symbol "BWEBF"
                    exchange "NASDAQ"
                }
                {
                    symbol "BWEN"
                    exchange "NASDAQ"
                }
                {
                    symbol "BWLP"
                    exchange "NYSE"
                }
                {
                    symbol "BWMN"
                    exchange "NASDAQ"
                }
                {
                    symbol "BWOWF"
                    exchange "NASDAQ"
                }
                {
                    symbol "BWP"
                    exchange "NYSE"
                }
                {
                    symbol "BWSI"
                    exchange "NASDAQ"
                }
                {
                    symbol "BWXT"
                    exchange "NYSE"
                }
                {
                    symbol "BXC"
                    exchange "NYSE"
                }
                {
                    symbol "BXEFF"
                    exchange "NYSE"
                }
                {
                    symbol "BYI"
                    exchange "NYSE"
                }
                {
                    symbol "BYNDQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BYNO"
                    exchange "NASDAQ"
                }
                {
                    symbol "BYRN"
                    exchange "NASDAQ"
                }
                {
                    symbol "BZ"
                    exchange "NASDAQ"
                }
                {
                    symbol "BZC"
                    exchange "NYSEMKT"
                }
                {
                    symbol "CA1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAAP"
                    exchange "NYSE"
                }
                {
                    symbol "CAB1"
                    exchange "NYSE"
                }
                {
                    symbol "CACGU"
                    exchange "NASDAQ"
                }
                {
                    symbol "CACI"
                    exchange "NYSE"
                }
                {
                    symbol "CACS"
                    exchange "NASDAQ"
                }
                {
                    symbol "CADA"
                    exchange "NASDAQ"
                }
                {
                    symbol "CADE2"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAE"
                    exchange "NYSE"
                }
                {
                    symbol "CAER"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAI"
                    exchange "NYSE"
                }
                {
                    symbol "CAII"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAIR"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAIS"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAJPY"
                    exchange "NYSE"
                }
                {
                    symbol "CAL1"
                    exchange "NYSE"
                }
                {
                    symbol "CALAQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "CALD"
                    exchange "NASDAQ"
                }
                {
                    symbol "CALX"
                    exchange "NYSE"
                }
                {
                    symbol "CAM"
                    exchange "NYSE"
                }
                {
                    symbol "CAM1"
                    exchange "NYSE"
                }
                {
                    symbol "CAMB"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAMBA"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAMD"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAMPQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAMT"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAMZ"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAN"
                    exchange "NASDAQ"
                }
                {
                    symbol "CANI"
                    exchange "NASDAQ"
                }
                {
                    symbol "CANOQ1"
                    exchange "NYSEMKT"
                }
                {
                    symbol "CANR1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CANRQ"
                    exchange "NYSEMKT"
                }
                {
                    symbol "CAPA1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAPI"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAPL"
                    exchange "NYSE"
                }
                {
                    symbol "CAPNU"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAPT"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAR"
                    exchange "NASDAQ"
                }
                {
                    symbol "CARB"
                    exchange "NASDAQ"
                }
                {
                    symbol "CARD1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CARE1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CARI"
                    exchange "NASDAQ"
                }
                {
                    symbol "CARL1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAS"
                    exchange "NYSE"
                }
                {
                    symbol "CASC1"
                    exchange "NYSE"
                }
                {
                    symbol "CASS"
                    exchange "NASDAQ"
                }
                {
                    symbol "CASSQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAST1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAT"
                    exchange "NYSE"
                }
                {
                    symbol "CATM"
                    exchange "NASDAQ"
                }
                {
                    symbol "CATP"
                    exchange "NASDAQ"
                }
                {
                    symbol "CATS1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CATT"
                    exchange "NASDAQ"
                }
                {
                    symbol "CATX1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CATZ"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAUD"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAVM"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAVN"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAVO"
                    exchange "NASDAQ"
                }
                {
                    symbol "CAYN"
                    exchange "NASDAQ"
                }
                {
                    symbol "CBAT"
                    exchange "NASDAQ"
                }
                {
                    symbol "CBE"
                    exchange "NYSE"
                }
                {
                    symbol "CBEH"
                    exchange "NASDAQ"
                }
                {
                    symbol "CBI"
                    exchange "NYSE"
                }
                {
                    symbol "CBIS1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CBLK"
                    exchange "NASDAQ"
                }
                {
                    symbol "CBLT"
                    exchange "NASDAQ"
                }
                {
                    symbol "CBNRQ"
                    exchange "NYSEMKT"
                }
                {
                    symbol "CBRG"
                    exchange "NASDAQ"
                }
                {
                    symbol "CBRI"
                    exchange "NYSE"
                }
                {
                    symbol "CBXC"
                    exchange "NASDAQ"
                }
                {
                    symbol "CBZ"
                    exchange "NYSE"
                }
                {
                    symbol "CBZ2"
                    exchange "NYSE"
                }
                {
                    symbol "CCA1"
                    exchange "NYSE"
                }
                {
                    symbol "CCAI"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCAR"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCBL"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCCS"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCEC"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCGM"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCIX"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCIX2"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCL"
                    exchange "NYSE"
                }
                {
                    symbol "CCLN"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCLP"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCMP"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCMTF"
                    exchange "NYSEMKT"
                }
                {
                    symbol "CCN"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCRC"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCRD"
                    exchange "NYSE"
                }
                {
                    symbol "CCRD1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCSC1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCSI"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCTG"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCTS"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCTX"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCUR"
                    exchange "NASDAQ"
                }
                {
                    symbol "CCV"
                    exchange "NYSE"
                }
                {
                    symbol "CCVI"
                    exchange "NYSE"
                }
                {
                    symbol "CD"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDAQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDCAQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDCM"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDCO1"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDCSY"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDCY"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDD"
                    exchange "NYSE"
                }
                {
                    symbol "CDDDQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDDT"
                    exchange "NYSEMKT"
                }
                {
                    symbol "CDG"
                    exchange "NYSE"
                }
                {
                    symbol "CDI"
                    exchange "NYSE"
                }
                {
                    symbol "CDIIQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDK"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDLR"
                    exchange "NYSE"
                }
                {
                    symbol "CDMS"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDNS"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDOT"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDRBQ"
                    exchange "NASDAQ"
                }
                {
                    symbol "CDRE"
                    exchange "NYSE"
                }
                {
                    symbol "CDS2"
                    exchange "NYSEMKT"
                }
                {
                    symbol "CDSC"
                    exchange "NASDAQ"
                }
            ]
        }
    }
}
