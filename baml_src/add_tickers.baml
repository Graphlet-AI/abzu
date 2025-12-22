class TickerList {
  tickers Ticker[]
}

function AddTickersToCompanies(company_list: CompanyList, ticker_list: TickerList) -> CompanyList {
  // see clients.baml
  client Gemini20Flash

  // The prompt uses Jinja syntax. Change the models or this text and watch the prompt preview change!
  prompt #"
    Examine the following sets of companies and tickers and match the tickers with the companies based on their names representing the same entity. Merge the matched records, adding a Ticker to each Company that matches. If the company name in the ticker differs from the company name, use the full corporate name. Include the name of the exchange from the ticker record.

    Return a set of companies with tickers merged into the ticker field. Return the original company if no matching ticker is found.

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
                    source_ids null
                    source_uuids null
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
                    source_ids null
                    source_uuids null
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
                    source_ids null
                    source_uuids null
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
                    source_ids null
                    source_uuids null
                }
            ]
        }
        ticker_list {
            tickers [
                {
                    id 5
                    symbol "AMD"
                    exchange "UQ"
                }
                {
                    id 6
                    symbol "AAC"
                    exchange "UN"
                }
                {
                    id 7
                    symbol "AACI"
                    exchange "UQ"
                }
                {
                    id 8
                    symbol "AACPF"
                    exchange "UQ"
                }
                {
                    id 9
                    symbol "AACT"
                    exchange "UN"
                }
                {
                    id 10
                    symbol "AAI"
                    exchange "UQ"
                }
                {
                    id 11
                    symbol "AAI1"
                    exchange "UN"
                }
                {
                    id 12
                    symbol "AAIIQ"
                    exchange "UQ"
                }
                {
                    id 13
                    symbol "AAL"
                    exchange "UQ"
                }
                {
                    id 14
                    symbol "AAM"
                    exchange "UN"
                }
                {
                    id 15
                    symbol "AAMRQ"
                    exchange "UN"
                }
                {
                    id 16
                    symbol "AAN"
                    exchange "UN"
                }
                {
                    id 17
                    symbol "AAOI"
                    exchange "UQ"
                }
                {
                    id 18
                    symbol "AAPL"
                    exchange "UQ"
                }
                {
                    id 19
                    symbol "AAQC"
                    exchange "UN"
                }
                {
                    id 20
                    symbol "AATC"
                    exchange "UQ"
                }
                {
                    id 21
                    symbol "AATI"
                    exchange "UQ"
                }
                {
                    id 22
                    symbol "AATI1"
                    exchange "UQ"
                }
                {
                    id 23
                    symbol "AATT"
                    exchange "UQ"
                }
                {
                    id 24
                    symbol "AAVVF"
                    exchange "UN"
                }
                {
                    id 25
                    symbol "AAWHQ"
                    exchange "UQ"
                }
                {
                    id 26
                    symbol "AAWW"
                    exchange "UQ"
                }
                {
                    id 27
                    symbol "ABACQ"
                    exchange "UQ"
                }
                {
                    id 28
                    symbol "ABAT1"
                    exchange "UQ"
                }
                {
                    id 29
                    symbol "ABBNY"
                    exchange "UN"
                }
                {
                    id 30
                    symbol "ABCC"
                    exchange "UQ"
                }
                {
                    id 31
                    symbol "ABDR1"
                    exchange "UQ"
                }
                {
                    id 32
                    symbol "ABF"
                    exchange "UN"
                }
                {
                    id 33
                    symbol "ABGBY"
                    exchange "UQ"
                }
                {
                    id 34
                    symbol "ABGI"
                    exchange "UQ"
                }
                {
                    id 35
                    symbol "ABHH"
                    exchange "UN"
                }
                {
                    id 36
                    symbol "ABILF"
                    exchange "UQ"
                }
                {
                    id 37
                    symbol "ABIX"
                    exchange "UQ"
                }
                {
                    id 38
                    symbol "ABM"
                    exchange "UN"
                }
                {
                    id 39
                    symbol "ABNB"
                    exchange "UQ"
                }
                {
                    id 40
                    symbol "ABNTQ"
                    exchange "UN"
                }
                {
                    id 41
                    symbol "ABOV"
                    exchange "UQ"
                }
                {
                    id 42
                    symbol "ABRX1"
                    exchange "UQ"
                }
                {
                    id 43
                    symbol "ABST"
                    exchange "UQ"
                }
                {
                    id 44
                    symbol "ABTE"
                    exchange "UQ"
                }
                {
                    id 45
                    symbol "ACA"
                    exchange "UN"
                }
                {
                    id 46
                    symbol "ACAB"
                    exchange "UQ"
                }
                {
                    id 47
                    symbol "ACAC"
                    exchange "UQ"
                }
                {
                    id 48
                    symbol "ACAH"
                    exchange "UQ"
                }
                {
                    id 49
                    symbol "ACAQ"
                    exchange "UN"
                }
                {
                    id 50
                    symbol "ACAT"
                    exchange "UQ"
                }
                {
                    id 51
                    symbol "ACBA"
                    exchange "UQ"
                }
                {
                    id 52
                    symbol "ACCD1"
                    exchange "UQ"
                }
                {
                    id 53
                    symbol "ACCL"
                    exchange "UQ"
                }
                {
                    id 54
                    symbol "ACCO"
                    exchange "UN"
                }
                {
                    id 55
                    symbol "ACDC"
                    exchange "UQ"
                }
                {
                    id 56
                    symbol "ACDI"
                    exchange "UN"
                }
                {
                    id 57
                    symbol "ACEC"
                    exchange "UQ"
                }
                {
                    id 58
                    symbol "ACEE"
                    exchange "UQ"
                }
                {
                    id 59
                    symbol "ACFN"
                    exchange "UQ"
                }
                {
                    id 60
                    symbol "ACHR"
                    exchange "UN"
                }
                {
                    id 61
                    symbol "ACIA"
                    exchange "UQ"
                }
                {
                    id 62
                    symbol "ACII"
                    exchange "UN"
                }
                {
                    id 63
                    symbol "ACIW"
                    exchange "UQ"
                }
                {
                    id 64
                    symbol "ACKIU"
                    exchange "UQ"
                }
                {
                    id 65
                    symbol "ACLA"
                    exchange "UQ"
                }
                {
                    id 66
                    symbol "ACLI"
                    exchange "UQ"
                }
                {
                    id 67
                    symbol "ACLNF"
                    exchange "UQ"
                }
                {
                    id 68
                    symbol "ACLO"
                    exchange "UQ"
                }
                {
                    id 69
                    symbol "ACLS"
                    exchange "UQ"
                }
                {
                    id 70
                    symbol "ACM"
                    exchange "UN"
                }
                {
                    id 71
                    symbol "ACMM"
                    exchange "UQ"
                }
                {
                    id 72
                    symbol "ACMR"
                    exchange "UQ"
                }
                {
                    id 73
                    symbol "ACN"
                    exchange "UN"
                }
                {
                    id 74
                    symbol "ACNAQ"
                    exchange "UQ"
                }
                {
                    id 75
                    symbol "ACO"
                    exchange "UN"
                }
                {
                    id 76
                    symbol "ACOM"
                    exchange "UQ"
                }
                {
                    id 77
                    symbol "ACOM1"
                    exchange "UQ"
                }
                {
                    id 78
                    symbol "ACQR"
                    exchange "UQ"
                }
                {
                    id 79
                    symbol "ACRO"
                    exchange "UN"
                }
                {
                    id 80
                    symbol "ACRO1"
                    exchange "UQ"
                }
                {
                    id 81
                    symbol "ACRUQ"
                    exchange "UQ"
                }
                {
                    id 82
                    symbol "ACS"
                    exchange "UN"
                }
                {
                    id 83
                    symbol "ACSC"
                    exchange "UQ"
                }
                {
                    id 84
                    symbol "ACSEF"
                    exchange "UQ"
                }
                {
                    id 85
                    symbol "ACTA"
                    exchange "UQ"
                }
                {
                    id 86
                    symbol "ACTG"
                    exchange "UQ"
                }
                {
                    id 87
                    symbol "ACTI"
                    exchange "UQ"
                }
                {
                    id 88
                    symbol "ACTI1"
                    exchange "UQ"
                }
                {
                    id 89
                    symbol "ACTL1"
                    exchange "UQ"
                }
                {
                    id 90
                    symbol "ACTRQ"
                    exchange "UQ"
                }
                {
                    id 91
                    symbol "ACTS"
                    exchange "UQ"
                }
                {
                    id 92
                    symbol "ACTV1"
                    exchange "UQ"
                }
                {
                    id 93
                    symbol "ACTV2"
                    exchange "UN"
                }
                {
                    id 94
                    symbol "ACVC"
                    exchange "UQ"
                }
                {
                    id 95
                    symbol "AD"
                    exchange "UN"
                }
                {
                    id 96
                    symbol "ADAL"
                    exchange "UQ"
                }
                {
                    id 97
                    symbol "ADAM"
                    exchange "UQ"
                }
                {
                    id 98
                    symbol "ADAPQ"
                    exchange "UQ"
                }
                {
                    id 99
                    symbol "ADAX"
                    exchange "UQ"
                }
                {
                    id 100
                    symbol "ADBE"
                    exchange "UQ"
                }
                {
                    id 101
                    symbol "ADBL"
                    exchange "UQ"
                }
                {
                    id 102
                    symbol "ADCC"
                    exchange "UQ"
                }
                {
                    id 103
                    symbol "ADCT1"
                    exchange "UQ"
                }
                {
                    id 104
                    symbol "ADEA"
                    exchange "UQ"
                }
                {
                    id 105
                    symbol "ADEP"
                    exchange "UQ"
                }
                {
                    id 106
                    symbol "ADER"
                    exchange "UQ"
                }
                {
                    id 107
                    symbol "ADEX1"
                    exchange "UQ"
                }
                {
                    id 108
                    symbol "ADFC"
                    exchange "UQ"
                }
                {
                    id 109
                    symbol "ADFS"
                    exchange "UN"
                }
                {
                    id 110
                    symbol "ADGI1"
                    exchange "UN"
                }
                {
                    id 111
                    symbol "ADI"
                    exchange "UQ"
                }
                {
                    id 112
                    symbol "ADIC"
                    exchange "UQ"
                }
                {
                    id 113
                    symbol "ADK1"
                    exchange "UN"
                }
                {
                    id 114
                    symbol "ADLTQ"
                    exchange "UQ"
                }
                {
                    id 115
                    symbol "ADNC"
                    exchange "UQ"
                }
                {
                    id 116
                    symbol "ADO"
                    exchange "UN"
                }
                {
                    id 117
                    symbol "ADP"
                    exchange "UQ"
                }
                {
                    id 118
                    symbol "ADPC"
                    exchange "UN"
                }
                {
                    id 119
                    symbol "ADRT"
                    exchange "UN"
                }
                {
                    id 120
                    symbol "ADSC"
                    exchange "UQ"
                }
                {
                    id 121
                    symbol "ADSE"
                    exchange "UQ"
                }
                {
                    id 122
                    symbol "ADSI"
                    exchange "UQ"
                }
                {
                    id 123
                    symbol "ADSK"
                    exchange "UQ"
                }
                {
                    id 124
                    symbol "ADSO1"
                    exchange "UQ"
                }
                {
                    id 125
                    symbol "ADSPQ"
                    exchange "UQ"
                }
                {
                    id 126
                    symbol "ADST"
                    exchange "UQ"
                }
                {
                    id 127
                    symbol "ADSW"
                    exchange "UN"
                }
                {
                    id 128
                    symbol "ADT"
                    exchange "UN"
                }
                {
                    id 129
                    symbol "ADT1"
                    exchange "UN"
                }
                {
                    id 130
                    symbol "ADTCQ"
                    exchange "UQ"
                }
                {
                    id 131
                    symbol "ADTN"
                    exchange "UQ"
                }
                {
                    id 132
                    symbol "ADVS"
                    exchange "UQ"
                }
                {
                    id 133
                    symbol "ADZA"
                    exchange "UQ"
                }
                {
                    id 134
                    symbol "AE"
                    exchange "UN"
                }
                {
                    id 135
                    symbol "AEAC"
                    exchange "UQ"
                }
                {
                    id 136
                    symbol "AEAE"
                    exchange "UQ"
                }
                {
                    id 137
                    symbol "AEDC"
                    exchange "UQ"
                }
                {
                    id 138
                    symbol "AEGN"
                    exchange "UQ"
                }
                {
                    id 139
                    symbol "AEHR"
                    exchange "UQ"
                }
                {
                    id 140
                    symbol "AEIC"
                    exchange "UQ"
                }
                {
                    id 141
                    symbol "AEIS"
                    exchange "UQ"
                }
                {
                    id 142
                    symbol "AENZ"
                    exchange "UN"
                }
                {
                    id 143
                    symbol "AEPI"
                    exchange "UQ"
                }
                {
                    id 144
                    symbol "AER"
                    exchange "UN"
                }
                {
                    id 145
                    symbol "AERG"
                    exchange "UQ"
                }
                {
                    id 146
                    symbol "AERS1"
                    exchange "UQ"
                }
                {
                    id 147
                    symbol "AERT"
                    exchange "UQ"
                }
                {
                    id 148
                    symbol "AESI"
                    exchange "UN"
                }
                {
                    id 149
                    symbol "AESP"
                    exchange "UQ"
                }
                {
                    id 150
                    symbol "AETCQ"
                    exchange "UQ"
                }
                {
                    id 151
                    symbol "AETUF"
                    exchange "UN"
                }
                {
                    id 152
                    symbol "AEYE"
                    exchange "UQ"
                }
                {
                    id 153
                    symbol "AEYGQ"
                    exchange "UQ"
                }
                {
                    id 154
                    symbol "AEZ"
                    exchange "UN"
                }
                {
                    id 155
                    symbol "AFAC"
                    exchange "UQ"
                }
                {
                    id 156
                    symbol "AFAQ"
                    exchange "UQ"
                }
                {
                    id 157
                    symbol "AFAR"
                    exchange "UQ"
                }
                {
                    id 158
                    symbol "AFCI"
                    exchange "UQ"
                }
                {
                    id 159
                    symbol "AFCO1"
                    exchange "UQ"
                }
                {
                    id 160
                    symbol "AFCX"
                    exchange "UQ"
                }
                {
                    id 161
                    symbol "AFIS"
                    exchange "UQ"
                }
                {
                    id 162
                    symbol "AFJK"
                    exchange "UQ"
                }
                {
                    id 163
                    symbol "AFLX"
                    exchange "UQ"
                }
                {
                    id 164
                    symbol "AFOP"
                    exchange "UQ"
                }
                {
                    id 165
                    symbol "AFRM"
                    exchange "UQ"
                }
                {
                    id 166
                    symbol "AFTR"
                    exchange "UN"
                }
                {
                    id 167
                    symbol "AFWY"
                    exchange "UQ"
                }
                {
                    id 168
                    symbol "AGACF"
                    exchange "UN"
                }
                {
                    id 169
                    symbol "AGAI"
                    exchange "UQ"
                }
                {
                    id 170
                    symbol "AGAM1"
                    exchange "UQ"
                }
                {
                    id 171
                    symbol "AGATQ"
                    exchange "UN"
                }
                {
                    id 172
                    symbol "AGCB"
                    exchange "UN"
                }
                {
                    id 173
                    symbol "AGCH"
                    exchange "UQ"
                }
                {
                    id 174
                    symbol "AGCO"
                    exchange "UN"
                }
                {
                    id 175
                    symbol "AGD1"
                    exchange "UN"
                }
                {
                    id 176
                    symbol "AGFY"
                    exchange "UQ"
                }
                {
                    id 177
                    symbol "AGGR"
                    exchange "UQ"
                }
                {
                    id 178
                    symbol "AGIL1"
                    exchange "UQ"
                }
                {
                    id 179
                    symbol "AGILQ"
                    exchange "UQ"
                }
                {
                    id 180
                    symbol "AGIS"
                    exchange "UQ"
                }
                {
                    id 181
                    symbol "AGMH"
                    exchange "UQ"
                }
                {
                    id 182
                    symbol "AGNUQ"
                    exchange "UN"
                }
                {
                    id 183
                    symbol "AGR1"
                    exchange "UN"
                }
                {
                    id 184
                    symbol "AGS1"
                    exchange "UN"
                }
                {
                    id 185
                    symbol "AGX"
                    exchange "UN"
                }
                {
                    id 186
                    symbol "AGYS"
                    exchange "UQ"
                }
                {
                    id 187
                    symbol "AHAG"
                    exchange "UQ"
                }
                {
                    id 188
                    symbol "AHI"
                    exchange "UQ"
                }
                {
                    id 189
                    symbol "AHII"
                    exchange "UQ"
                }
                {
                    id 190
                    symbol "AHIZQ"
                    exchange "UN"
                }
                {
                    id 191
                    symbol "AHLS"
                    exchange "UQ"
                }
                {
                    id 192
                    symbol "AHNA"
                    exchange "UN"
                }
                {
                    id 193
                    symbol "AHNCQ"
                    exchange "UN"
                }
                {
                    id 194
                    symbol "ORCL"
                    exchange "UN"
                }
                {
                    id 195
                    symbol "AHRN"
                    exchange "UQ"
                }
                {
                    id 196
                    symbol "AHWY"
                    exchange "UQ"
                }
                {
                    id 197
                    symbol "AI"
                    exchange "UN"
                }
                {
                    id 198
                    symbol "AICOQ"
                    exchange "UN"
                }
                {
                    id 199
                    symbol "AIFF"
                    exchange "UQ"
                }
                {
                    id 200
                    symbol "AIH1"
                    exchange "UN"
                }
                {
                    id 201
                    symbol "AIII1"
                    exchange "UQ"
                }
                {
                    id 202
                    symbol "AIIXY"
                    exchange "UQ"
                }
                {
                    id 203
                    symbol "AILE"
                    exchange "UQ"
                }
                {
                    id 204
                    symbol "AILP"
                    exchange "UQ"
                }
                {
                    id 205
                    symbol "AIM1"
                    exchange "UN"
                }
                {
                    id 206
                    symbol "AIMAU"
                    exchange "UQ"
                }
                {
                    id 207
                    symbol "AIMC"
                    exchange "UQ"
                }
                {
                    id 208
                    symbol "AIND"
                    exchange "UQ"
                }
                {
                    id 209
                    symbol "AINN"
                    exchange "UQ"
                }
                {
                    id 210
                    symbol "AIOT"
                    exchange "UQ"
                }
                {
                    id 211
                    symbol "AIP"
                    exchange "UQ"
                }
                {
                    id 212
                    symbol "AIPN"
                    exchange "UQ"
                }
                {
                    id 213
                    symbol "AIR"
                    exchange "UN"
                }
                {
                    id 214
                    symbol "AIRG"
                    exchange "UQ"
                }
                {
                    id 215
                    symbol "AIRI"
                    exchange "UN"
                }
                {
                    id 216
                    symbol "AIRM"
                    exchange "UQ"
                }
                {
                    id 217
                    symbol "AIRO1"
                    exchange "UQ"
                }
                {
                    id 218
                    symbol "AIRS1"
                    exchange "UQ"
                }
                {
                    id 219
                    symbol "AIRT"
                    exchange "UQ"
                }
                {
                    id 220
                    symbol "AIRV"
                    exchange "UQ"
                }
                {
                    id 221
                    symbol "AISP"
                    exchange "UQ"
                }
                {
                    id 222
                    symbol "AIT"
                    exchange "UN"
                }
                {
                    id 223
                    symbol "AITR"
                    exchange "UQ"
                }
                {
                    id 224
                    symbol "AIXI"
                    exchange "UQ"
                }
                {
                    id 225
                    symbol "AJRD"
                    exchange "UN"
                }
                {
                    id 226
                    symbol "AKAM"
                    exchange "UQ"
                }
                {
                    id 227
                    symbol "AKIC"
                    exchange "UQ"
                }
                {
                    id 228
                    symbol "AKLMQ"
                    exchange "UQ"
                }
                {
                    id 229
                    symbol "AKTS"
                    exchange "UQ"
                }
                {
                    id 230
                    symbol "AL"
                    exchange "UN"
                }
                {
                    id 231
                    symbol "ALAB"
                    exchange "UQ"
                }
                {
                    id 232
                    symbol "ALAC"
                    exchange "UQ"
                }
                {
                    id 233
                    symbol "ALAN"
                    exchange "UQ"
                }
                {
                    id 234
                    symbol "ALAR"
                    exchange "UQ"
                }
                {
                    id 235
                    symbol "ALCY"
                    exchange "UQ"
                }
                {
                    id 236
                    symbol "ALDN"
                    exchange "UQ"
                }
                {
                    id 237
                    symbol "ALDV1"
                    exchange "UQ"
                }
                {
                    id 238
                    symbol "ALDW"
                    exchange "UN"
                }
                {
                    id 239
                    symbol "ALF"
                    exchange "UQ"
                }
                {
                    id 240
                    symbol "ALFIQ"
                    exchange "UQ"
                }
                {
                    id 241
                    symbol "ALFO"
                    exchange "UQ"
                }
                {
                    id 242
                    symbol "ALG"
                    exchange "UN"
                }
                {
                    id 243
                    symbol "ALGM"
                    exchange "UQ"
                }
                {
                    id 244
                    symbol "ALGR"
                    exchange "UQ"
                }
                {
                    id 245
                    symbol "ALGT"
                    exchange "UQ"
                }
                {
                    id 246
                    symbol "ALIT"
                    exchange "UN"
                }
                {
                    id 247
                    symbol "ALJ"
                    exchange "UN"
                }
                {
                    id 248
                    symbol "ALJJ"
                    exchange "UQ"
                }
                {
                    id 249
                    symbol "ALK"
                    exchange "UN"
                }
                {
                    id 250
                    symbol "ALKT"
                    exchange "UQ"
                }
                {
                    id 251
                    symbol "ALLE"
                    exchange "UN"
                }
                {
                    id 252
                    symbol "ALLR1"
                    exchange "UQ"
                }
                {
                    id 253
                    symbol "ALLT"
                    exchange "UQ"
                }
                {
                    id 254
                    symbol "ALN1"
                    exchange "UN"
                }
                {
                    id 255
                    symbol "ALNK"
                    exchange "UQ"
                }
                {
                    id 256
                    symbol "ALNT"
                    exchange "UQ"
                }
                {
                    id 257
                    symbol "ALOR"
                    exchange "UQ"
                }
                {
                    id 258
                    symbol "ALOT"
                    exchange "UQ"
                }
                {
                    id 259
                    symbol "ALPH"
                    exchange "UQ"
                }
                {
                    id 260
                    symbol "ALPP"
                    exchange "UQ"
                }
                {
                    id 261
                    symbol "ALPSQ"
                    exchange "UQ"
                }
                {
                    id 262
                    symbol "ALRC"
                    exchange "UQ"
                }
                {
                    id 263
                    symbol "ALRM"
                    exchange "UQ"
                }
                {
                    id 264
                    symbol "ALRN2"
                    exchange "UQ"
                }
                {
                    id 265
                    symbol "ALSA"
                    exchange "UQ"
                }
                {
                    id 266
                    symbol "ALSM"
                    exchange "UQ"
                }
                {
                    id 267
                    symbol "ALTG"
                    exchange "UN"
                }
                {
                    id 268
                    symbol "ALTR"
                    exchange "UQ"
                }
                {
                    id 269
                    symbol "ALTR1"
                    exchange "UQ"
                }
                {
                    id 270
                    symbol "ALTS"
                    exchange "UQ"
                }
                {
                    id 271
                    symbol "ALTU"
                    exchange "UQ"
                }
                {
                    id 272
                    symbol "ALVRQ"
                    exchange "UQ"
                }
                {
                    id 273
                    symbol "ALY"
                    exchange "UN"
                }
                {
                    id 274
                    symbol "ALYAF"
                    exchange "UQ"
                }
                {
                    id 275
                    symbol "ALYS"
                    exchange "UQ"
                }
                {
                    id 276
                    symbol "AM"
                    exchange "UN"
                }
                {
                    id 277
                    symbol "AM2"
                    exchange "UN"
                }
                {
                    id 278
                    symbol "AMAP"
                    exchange "UQ"
                }
                {
                    id 279
                    symbol "AMAT"
                    exchange "UQ"
                }
                {
                    id 280
                    symbol "AMBA"
                    exchange "UQ"
                }
                {
                    id 281
                    symbol "AMBI"
                    exchange "UN"
                }
                {
                    id 282
                    symbol "AMBR"
                    exchange "UN"
                }
                {
                    id 283
                    symbol "AMCC"
                    exchange "UQ"
                }
                {
                    id 284
                    symbol "AMCF"
                    exchange "UQ"
                }
                {
                    id 285
                    symbol "AMCS"
                    exchange "UQ"
                }
                {
                    id 286
                    symbol "AMCVQ"
                    exchange "UQ"
                }
                {
                    id 287
                    symbol "AMD"
                    exchange "UQ"
                }
                {
                    id 288
                    symbol "AME"
                    exchange "UN"
                }
                {
                    id 289
                    symbol "AMEP"
                    exchange "UQ"
                }
                {
                    id 290
                    symbol "AMFW"
                    exchange "UN"
                }
                {
                    id 291
                    symbol "AMID1"
                    exchange "UN"
                }
                {
                    id 292
                    symbol "AMIEQ"
                    exchange "UQ"
                }
                {
                    id 293
                    symbol "AMIIQ"
                    exchange "UN"
                }
                {
                    id 294
                    symbol "AMIS"
                    exchange "UQ"
                }
                {
                    id 295
                    symbol "AMK1"
                    exchange "UN"
                }
                {
                    id 296
                    symbol "AMKR"
                    exchange "UQ"
                }
                {
                    id 297
                    symbol "AMLJ"
                    exchange "UQ"
                }
                {
                    id 298
                    symbol "AMNI"
                    exchange "UQ"
                }
                {
                    id 299
                    symbol "AMNUQ"
                    exchange "UQ"
                }
                {
                    id 300
                    symbol "AMP1"
                    exchange "UN"
                }
                {
                    id 301
                    symbol "AMPG"
                    exchange "UQ"
                }
                {
                    id 302
                    symbol "AMPI"
                    exchange "UN"
                }
                {
                    id 303
                    symbol "AMPL"
                    exchange "UQ"
                }
                {
                    id 304
                    symbol "AMPX"
                    exchange "UN"
                }
                {
                    id 305
                    symbol "AMPXQ"
                    exchange "UQ"
                }
                {
                    id 306
                    symbol "AMPY"
                    exchange "UN"
                }
                {
                    id 307
                    symbol "AMRC"
                    exchange "UN"
                }
                {
                    id 308
                    symbol "AMRQQ"
                    exchange "UQ"
                }
                {
                    id 309
                    symbol "AMSC"
                    exchange "UQ"
                }
                {
                    id 310
                    symbol "AMSI"
                    exchange "UQ"
                }
                {
                    id 311
                    symbol "AMSI1"
                    exchange "UQ"
                }
                {
                    id 312
                    symbol "AMST"
                    exchange "UQ"
                }
                {
                    id 313
                    symbol "AMTM"
                    exchange "UN"
                }
                {
                    id 314
                    symbol "AMTX"
                    exchange "UQ"
                }
                {
                    id 315
                    symbol "AMVC"
                    exchange "UQ"
                }
                {
                    id 316
                    symbol "AMXC"
                    exchange "UQ"
                }
                {
                    id 317
                    symbol "AN1"
                    exchange "UN"
                }
                {
                    id 318
                    symbol "ANAC"
                    exchange "UN"
                }
                {
                    id 319
                    symbol "ANAD"
                    exchange "UQ"
                }
                {
                    id 320
                    symbol "ANCCQ"
                    exchange "UQ"
                }
                {
                    id 321
                    symbol "ANCJQ"
                    exchange "UQ"
                }
                {
                    id 322
                    symbol "ANCR"
                    exchange "UQ"
                }
                {
                    id 323
                    symbol "ANDA1"
                    exchange "UQ"
                }
                {
                    id 324
                    symbol "ANDA2"
                    exchange "UQ"
                }
                {
                    id 325
                    symbol "ANDN1"
                    exchange "UQ"
                }
                {
                    id 326
                    symbol "ANDR"
                    exchange "UN"
                }
                {
                    id 327
                    symbol "ANDV"
                    exchange "UN"
                }
                {
                    id 328
                    symbol "ANDW"
                    exchange "UQ"
                }
                {
                    id 329
                    symbol "ANDX"
                    exchange "UN"
                }
                {
                    id 330
                    symbol "ANEN"
                    exchange "UQ"
                }
                {
                    id 331
                    symbol "ANET"
                    exchange "UN"
                }
                {
                    id 332
                    symbol "ANET2"
                    exchange "UQ"
                }
                {
                    id 333
                    symbol "ANI"
                    exchange "UN"
                }
                {
                    id 334
                    symbol "ANIC"
                    exchange "UQ"
                }
                {
                    id 335
                    symbol "ANLG"
                    exchange "UQ"
                }
                {
                    id 336
                    symbol "ANLY"
                    exchange "UQ"
                }
                {
                    id 337
                    symbol "ANMP"
                    exchange "UQ"
                }
                {
                    id 338
                    symbol "ANS"
                    exchange "UN"
                }
                {
                    id 339
                    symbol "ANSC"
                    exchange "UQ"
                }
                {
                    id 340
                    symbol "ANSS"
                    exchange "UQ"
                }
                {
                    id 341
                    symbol "ANST"
                    exchange "UQ"
                }
                {
                    id 342
                    symbol "ANSW"
                    exchange "UQ"
                }
                {
                    id 343
                    symbol "ANT"
                    exchange "UN"
                }
                {
                    id 344
                    symbol "ANTP"
                    exchange "UQ"
                }
                {
                    id 345
                    symbol "ANV1"
                    exchange "UN"
                }
                {
                    id 346
                    symbol "ANWWQ"
                    exchange "UN"
                }
                {
                    id 347
                    symbol "ANY"
                    exchange "UQ"
                }
                {
                    id 348
                    symbol "AOGO"
                    exchange "UQ"
                }
                {
                    id 349
                    symbol "AOGSQ"
                    exchange "UN"
                }
                {
                    id 350
                    symbol "AOL"
                    exchange "UN"
                }
                {
                    id 351
                    symbol "AONEQ"
                    exchange "UQ"
                }
                {
                    id 352
                    symbol "AORGB"
                    exchange "UQ"
                }
                {
                    id 353
                    symbol "AOS"
                    exchange "UN"
                }
                {
                    id 354
                    symbol "AOSL"
                    exchange "UQ"
                }
                {
                    id 355
                    symbol "AOUT"
                    exchange "UQ"
                }
                {
                    id 356
                    symbol "AP"
                    exchange "UN"
                }
                {
                    id 357
                    symbol "APA"
                    exchange "UQ"
                }
                {
                    id 358
                    symbol "APAC1"
                    exchange "UQ"
                }
                {
                    id 359
                    symbol "APAGF"
                    exchange "UQ"
                }
                {
                    id 360
                    symbol "APC"
                    exchange "UN"
                }
                {
                    id 361
                    symbol "APCA"
                    exchange "UN"
                }
                {
                    id 362
                    symbol "APCC"
                    exchange "UQ"
                }
                {
                    id 363
                    symbol "APCX"
                    exchange "UQ"
                }
                {
                    id 364
                    symbol "APEX1"
                    exchange "UQ"
                }
                {
                    id 365
                    symbol "APG"
                    exchange "UN"
                }
                {
                    id 366
                    symbol "APGB"
                    exchange "UN"
                }
                {
                    id 367
                    symbol "APH"
                    exchange "UN"
                }
                {
                    id 368
                    symbol "API"
                    exchange "UQ"
                }
                {
                    id 369
                    symbol "API1"
                    exchange "UN"
                }
                {
                    id 370
                    symbol "APIC"
                    exchange "UQ"
                }
                {
                    id 371
                    symbol "APKT"
                    exchange "UQ"
                }
                {
                    id 372
                    symbol "APL"
                    exchange "UN"
                }
                {
                    id 373
                    symbol "APLP"
                    exchange "UQ"
                }
                {
                    id 374
                    symbol "APLX"
                    exchange "UQ"
                }
                {
                    id 375
                    symbol "APM1"
                    exchange "UN"
                }
                {
                    id 376
                    symbol "APMC"
                    exchange "UQ"
                }
                {
                    id 377
                    symbol "APMI"
                    exchange "UQ"
                }
                {
                    id 378
                    symbol "APNC"
                    exchange "UN"
                }
                {
                    id 379
                    symbol "APNI"
                    exchange "UN"
                }
                {
                    id 380
                    symbol "APNT1"
                    exchange "UQ"
                }
                {
                    id 381
                    symbol "APP"
                    exchange "UQ"
                }
                {
                    id 382
                    symbol "APPCQ"
                    exchange "UN"
                }
                {
                    id 383
                    symbol "APPF"
                    exchange "UQ"
                }
                {
                    id 384
                    symbol "APPN"
                    exchange "UQ"
                }
                {
                    id 385
                    symbol "APPS"
                    exchange "UQ"
                }
                {
                    id 386
                    symbol "APPS1"
                    exchange "UQ"
                }
                {
                    id 387
                    symbol "APQCF"
                    exchange "UQ"
                }
                {
                    id 388
                    symbol "APR1"
                    exchange "UN"
                }
                {
                    id 389
                    symbol "APRS"
                    exchange "UQ"
                }
                {
                    id 390
                    symbol "APSG1"
                    exchange "UQ"
                }
                {
                    id 391
                    symbol "APTI"
                    exchange "UQ"
                }
                {
                    id 392
                    symbol "APTI1"
                    exchange "UQ"
                }
                {
                    id 393
                    symbol "APTM1"
                    exchange "UQ"
                }
                {
                    id 394
                    symbol "APW"
                    exchange "UN"
                }
                {
                    id 395
                    symbol "APWC"
                    exchange "UQ"
                }
                {
                    id 396
                    symbol "APWR1"
                    exchange "UQ"
                }
                {
                    id 397
                    symbol "APWRQ"
                    exchange "UQ"
                }
                {
                    id 398
                    symbol "APXI"
                    exchange "UQ"
                }
                {
                    id 399
                    symbol "AQ"
                    exchange "UN"
                }
                {
                    id 400
                    symbol "AQ1"
                    exchange "UN"
                }
                {
                    id 401
                    symbol "AQCR"
                    exchange "UQ"
                }
                {
                    id 402
                    symbol "AQMS"
                    exchange "UQ"
                }
                {
                    id 403
                    symbol "AQNT"
                    exchange "UQ"
                }
                {
                    id 404
                    symbol "AQP"
                    exchange "UN"
                }
                {
                    id 405
                    symbol "AQU"
                    exchange "UQ"
                }
                {
                    id 406
                    symbol "AQUA"
                    exchange "UN"
                }
                {
                    id 407
                    symbol "AR"
                    exchange "UN"
                }
                {
                    id 408
                    symbol "ARB1"
                    exchange "UN"
                }
                {
                    id 409
                    symbol "ARBA"
                    exchange "UQ"
                }
                {
                    id 410
                    symbol "ARBB"
                    exchange "UQ"
                }
                {
                    id 411
                    symbol "ARBE"
                    exchange "UQ"
                }
                {
                    id 412
                    symbol "ARBG"
                    exchange "UQ"
                }
                {
                    id 413
                    symbol "ARBX"
                    exchange "UQ"
                }
                {
                    id 414
                    symbol "ARC"
                    exchange "UN"
                }
                {
                    id 415
                    symbol "ARC1"
                    exchange "UN"
                }
                {
                    id 416
                    symbol "ARCB"
                    exchange "UQ"
                }
                {
                    id 417
                    symbol "ARCK"
                    exchange "UQ"
                }
                {
                    id 418
                    symbol "ARCW"
                    exchange "UQ"
                }
                {
                    id 419
                    symbol "ARCX"
                    exchange "UN"
                }
                {
                    id 420
                    symbol "ARD1"
                    exchange "UN"
                }
                {
                    id 421
                    symbol "ARDI"
                    exchange "UQ"
                }
                {
                    id 422
                    symbol "ARDT1"
                    exchange "UQ"
                }
                {
                    id 423
                    symbol "AREM1"
                    exchange "UQ"
                }
                {
                    id 424
                    symbol "AREXQ"
                    exchange "UQ"
                }
                {
                    id 425
                    symbol "ARG"
                    exchange "UN"
                }
                {
                    id 426
                    symbol "ARGU"
                    exchange "UQ"
                }
                {
                    id 427
                    symbol "ARII"
                    exchange "UQ"
                }
                {
                    id 428
                    symbol "ARLCF"
                    exchange "UQ"
                }
                {
                    id 429
                    symbol "ARM"
                    exchange "UQ"
                }
                {
                    id 430
                    symbol "ARMH"
                    exchange "UQ"
                }
                {
                    id 431
                    symbol "ARMK"
                    exchange "UN"
                }
                {
                    id 432
                    symbol "ARNC"
                    exchange "UN"
                }
                {
                    id 433
                    symbol "AROC"
                    exchange "UN"
                }
                {
                    id 434
                    symbol "ARPJQ"
                    exchange "UN"
                }
                {
                    id 435
                    symbol "ARQ"
                    exchange "UQ"
                }
                {
                    id 436
                    symbol "ARQQ"
                    exchange "UQ"
                }
                {
                    id 437
                    symbol "ARRS"
                    exchange "UQ"
                }
                {
                    id 438
                    symbol "ARRY"
                    exchange "UQ"
                }
                {
                    id 439
                    symbol "ARS1"
                    exchange "UN"
                }
                {
                    id 440
                    symbol "ARST"
                    exchange "UQ"
                }
                {
                    id 441
                    symbol "ART1"
                    exchange "UN"
                }
                {
                    id 442
                    symbol "ARTE"
                    exchange "UQ"
                }
                {
                    id 443
                    symbol "ARTE1"
                    exchange "UQ"
                }
                {
                    id 444
                    symbol "ARTG"
                    exchange "UQ"
                }
                {
                    id 445
                    symbol "ARTI1"
                    exchange "UQ"
                }
                {
                    id 446
                    symbol "ARTW"
                    exchange "UQ"
                }
                {
                    id 447
                    symbol "ARTX"
                    exchange "UQ"
                }
                {
                    id 448
                    symbol "ARUN"
                    exchange "UQ"
                }
                {
                    id 449
                    symbol "ARVX"
                    exchange "UQ"
                }
                {
                    id 450
                    symbol "ARW"
                    exchange "UN"
                }
                {
                    id 451
                    symbol "ARWA"
                    exchange "UQ"
                }
                {
                    id 452
                    symbol "ARX"
                    exchange "UN"
                }
                {
                    id 453
                    symbol "ARXX"
                    exchange "UQ"
                }
                {
                    id 454
                    symbol "ARYE"
                    exchange "UQ"
                }
                {
                    id 455
                    symbol "ASAI1"
                    exchange "UQ"
                }
                {
                    id 456
                    symbol "ASAL"
                    exchange "UQ"
                }
                {
                    id 457
                    symbol "ASAM1"
                    exchange "UQ"
                }
                {
                    id 458
                    symbol "ASAN"
                    exchange "UN"
                }
                {
                    id 459
                    symbol "ASAPQ"
                    exchange "UQ"
                }
                {
                    id 460
                    symbol "ASAQ"
                    exchange "UN"
                }
                {
                    id 461
                    symbol "ASAX"
                    exchange "UQ"
                }
                {
                    id 462
                    symbol "ASC"
                    exchange "UN"
                }
                {
                    id 463
                    symbol "ASCBF"
                    exchange "UQ"
                }
                {
                    id 464
                    symbol "ASCL"
                    exchange "UQ"
                }
                {
                    id 465
                    symbol "ASCMA"
                    exchange "UQ"
                }
                {
                    id 466
                    symbol "ASCX"
                    exchange "UQ"
                }
                {
                    id 467
                    symbol "ASDG"
                    exchange "UQ"
                }
                {
                    id 468
                    symbol "ASDS"
                    exchange "UQ"
                }
                {
                    id 469
                    symbol "ASDV"
                    exchange "UQ"
                }
                {
                    id 470
                    symbol "ASEC"
                    exchange "UQ"
                }
                {
                    id 471
                    symbol "ASGN"
                    exchange "UN"
                }
                {
                    id 472
                    symbol "ASHE"
                    exchange "UQ"
                }
                {
                    id 473
                    symbol "ASIA1"
                    exchange "UQ"
                }
                {
                    id 474
                    symbol "ASIGF1"
                    exchange "UQ"
                }
                {
                    id 475
                    symbol "ASIS"
                    exchange "UQ"
                }
                {
                    id 476
                    symbol "ASKJ"
                    exchange "UQ"
                }
                {
                    id 477
                    symbol "ASLE"
                    exchange "UQ"
                }
                {
                    id 478
                    symbol "ASMIY"
                    exchange "UQ"
                }
                {
                    id 479
                    symbol "ASML"
                    exchange "UQ"
                }
                {
                    id 480
                    symbol "ASND1"
                    exchange "UQ"
                }
                {
                    id 481
                    symbol "ASNS"
                    exchange "UQ"
                }
                {
                    id 482
                    symbol "ASPIY"
                    exchange "UQ"
                }
                {
                    id 483
                    symbol "ASPT"
                    exchange "UQ"
                }
                {
                    id 484
                    symbol "ASPXQ"
                    exchange "UQ"
                }
                {
                    id 485
                    symbol "ASR"
                    exchange "UN"
                }
                {
                    id 486
                    symbol "ASTC"
                    exchange "UQ"
                }
                {
                    id 487
                    symbol "ASTE"
                    exchange "UQ"
                }
                {
                    id 488
                    symbol "ASTI"
                    exchange "UQ"
                }
                {
                    id 489
                    symbol "ASTR"
                    exchange "UQ"
                }
                {
                    id 490
                    symbol "ASTS"
                    exchange "UQ"
                }
                {
                    id 491
                    symbol "ASTTY"
                    exchange "UQ"
                }
                {
                    id 492
                    symbol "ASTX1"
                    exchange "UQ"
                }
                {
                    id 493
                    symbol "ASUR"
                    exchange "UQ"
                }
                {
                    id 494
                    symbol "ASV"
                    exchange "UQ"
                }
                {
                    id 495
                    symbol "ASVI"
                    exchange "UQ"
                }
                {
                    id 496
                    symbol "ASW1"
                    exchange "UN"
                }
                {
                    id 497
                    symbol "ASWX"
                    exchange "UQ"
                }
                {
                    id 498
                    symbol "ASX"
                    exchange "UN"
                }
                {
                    id 499
                    symbol "ASYS"
                    exchange "UQ"
                }
                {
                    id 500
                    symbol "ASYTQ"
                    exchange "UQ"
                }
                {
                    id 501
                    symbol "ASZ"
                    exchange "UN"
                }
                {
                    id 502
                    symbol "ATA"
                    exchange "UN"
                }
                {
                    id 503
                    symbol "ATAC1"
                    exchange "UQ"
                }
                {
                    id 504
                    symbol "ATAHQ"
                    exchange "UQ"
                }
                {
                    id 505
                    symbol "ATAQ"
                    exchange "UN"
                }
                {
                    id 506
                    symbol "ATAR1"
                    exchange "UQ"
                }
                {
                    id 507
                    symbol "ATB"
                    exchange "UN"
                }
                {
                    id 508
                    symbol "ATC"
                    exchange "UN"
                }
                {
                    id 509
                    symbol "ATCH"
                    exchange "UN"
                }
                {
                    id 510
                    symbol "ATCH1"
                    exchange "UQ"
                }
                {
                    id 511
                    symbol "ATCM"
                    exchange "UQ"
                }
                {
                    id 512
                    symbol "ATCX"
                    exchange "UQ"
                }
                {
                    id 513
                    symbol "ATEA"
                    exchange "UQ"
                }
                {
                    id 514
                    symbol "ATEK"
                    exchange "UN"
                }
                {
                    id 515
                    symbol "ATEL"
                    exchange "UN"
                }
                {
                    id 516
                    symbol "ATEN"
                    exchange "UN"
                }
                {
                    id 517
                    symbol "ATEYY"
                    exchange "UN"
                }
                {
                    id 518
                    symbol "ATGCQ"
                    exchange "UQ"
                }
                {
                    id 519
                    symbol "ATGL"
                    exchange "UQ"
                }
                {
                    id 520
                    symbol "ATGN"
                    exchange "UQ"
                }
                {
                    id 521
                    symbol "ATHL"
                    exchange "UN"
                }
                {
                    id 522
                    symbol "ATHR"
                    exchange "UQ"
                }
                {
                    id 523
                    symbol "ATHYQ"
                    exchange "UQ"
                }
                {
                    id 524
                    symbol "ATI"
                    exchange "UN"
                }
                {
                    id 525
                    symbol "ATIS"
                    exchange "UQ"
                }
                {
                    id 526
                    symbol "ATKR"
                    exchange "UN"
                }
                {
                    id 527
                    symbol "ATLPA"
                    exchange "UQ"
                }
                {
                    id 528
                    symbol "ATLS"
                    exchange "UN"
                }
                {
                    id 529
                    symbol "ATLS1"
                    exchange "UN"
                }
                {
                    id 530
                    symbol "ATLS2"
                    exchange "UN"
                }
                {
                    id 531
                    symbol "ATMC"
                    exchange "UQ"
                }
                {
                    id 532
                    symbol "ATML"
                    exchange "UQ"
                }
                {
                    id 533
                    symbol "ATMU"
                    exchange "UN"
                }
                {
                    id 534
                    symbol "ATMV"
                    exchange "UQ"
                }
                {
                    id 535
                    symbol "ATN"
                    exchange "UN"
                }
                {
                    id 536
                    symbol "ATN1"
                    exchange "UN"
                }
                {
                    id 537
                    symbol "ATNY"
                    exchange "UQ"
                }
                {
                    id 538
                    symbol "ATOM"
                    exchange "UQ"
                }
                {
                    id 539
                    symbol "ATON"
                    exchange "UQ"
                }
                {
                    id 540
                    symbol "ATPAQ"
                    exchange "UQ"
                }
                {
                    id 541
                    symbol "ATPL"
                    exchange "UQ"
                }
                {
                    id 542
                    symbol "ATRO"
                    exchange "UQ"
                }
                {
                    id 543
                    symbol "ATRS1"
                    exchange "UQ"
                }
                {
                    id 544
                    symbol "ATS"
                    exchange "UN"
                }
                {
                    id 545
                    symbol "ATSC1"
                    exchange "UN"
                }
                {
                    id 546
                    symbol "ATSG"
                    exchange "UQ"
                }
                {
                    id 547
                    symbol "ATSN"
                    exchange "UQ"
                }
                {
                    id 548
                    symbol "ATTOF"
                    exchange "UN"
                }
                {
                    id 549
                    symbol "ATTU"
                    exchange "UQ"
                }
                {
                    id 550
                    symbol "ATTY"
                    exchange "UQ"
                }
                {
                    id 551
                    symbol "ATW"
                    exchange "UN"
                }
                {
                    id 552
                    symbol "ATX"
                    exchange "UQ"
                }
                {
                    id 553
                    symbol "ATXG"
                    exchange "UQ"
                }
                {
                    id 554
                    symbol "ATXI1"
                    exchange "UQ"
                }
                {
                    id 555
                    symbol "ATYT"
                    exchange "UQ"
                }
                {
                    id 556
                    symbol "AUDC"
                    exchange "UQ"
                }
                {
                    id 557
                    symbol "AUGS"
                    exchange "UQ"
                }
                {
                    id 558
                    symbol "AUGT1"
                    exchange "UQ"
                }
                {
                    id 559
                    symbol "AUID"
                    exchange "UQ"
                }
                {
                    id 560
                    symbol "AULT1"
                    exchange "UQ"
                }
                {
                    id 561
                    symbol "AUOTY"
                    exchange "UN"
                }
                {
                    id 562
                    symbol "AUR"
                    exchange "UQ"
                }
                {
                    id 563
                    symbol "AURAQ"
                    exchange "UQ"
                }
                {
                    id 564
                    symbol "AUS"
                    exchange "UN"
                }
                {
                    id 565
                    symbol "AUSA"
                    exchange "UQ"
                }
                {
                    id 566
                    symbol "AUSPF"
                    exchange "UN"
                }
                {
                    id 567
                    symbol "AUTH"
                    exchange "UQ"
                }
                {
                    id 568
                    symbol "AUTNY"
                    exchange "UQ"
                }
                {
                    id 569
                    symbol "AUTO1"
                    exchange "UQ"
                }
                {
                    id 570
                    symbol "AUUD"
                    exchange "UQ"
                }
                {
                    id 571
                    symbol "AUZR"
                    exchange "UQ"
                }
                {
                    id 572
                    symbol "AV1"
                    exchange "UN"
                }
                {
                    id 573
                    symbol "AVAN"
                    exchange "UN"
                }
                {
                    id 574
                    symbol "AVAV"
                    exchange "UQ"
                }
                {
                    id 575
                    symbol "AVC"
                    exchange "UN"
                }
                {
                    id 576
                    symbol "AVCT1"
                    exchange "UQ"
                }
                {
                    id 577
                    symbol "AVCTQ"
                    exchange "UQ"
                }
                {
                    id 578
                    symbol "AVDS1"
                    exchange "UQ"
                }
                {
                    id 579
                    symbol "AVDX"
                    exchange "UQ"
                }
                {
                    id 580
                    symbol "AVGE1"
                    exchange "UQ"
                }
                {
                    id 581
                    symbol "AVGO"
                    exchange "UQ"
                }
                {
                    id 582
                    symbol "AVGO1"
                    exchange "UQ"
                }
                {
                    id 583
                    symbol "AVGTF"
                    exchange "UN"
                }
                {
                    id 584
                    symbol "AVHI"
                    exchange "UQ"
                }
                {
                    id 585
                    symbol "AVHOQ"
                    exchange "UN"
                }
                {
                    id 586
                    symbol "AVI"
                    exchange "UN"
                }
                {
                    id 587
                    symbol "AVID"
                    exchange "UQ"
                }
                {
                    id 588
                    symbol "AVL1"
                    exchange "UN"
                }
                {
                    id 589
                    symbol "AVLR"
                    exchange "UN"
                }
                {
                    id 590
                    symbol "AVMC1"
                    exchange "UQ"
                }
                {
                    id 591
                    symbol "AVNT1"
                    exchange "UQ"
                }
                {
                    id 592
                    symbol "AVNW"
                    exchange "UQ"
                }
                {
                    id 593
                    symbol "AVNX"
                    exchange "UQ"
                }
                {
                    id 594
                    symbol "AVOL"
                    exchange "UN"
                }
                {
                    id 595
                    symbol "AVPT"
                    exchange "UQ"
                }
                {
                    id 596
                    symbol "AVSR"
                    exchange "UQ"
                }
                {
                    id 597
                    symbol "AVT"
                    exchange "UQ"
                }
                {
                    id 598
                    symbol "AVTMQ"
                    exchange "UQ"
                }
                {
                    id 599
                    symbol "AVV"
                    exchange "UN"
                }
                {
                    id 600
                    symbol "AVX"
                    exchange "UN"
                }
                {
                    id 601
                    symbol "AVYAQ"
                    exchange "UN"
                }
                {
                    id 602
                    symbol "AVZAQ"
                    exchange "UQ"
                }
                {
                    id 603
                    symbol "AW"
                    exchange "UN"
                }
                {
                    id 604
                    symbol "AWA"
                    exchange "UN"
                }
                {
                    id 605
                    symbol "AWAY1"
                    exchange "UQ"
                }
                {
                    id 606
                    symbol "AWIN"
                    exchange "UQ"
                }
                {
                    id 607
                    symbol "AWRE"
                    exchange "UQ"
                }
                {
                    id 608
                    symbol "AWX"
                    exchange "UN"
                }
                {
                    id 609
                    symbol "AXAC"
                    exchange "UN"
                }
                {
                    id 610
                    symbol "AXAR"
                    exchange "UQ"
                }
                {
                    id 611
                    symbol "AXAS"
                    exchange "UQ"
                }
                {
                    id 612
                    symbol "AXE"
                    exchange "UN"
                }
                {
                    id 613
                    symbol "AXHI"
                    exchange "UN"
                }
                {
                    id 614
                    symbol "AXHM"
                    exchange "UQ"
                }
                {
                    id 615
                    symbol "AXIL"
                    exchange "UN"
                }
                {
                    id 616
                    symbol "AXNT"
                    exchange "UQ"
                }
                {
                    id 617
                    symbol "AXON"
                    exchange "UQ"
                }
                {
                    id 618
                    symbol "AXPWQ"
                    exchange "UQ"
                }
                {
                    id 619
                    symbol "AXSI"
                    exchange "UQ"
                }
                {
                    id 620
                    symbol "AXSO"
                    exchange "UN"
                }
                {
                    id 621
                    symbol "AXST"
                    exchange "UQ"
                }
                {
                    id 622
                    symbol "AXTC"
                    exchange "UQ"
                }
                {
                    id 623
                    symbol "AXTI"
                    exchange "UQ"
                }
                {
                    id 624
                    symbol "AXYS"
                    exchange "UQ"
                }
                {
                    id 625
                    symbol "AYD"
                    exchange "UN"
                }
                {
                    id 626
                    symbol "AYI"
                    exchange "UN"
                }
                {
                    id 627
                    symbol "AYR"
                    exchange "UN"
                }
                {
                    id 628
                    symbol "AYS"
                    exchange "UN"
                }
                {
                    id 629
                    symbol "AYX"
                    exchange "UN"
                }
                {
                    id 630
                    symbol "AZ"
                    exchange "UQ"
                }
                {
                    id 631
                    symbol "AZIC"
                    exchange "UQ"
                }
                {
                    id 632
                    symbol "AZPN"
                    exchange "UQ"
                }
                {
                    id 633
                    symbol "AZPN1"
                    exchange "UQ"
                }
                {
                    id 634
                    symbol "AZUL"
                    exchange "UN"
                }
                {
                    id 635
                    symbol "AZURQ"
                    exchange "UQ"
                }
                {
                    id 636
                    symbol "AZZ"
                    exchange "UN"
                }
                {
                    id 637
                    symbol "B"
                    exchange "UN"
                }
                {
                    id 638
                    symbol "BA"
                    exchange "UN"
                }
                {
                    id 639
                    symbol "BAANF"
                    exchange "UQ"
                }
                {
                    id 640
                    symbol "BACA"
                    exchange "UN"
                }
                {
                    id 641
                    symbol "BAER"
                    exchange "UQ"
                }
                {
                    id 642
                    symbol "BAH"
                    exchange "UN"
                }
                {
                    id 643
                    symbol "BALT2"
                    exchange "UN"
                }
                {
                    id 644
                    symbol "BAND"
                    exchange "UQ"
                }
                {
                    id 645
                    symbol "BANL"
                    exchange "UQ"
                }
                {
                    id 646
                    symbol "BAR1"
                    exchange "UN"
                }
                {
                    id 647
                    symbol "BASE"
                    exchange "UQ"
                }
                {
                    id 648
                    symbol "BASEA"
                    exchange "UQ"
                }
                {
                    id 649
                    symbol "BASXQ"
                    exchange "UN"
                }
                {
                    id 650
                    symbol "BATL"
                    exchange "UN"
                }
                {
                    id 651
                    symbol "BATT1"
                    exchange "UQ"
                }
                {
                    id 652
                    symbol "BAY1"
                    exchange "UN"
                }
                {
                    id 653
                    symbol "BAYA"
                    exchange "UQ"
                }
                {
                    id 654
                    symbol "BB"
                    exchange "UN"
                }
                {
                    id 655
                    symbol "BBAI"
                    exchange "UN"
                }
                {
                    id 656
                    symbol "BBBB"
                    exchange "UQ"
                }
                {
                    id 657
                    symbol "BBCP"
                    exchange "UQ"
                }
                {
                    id 658
                    symbol "BBEPQ"
                    exchange "UQ"
                }
                {
                    id 659
                    symbol "BBG"
                    exchange "UN"
                }
                {
                    id 660
                    symbol "BBLKF"
                    exchange "UN"
                }
                {
                    id 661
                    symbol "BBLUQ"
                    exchange "UQ"
                }
                {
                    id 662
                    symbol "BBND"
                    exchange "UQ"
                }
                {
                    id 663
                    symbol "BBOX"
                    exchange "UQ"
                }
                {
                    id 664
                    symbol "BBRC1"
                    exchange "UQ"
                }
                {
                    id 665
                    symbol "BBSI"
                    exchange "UQ"
                }
                {
                    id 666
                    symbol "BBSW"
                    exchange "UQ"
                }
                {
                    id 667
                    symbol "BBU"
                    exchange "UN"
                }
                {
                    id 668
                    symbol "BCAN"
                    exchange "UQ"
                }
                {
                    id 669
                    symbol "BCAS"
                    exchange "UQ"
                }
                {
                    id 670
                    symbol "BCDS1"
                    exchange "UQ"
                }
                {
                    id 671
                    symbol "BCO"
                    exchange "UN"
                }
                {
                    id 672
                    symbol "BCOV"
                    exchange "UQ"
                }
                {
                    id 673
                    symbol "BCSA"
                    exchange "UQ"
                }
                {
                    id 674
                    symbol "BCSI"
                    exchange "UQ"
                }
                {
                    id 675
                    symbol "BCST"
                    exchange "UQ"
                }
                {
                    id 676
                    symbol "BCTI"
                    exchange "UQ"
                }
                {
                    id 677
                    symbol "BDC"
                    exchange "UN"
                }
                {
                    id 678
                    symbol "BDCO"
                    exchange "UQ"
                }
                {
                    id 679
                    symbol "BDE1"
                    exchange "UQ"
                }
                {
                    id 680
                    symbol "BDGPA"
                    exchange "UN"
                }
                {
                    id 681
                    symbol "BDI"
                    exchange "UN"
                }
                {
                    id 682
                    symbol "BDK"
                    exchange "UQ"
                }
                {
                    id 683
                    symbol "BDLN"
                    exchange "UQ"
                }
                {
                    id 684
                    symbol "BDLSQ"
                    exchange "UN"
                }
                {
                    id 685
                    symbol "BDMI"
                    exchange "UQ"
                }
                {
                    id 686
                    symbol "BDRL"
                    exchange "UN"
                }
                {
                    id 687
                    symbol "BE"
                    exchange "UN"
                }
                {
                    id 688
                    symbol "BEAS"
                    exchange "UQ"
                }
                {
                    id 689
                    symbol "BECN"
                    exchange "UQ"
                }
                {
                    id 690
                    symbol "BEEM"
                    exchange "UQ"
                }
                {
                    id 691
                    symbol "BEEP"
                    exchange "UN"
                }
                {
                    id 692
                    symbol "BEI1"
                    exchange "UN"
                }
                {
                    id 693
                    symbol "BEIQ"
                    exchange "UQ"
                }
                {
                    id 694
                    symbol "BELFA"
                    exchange "UQ"
                }
                {
                    id 695
                    symbol "BELM"
                    exchange "UQ"
                }
                {
                    id 696
                    symbol "BENE"
                    exchange "UQ"
                }
                {
                    id 697
                    symbol "BEOSZ"
                    exchange "UQ"
                }
                {
                    id 698
                    symbol "BEST"
                    exchange "UN"
                }
                {
                    id 699
                    symbol "BEST1"
                    exchange "UQ"
                }
                {
                    id 700
                    symbol "BET"
                    exchange "UN"
                }
                {
                    id 701
                    symbol "BEXP"
                    exchange "UQ"
                }
                {
                    id 702
                    symbol "BEZ"
                    exchange "UN"
                }
                {
                    id 703
                    symbol "BFAC"
                    exchange "UN"
                }
                {
                    id 704
                    symbol "BFI1"
                    exchange "UN"
                }
                {
                    id 705
                    symbol "BFRE1"
                    exchange "UQ"
                }
                {
                    id 706
                    symbol "BFUN"
                    exchange "UQ"
                }
                {
                    id 707
                    symbol "BFX1"
                    exchange "UN"
                }
                {
                    id 708
                    symbol "BGC2"
                    exchange "UN"
                }
                {
                    id 709
                    symbol "BGF"
                    exchange "UN"
                }
                {
                    id 710
                    symbol "BGGSQ"
                    exchange "UN"
                }
                {
                    id 711
                    symbol "BGH1"
                    exchange "UN"
                }
                {
                    id 712
                    symbol "BGPTQ"
                    exchange "UN"
                }
                {
                    id 713
                    symbol "BGRH"
                    exchange "UQ"
                }
                {
                    id 714
                    symbol "BGRY"
                    exchange "UQ"
                }
                {
                    id 715
                    symbol "BGSF"
                    exchange "UN"
                }
                {
                    id 716
                    symbol "BGSX"
                    exchange "UN"
                }
                {
                    id 717
                    symbol "BHAC"
                    exchange "UQ"
                }
                {
                    id 718
                    symbol "BHAC1"
                    exchange "UQ"
                }
                {
                    id 719
                    symbol "BHAG"
                    exchange "UQ"
                }
                {
                    id 720
                    symbol "BHE"
                    exchange "UN"
                }
                {
                    id 721
                    symbol "BHI"
                    exchange "UN"
                }
                {
                    id 722
                    symbol "BHODQ"
                    exchange "UN"
                }
                {
                    id 723
                    symbol "BIDZ"
                    exchange "UQ"
                }
                {
                    id 724
                    symbol "BIGC"
                    exchange "UQ"
                }
                {
                    id 725
                    symbol "BILL"
                    exchange "UN"
                }
                {
                    id 726
                    symbol "BIOS"
                    exchange "UQ"
                }
                {
                    id 727
                    symbol "BIOT"
                    exchange "UQ"
                }
                {
                    id 728
                    symbol "BIRT"
                    exchange "UQ"
                }
                {
                    id 729
                    symbol "BISA"
                    exchange "UQ"
                }
                {
                    id 730
                    symbol "BITS1"
                    exchange "UQ"
                }
                {
                    id 731
                    symbol "BIZZ1"
                    exchange "UQ"
                }
                {
                    id 732
                    symbol "BJS"
                    exchange "UN"
                }
                {
                    id 733
                    symbol "BKEP"
                    exchange "UQ"
                }
                {
                    id 734
                    symbol "BKHA"
                    exchange "UQ"
                }
                {
                    id 735
                    symbol "BKI"
                    exchange "UN"
                }
                {
                    id 736
                    symbol "BKKT"
                    exchange "UN"
                }
                {
                    id 737
                    symbol "BKNG"
                    exchange "UQ"
                }
                {
                    id 738
                    symbol "BKR"
                    exchange "UQ"
                }
                {
                    id 739
                    symbol "BKSY"
                    exchange "UN"
                }
                {
                    id 740
                    symbol "BKTI"
                    exchange "UN"
                }
                {
                    id 741
                    symbol "BKV"
                    exchange "UN"
                }
                {
                    id 742
                    symbol "BKYI"
                    exchange "UQ"
                }
                {
                    id 743
                    symbol "BL"
                    exchange "UQ"
                }
                {
                    id 744
                    symbol "BLAC"
                    exchange "UQ"
                }
                {
                    id 745
                    symbol "BLBX"
                    exchange "UQ"
                }
                {
                    id 746
                    symbol "BLD"
                    exchange "UN"
                }
                {
                    id 747
                    symbol "BLD1"
                    exchange "UN"
                }
                {
                    id 748
                    symbol "BLDE"
                    exchange "UQ"
                }
                {
                    id 749
                    symbol "BLDP"
                    exchange "UQ"
                }
                {
                    id 750
                    symbol "BLEU"
                    exchange "UQ"
                }
                {
                    id 751
                    symbol "BLIN"
                    exchange "UQ"
                }
                {
                    id 752
                    symbol "BLKB"
                    exchange "UQ"
                }
                {
                    id 753
                    symbol "BLND"
                    exchange "UN"
                }
                {
                    id 754
                    symbol "BLNG"
                    exchange "UQ"
                }
                {
                    id 755
                    symbol "BLNK"
                    exchange "UQ"
                }
                {
                    id 756
                    symbol "BLOG"
                    exchange "UQ"
                }
                {
                    id 757
                    symbol "BLOX"
                    exchange "UN"
                }
                {
                    id 758
                    symbol "BLPG1"
                    exchange "UQ"
                }
                {
                    id 759
                    symbol "BLSA"
                    exchange "UQ"
                }
                {
                    id 760
                    symbol "BLSW1"
                    exchange "UQ"
                }
                {
                    id 761
                    symbol "BLT"
                    exchange "UN"
                }
                {
                    id 762
                    symbol "BLTS"
                    exchange "UQ"
                }
                {
                    id 763
                    symbol "BLUAF"
                    exchange "UN"
                }
                {
                    id 764
                    symbol "BLUE1"
                    exchange "UQ"
                }
                {
                    id 765
                    symbol "BLVD"
                    exchange "UQ"
                }
                {
                    id 766
                    symbol "BLZE"
                    exchange "UQ"
                }
                {
                    id 767
                    symbol "BLZE1"
                    exchange "UQ"
                }
                {
                    id 768
                    symbol "BMAC"
                    exchange "UN"
                }
                {
                    id 769
                    symbol "BMAN"
                    exchange "UQ"
                }
                {
                    id 770
                    symbol "BMAQ"
                    exchange "UQ"
                }
                {
                    id 771
                    symbol "BMBL"
                    exchange "UQ"
                }
                {
                    id 772
                    symbol "BMC"
                    exchange "UQ"
                }
                {
                    id 773
                    symbol "BMI"
                    exchange "UN"
                }
                {
                    id 774
                    symbol "BMR"
                    exchange "UQ"
                }
                {
                    id 775
                    symbol "BMRQ"
                    exchange "UQ"
                }
                {
                    id 776
                    symbol "BMTM"
                    exchange "UQ"
                }
                {
                    id 777
                    symbol "BMTX"
                    exchange "UN"
                }
                {
                    id 778
                    symbol "BN1"
                    exchange "UQ"
                }
                {
                    id 779
                    symbol "BNAI"
                    exchange "UQ"
                }
                {
                    id 780
                    symbol "BNE1"
                    exchange "UQ"
                }
                {
                    id 781
                    symbol "BNFT"
                    exchange "UQ"
                }
                {
                    id 782
                    symbol "BNI"
                    exchange "UQ"
                }
                {
                    id 783
                    symbol "BNIX"
                    exchange "UQ"
                }
                {
                    id 784
                    symbol "BNNR"
                    exchange "UQ"
                }
                {
                    id 785
                    symbol "BNSOF"
                    exchange "UQ"
                }
                {
                    id 786
                    symbol "BNZI"
                    exchange "UQ"
                }
                {
                    id 787
                    symbol "BOAC"
                    exchange "UN"
                }
                {
                    id 788
                    symbol "BOBJY"
                    exchange "UQ"
                }
                {
                    id 789
                    symbol "BOCN"
                    exchange "UQ"
                }
                {
                    id 790
                    symbol "BOG"
                    exchange "UN"
                }
                {
                    id 791
                    symbol "BOLDQ"
                    exchange "UQ"
                }
                {
                    id 792
                    symbol "BOLT1"
                    exchange "UQ"
                }
                {
                    id 793
                    symbol "BOOL"
                    exchange "UQ"
                }
                {
                    id 794
                    symbol "BOOM"
                    exchange "UQ"
                }
                {
                    id 795
                    symbol "BOP"
                    exchange "UN"
                }
                {
                    id 796
                    symbol "BOR"
                    exchange "UN"
                }
                {
                    id 797
                    symbol "BORL"
                    exchange "UQ"
                }
                {
                    id 798
                    symbol "BORR"
                    exchange "UN"
                }
                {
                    id 799
                    symbol "BOSA"
                    exchange "UQ"
                }
                {
                    id 800
                    symbol "BOSC"
                    exchange "UQ"
                }
                {
                    id 801
                    symbol "BOWN"
                    exchange "UQ"
                }
                {
                    id 802
                    symbol "BOX"
                    exchange "UN"
                }
                {
                    id 803
                    symbol "BOX1"
                    exchange "UN"
                }
                {
                    id 804
                    symbol "BOXL"
                    exchange "UQ"
                }
                {
                    id 805
                    symbol "BOYD1"
                    exchange "UQ"
                }
                {
                    id 806
                    symbol "BP"
                    exchange "UN"
                }
                {
                    id 807
                    symbol "BPAC"
                    exchange "UQ"
                }
                {
                    id 808
                    symbol "BPAO"
                    exchange "UQ"
                }
                {
                    id 809
                    symbol "BPI.A"
                    exchange "UN"
                }
                {
                    id 810
                    symbol "BPIGF"
                    exchange "UN"
                }
                {
                    id 811
                    symbol "BPL"
                    exchange "UN"
                }
                {
                    id 812
                    symbol "BPMP"
                    exchange "UN"
                }
                {
                    id 813
                    symbol "BPOM"
                    exchange "UQ"
                }
                {
                    id 814
                    symbol "BPT"
                    exchange "UN"
                }
                {
                    id 815
                    symbol "BPTM"
                    exchange "UQ"
                }
                {
                    id 816
                    symbol "BPTR"
                    exchange "UQ"
                }
                {
                    id 817
                    symbol "BPZRQ"
                    exchange "UN"
                }
                {
                    id 818
                    symbol "BR"
                    exchange "UN"
                }
                {
                    id 819
                    symbol "BR1"
                    exchange "UN"
                }
                {
                    id 820
                    symbol "BRAC"
                    exchange "UQ"
                }
                {
                    id 821
                    symbol "BRANF"
                    exchange "UQ"
                }
                {
                    id 822
                    symbol "BRC"
                    exchange "UN"
                }
                {
                    id 823
                    symbol "BRCD"
                    exchange "UQ"
                }
                {
                    id 824
                    symbol "BRCM"
                    exchange "UQ"
                }
                {
                    id 825
                    symbol "BRD"
                    exchange "UN"
                }
                {
                    id 826
                    symbol "BRDG1"
                    exchange "UQ"
                }
                {
                    id 827
                    symbol "BRDR"
                    exchange "UQ"
                }
                {
                    id 828
                    symbol "BRDSQ"
                    exchange "UN"
                }
                {
                    id 829
                    symbol "BREK"
                    exchange "UQ"
                }
                {
                    id 830
                    symbol "BREZ"
                    exchange "UQ"
                }
                {
                    id 831
                    symbol "BRIO"
                    exchange "UQ"
                }
                {
                    id 832
                    symbol "BRIV"
                    exchange "UQ"
                }
                {
                    id 833
                    symbol "BRKC1"
                    exchange "UQ"
                }
                {
                    id 834
                    symbol "BRKH"
                    exchange "UQ"
                }
                {
                    id 835
                    symbol "BRKT"
                    exchange "UQ"
                }
                {
                    id 836
                    symbol "BRLCQ"
                    exchange "UQ"
                }
                {
                    id 837
                    symbol "BRLS1"
                    exchange "UQ"
                }
                {
                    id 838
                    symbol "BRN"
                    exchange "UN"
                }
                {
                    id 839
                    symbol "BRNC"
                    exchange "UQ"
                }
                {
                    id 840
                    symbol "BRNC1"
                    exchange "UQ"
                }
                {
                    id 841
                    symbol "BROD1"
                    exchange "UQ"
                }
                {
                    id 842
                    symbol "BROG"
                    exchange "UQ"
                }
                {
                    id 843
                    symbol "BRQSF"
                    exchange "UQ"
                }
                {
                    id 844
                    symbol "BRR"
                    exchange "UN"
                }
                {
                    id 845
                    symbol "BRR1"
                    exchange "UN"
                }
                {
                    id 846
                    symbol "BRSS"
                    exchange "UN"
                }
                {
                    id 847
                    symbol "BRST1"
                    exchange "UQ"
                }
                {
                    id 848
                    symbol "BRSWQ"
                    exchange "UN"
                }
                {
                    id 849
                    symbol "BRY"
                    exchange "UQ"
                }
                {
                    id 850
                    symbol "BRY1"
                    exchange "UN"
                }
                {
                    id 851
                    symbol "BRZE"
                    exchange "UQ"
                }
                {
                    id 852
                    symbol "BSFT"
                    exchange "UQ"
                }
                {
                    id 853
                    symbol "BSIIU"
                    exchange "UQ"
                }
                {
                    id 854
                    symbol "BSKY"
                    exchange "UQ"
                }
                {
                    id 855
                    symbol "BSM"
                    exchange "UN"
                }
                {
                    id 856
                    symbol "BSNX"
                    exchange "UQ"
                }
                {
                    id 857
                    symbol "BSQR"
                    exchange "UQ"
                }
                {
                    id 858
                    symbol "BSTW"
                    exchange "UQ"
                }
                {
                    id 859
                    symbol "BSY"
                    exchange "UQ"
                }
                {
                    id 860
                    symbol "BTAQ"
                    exchange "UQ"
                }
                {
                    id 861
                    symbol "BTC1"
                    exchange "UN"
                }
                {
                    id 862
                    symbol "BTCM"
                    exchange "UN"
                }
                {
                    id 863
                    symbol "BTDR"
                    exchange "UQ"
                }
                {
                    id 864
                    symbol "BTE"
                    exchange "UN"
                }
                {
                    id 865
                    symbol "BTF1"
                    exchange "UN"
                }
                {
                    id 866
                    symbol "BTGI"
                    exchange "UQ"
                }
                {
                    id 867
                    symbol "BTGL"
                    exchange "UQ"
                }
                {
                    id 868
                    symbol "BTH"
                    exchange "UN"
                }
                {
                    id 869
                    symbol "BTHS"
                    exchange "UQ"
                }
                {
                    id 870
                    symbol "BTIC"
                    exchange "UQ"
                }
                {
                    id 871
                    symbol "BTOC"
                    exchange "UQ"
                }
                {
                    id 872
                    symbol "BTRS"
                    exchange "UQ"
                }
                {
                    id 873
                    symbol "BTSR"
                    exchange "UQ"
                }
                {
                    id 874
                    symbol "BTUI"
                    exchange "UQ"
                }
                {
                    id 875
                    symbol "BUCY"
                    exchange "UQ"
                }
                {
                    id 876
                    symbol "BUJA"
                    exchange "UQ"
                }
                {
                    id 877
                    symbol "BURU"
                    exchange "UN"
                }
                {
                    id 878
                    symbol "BUSY"
                    exchange "UQ"
                }
                {
                    id 879
                    symbol "BUTLQ"
                    exchange "UQ"
                }
                {
                    id 880
                    symbol "BV"
                    exchange "UN"
                }
                {
                    id 881
                    symbol "BV1"
                    exchange "UQ"
                }
                {
                    id 882
                    symbol "BVEW"
                    exchange "UQ"
                }
                {
                    id 883
                    symbol "BVSI"
                    exchange "UQ"
                }
                {
                    id 884
                    symbol "BVSN"
                    exchange "UQ"
                }
                {
                    id 885
                    symbol "BW"
                    exchange "UN"
                }
                {
                    id 886
                    symbol "BWAC"
                    exchange "UQ"
                }
                {
                    id 887
                    symbol "BWAY1"
                    exchange "UQ"
                }
                {
                    id 888
                    symbol "BWC"
                    exchange "UQ"
                }
                {
                    id 889
                    symbol "BWC1"
                    exchange "UN"
                }
                {
                    id 890
                    symbol "BWEBF"
                    exchange "UQ"
                }
                {
                    id 891
                    symbol "BWEN"
                    exchange "UQ"
                }
                {
                    id 892
                    symbol "BWLP"
                    exchange "UN"
                }
                {
                    id 893
                    symbol "BWMN"
                    exchange "UQ"
                }
                {
                    id 894
                    symbol "BWOWF"
                    exchange "UQ"
                }
                {
                    id 895
                    symbol "BWP"
                    exchange "UN"
                }
                {
                    id 896
                    symbol "BWSI"
                    exchange "UQ"
                }
                {
                    id 897
                    symbol "BWXT"
                    exchange "UN"
                }
                {
                    id 898
                    symbol "BXC"
                    exchange "UN"
                }
                {
                    id 899
                    symbol "BXEFF"
                    exchange "UN"
                }
                {
                    id 900
                    symbol "BYI"
                    exchange "UN"
                }
                {
                    id 901
                    symbol "BYNDQ"
                    exchange "UQ"
                }
                {
                    id 902
                    symbol "BYNO"
                    exchange "UQ"
                }
                {
                    id 903
                    symbol "BYRN"
                    exchange "UQ"
                }
                {
                    id 904
                    symbol "BZ"
                    exchange "UQ"
                }
                {
                    id 905
                    symbol "BZC"
                    exchange "UN"
                }
                {
                    id 906
                    symbol "CA1"
                    exchange "UQ"
                }
                {
                    id 907
                    symbol "CAAP"
                    exchange "UN"
                }
                {
                    id 908
                    symbol "CAB1"
                    exchange "UN"
                }
                {
                    id 909
                    symbol "CACGU"
                    exchange "UQ"
                }
                {
                    id 910
                    symbol "CACI"
                    exchange "UN"
                }
                {
                    id 911
                    symbol "CACS"
                    exchange "UQ"
                }
                {
                    id 912
                    symbol "CADA"
                    exchange "UQ"
                }
                {
                    id 913
                    symbol "CADE2"
                    exchange "UQ"
                }
                {
                    id 914
                    symbol "CAE"
                    exchange "UN"
                }
                {
                    id 915
                    symbol "CAER"
                    exchange "UQ"
                }
                {
                    id 916
                    symbol "CAI"
                    exchange "UN"
                }
                {
                    id 917
                    symbol "CAII"
                    exchange "UQ"
                }
                {
                    id 918
                    symbol "CAIR"
                    exchange "UQ"
                }
                {
                    id 919
                    symbol "CAIS"
                    exchange "UQ"
                }
                {
                    id 920
                    symbol "CAJPY"
                    exchange "UN"
                }
                {
                    id 921
                    symbol "CAL1"
                    exchange "UN"
                }
                {
                    id 922
                    symbol "CALAQ"
                    exchange "UQ"
                }
                {
                    id 923
                    symbol "CALD"
                    exchange "UQ"
                }
                {
                    id 924
                    symbol "CALX"
                    exchange "UN"
                }
                {
                    id 925
                    symbol "CAM"
                    exchange "UN"
                }
                {
                    id 926
                    symbol "CAM1"
                    exchange "UN"
                }
                {
                    id 927
                    symbol "CAMB"
                    exchange "UQ"
                }
                {
                    id 928
                    symbol "CAMBA"
                    exchange "UQ"
                }
                {
                    id 929
                    symbol "CAMD"
                    exchange "UQ"
                }
                {
                    id 930
                    symbol "CAMPQ"
                    exchange "UQ"
                }
                {
                    id 931
                    symbol "CAMT"
                    exchange "UQ"
                }
                {
                    id 932
                    symbol "CAMZ"
                    exchange "UQ"
                }
                {
                    id 933
                    symbol "CAN"
                    exchange "UQ"
                }
                {
                    id 934
                    symbol "CANI"
                    exchange "UQ"
                }
                {
                    id 935
                    symbol "CANOQ1"
                    exchange "UN"
                }
                {
                    id 936
                    symbol "CANR1"
                    exchange "UQ"
                }
                {
                    id 937
                    symbol "CANRQ"
                    exchange "UN"
                }
                {
                    id 938
                    symbol "CAPA1"
                    exchange "UQ"
                }
                {
                    id 939
                    symbol "CAPI"
                    exchange "UQ"
                }
                {
                    id 940
                    symbol "CAPL"
                    exchange "UN"
                }
                {
                    id 941
                    symbol "CAPNU"
                    exchange "UQ"
                }
                {
                    id 942
                    symbol "CAPT"
                    exchange "UQ"
                }
                {
                    id 943
                    symbol "CAR"
                    exchange "UQ"
                }
                {
                    id 944
                    symbol "CARB"
                    exchange "UQ"
                }
                {
                    id 945
                    symbol "CARD1"
                    exchange "UQ"
                }
                {
                    id 946
                    symbol "CARE1"
                    exchange "UQ"
                }
                {
                    id 947
                    symbol "CARI"
                    exchange "UQ"
                }
                {
                    id 948
                    symbol "CARL1"
                    exchange "UQ"
                }
                {
                    id 949
                    symbol "CAS"
                    exchange "UN"
                }
                {
                    id 950
                    symbol "CASC1"
                    exchange "UN"
                }
                {
                    id 951
                    symbol "CASS"
                    exchange "UQ"
                }
                {
                    id 952
                    symbol "CASSQ"
                    exchange "UQ"
                }
                {
                    id 953
                    symbol "CAST1"
                    exchange "UQ"
                }
                {
                    id 954
                    symbol "CAT"
                    exchange "UN"
                }
                {
                    id 955
                    symbol "CATM"
                    exchange "UQ"
                }
                {
                    id 956
                    symbol "CATP"
                    exchange "UQ"
                }
                {
                    id 957
                    symbol "CATS1"
                    exchange "UQ"
                }
                {
                    id 958
                    symbol "CATT"
                    exchange "UQ"
                }
                {
                    id 959
                    symbol "CATX1"
                    exchange "UQ"
                }
                {
                    id 960
                    symbol "CATZ"
                    exchange "UQ"
                }
                {
                    id 961
                    symbol "CAUD"
                    exchange "UQ"
                }
                {
                    id 962
                    symbol "CAVM"
                    exchange "UQ"
                }
                {
                    id 963
                    symbol "CAVN"
                    exchange "UQ"
                }
                {
                    id 964
                    symbol "CAVO"
                    exchange "UQ"
                }
                {
                    id 965
                    symbol "CAYN"
                    exchange "UQ"
                }
                {
                    id 966
                    symbol "CBAT"
                    exchange "UQ"
                }
                {
                    id 967
                    symbol "CBE"
                    exchange "UN"
                }
                {
                    id 968
                    symbol "CBEH"
                    exchange "UQ"
                }
                {
                    id 969
                    symbol "CBI"
                    exchange "UN"
                }
                {
                    id 970
                    symbol "CBIS1"
                    exchange "UQ"
                }
                {
                    id 971
                    symbol "CBLK"
                    exchange "UQ"
                }
                {
                    id 972
                    symbol "CBLT"
                    exchange "UQ"
                }
                {
                    id 973
                    symbol "CBNRQ"
                    exchange "UN"
                }
                {
                    id 974
                    symbol "CBRG"
                    exchange "UQ"
                }
                {
                    id 975
                    symbol "CBRI"
                    exchange "UN"
                }
                {
                    id 976
                    symbol "CBXC"
                    exchange "UQ"
                }
                {
                    id 977
                    symbol "CBZ"
                    exchange "UN"
                }
                {
                    id 978
                    symbol "CBZ2"
                    exchange "UN"
                }
                {
                    id 979
                    symbol "CCA1"
                    exchange "UN"
                }
                {
                    id 980
                    symbol "CCAI"
                    exchange "UQ"
                }
                {
                    id 981
                    symbol "CCAR"
                    exchange "UQ"
                }
                {
                    id 982
                    symbol "CCBL"
                    exchange "UQ"
                }
                {
                    id 983
                    symbol "CCCS"
                    exchange "UQ"
                }
                {
                    id 984
                    symbol "CCEC"
                    exchange "UQ"
                }
                {
                    id 985
                    symbol "CCGM"
                    exchange "UQ"
                }
                {
                    id 986
                    symbol "CCIX"
                    exchange "UQ"
                }
                {
                    id 987
                    symbol "CCIX2"
                    exchange "UQ"
                }
                {
                    id 988
                    symbol "CCL"
                    exchange "UN"
                }
                {
                    id 989
                    symbol "CCLN"
                    exchange "UQ"
                }
                {
                    id 990
                    symbol "CCLP"
                    exchange "UQ"
                }
                {
                    id 991
                    symbol "CCMP"
                    exchange "UQ"
                }
                {
                    id 992
                    symbol "CCMTF"
                    exchange "UN"
                }
                {
                    id 993
                    symbol "CCN"
                    exchange "UQ"
                }
                {
                    id 994
                    symbol "CCRC"
                    exchange "UQ"
                }
                {
                    id 995
                    symbol "CCRD"
                    exchange "UN"
                }
                {
                    id 996
                    symbol "CCRD1"
                    exchange "UQ"
                }
                {
                    id 997
                    symbol "CCSC1"
                    exchange "UQ"
                }
                {
                    id 998
                    symbol "CCSI"
                    exchange "UQ"
                }
                {
                    id 999
                    symbol "CCTG"
                    exchange "UQ"
                }
                {
                    id 1000
                    symbol "CCTS"
                    exchange "UQ"
                }
                {
                    id 1001
                    symbol "CCTX"
                    exchange "UQ"
                }
                {
                    id 1002
                    symbol "CCUR"
                    exchange "UQ"
                }
                {
                    id 1003
                    symbol "CCV"
                    exchange "UN"
                }
                {
                    id 1004
                    symbol "CCVI"
                    exchange "UN"
                }
                {
                    id 1005
                    symbol "CD"
                    exchange "UQ"
                }
                {
                    id 1006
                    symbol "CDAQ"
                    exchange "UQ"
                }
                {
                    id 1007
                    symbol "CDCAQ"
                    exchange "UQ"
                }
                {
                    id 1008
                    symbol "CDCM"
                    exchange "UQ"
                }
                {
                    id 1009
                    symbol "CDCO1"
                    exchange "UQ"
                }
                {
                    id 1010
                    symbol "CDCSY"
                    exchange "UQ"
                }
                {
                    id 1011
                    symbol "CDCY"
                    exchange "UQ"
                }
                {
                    id 1012
                    symbol "CDD"
                    exchange "UN"
                }
                {
                    id 1013
                    symbol "CDDDQ"
                    exchange "UQ"
                }
                {
                    id 1014
                    symbol "CDDT"
                    exchange "UN"
                }
                {
                    id 1015
                    symbol "CDG"
                    exchange "UN"
                }
                {
                    id 1016
                    symbol "CDI"
                    exchange "UN"
                }
                {
                    id 1017
                    symbol "CDIIQ"
                    exchange "UQ"
                }
                {
                    id 1018
                    symbol "CDK"
                    exchange "UQ"
                }
                {
                    id 1019
                    symbol "CDLR"
                    exchange "UN"
                }
                {
                    id 1020
                    symbol "CDMS"
                    exchange "UQ"
                }
                {
                    id 1021
                    symbol "CDNS"
                    exchange "UQ"
                }
                {
                    id 1022
                    symbol "CDOT"
                    exchange "UQ"
                }
                {
                    id 1023
                    symbol "CDRBQ"
                    exchange "UQ"
                }
                {
                    id 1024
                    symbol "CDRE"
                    exchange "UN"
                }
                {
                    id 1025
                    symbol "CDS2"
                    exchange "UN"
                }
                {
                    id 1026
                    symbol "CDSC"
                    exchange "UQ"
                }
            ]
        }
    }
}
test RandomCompaniesTickerMatchTest {
    functions [AddTickersToCompanies]
    args {
        company_list {
            companies [
                {
                    id 0
                    name "Atgenomix SeqsLab"
                    ticker null
                    description "Atgenomix SeqsLab is a Spark-native platform designed to address the challenges of health omics data analysis."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 1
                    name "NTT"
                    ticker null
                    description "NTT is a data center operator."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 2
                    name "Stack Infrastructure"
                    ticker null
                    description "A company that develops and operates data centers."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 3
                    name "Zoomlion"
                    ticker null
                    description "Zoomlion is a company that showcases robotics innovations at World Robot Conference."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 4
                    name "Terabeam"
                    ticker null
                    description "Terabeam is a company."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 5
                    name "Samsung"
                    ticker null
                    description "Samsung is a multinational conglomerate company with a wide range of businesses, including electronics, semiconductors, and telecommunications."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 6
                    name "Cipher Mining Inc."
                    ticker null
                    description "Cipher Mining Inc. is a company focused on cryptocurrency mining."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 7
                    name "Prometheus Hyperscale"
                    ticker null
                    description "Prometheus Hyperscale is a data center firm."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 8
                    name "Diversified"
                    ticker null
                    description "Company that produces Geo Week."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 9
                    name "Flex"
                    ticker null
                    description "Flex is a company that announces new AI infrastructure platform to speed deployment by up to 30 percent."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 10
                    name "NVIDIA"
                    ticker null
                    description "NVIDIA is a technology company that designs graphics processing units (GPUs)."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 11
                    name "Cardinal Kinetic"
                    ticker null
                    description "Cardinal Kinetic is a company that develops motion control solutions."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 12
                    name "MUFG"
                    ticker null
                    description "MUFG is a Japanese financial institution."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 13
                    name "TSMC"
                    ticker null
                    description "Taiwan Semiconductor Manufacturing Company (TSMC) is a semiconductor foundry."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 14
                    name "Equinix, Inc."
                    ticker null
                    description "Equinix, Inc. is a global digital infrastructure company that provides data center and interconnection services."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 15
                    name "Cisco Systems, Inc."
                    ticker null
                    description "Cisco Systems, Inc. is a networking hardware and software company."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 16
                    name "Murata Manufacturing Co., Ltd."
                    ticker null
                    description "Murata Manufacturing is a Japanese manufacturer of electronic components."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 17
                    name "Sprint"
                    ticker null
                    description "Sprint Corporation was a telecommunications company providing wireless services and internet access."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 18
                    name "CIMIC"
                    ticker null
                    description "CIMIC is a construction company."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
                {
                    id 19
                    name "Pelagian"
                    ticker null
                    description "Pelagian is a company."
                    website_url null
                    headquarters_location null
                    revenue_usd null
                    employees null
                    founded_year null
                    ceo null
                    linkedin_url null
                    source_ids null
                    source_uuids null
                }
            ]
        }
        ticker_list {
            tickers [
                {
                    id 0
                    symbol "MSFT"
                    exchange null
                }
                {
                    id 1
                    symbol "NVDA"
                    exchange null
                }
                {
                    id 2
                    symbol "AAPL"
                    exchange null
                }
                {
                    id 3
                    symbol "AMZN"
                    exchange null
                }
                {
                    id 4
                    symbol "GOOGL"
                    exchange null
                }
                {
                    id 5
                    symbol "META"
                    exchange null
                }
                {
                    id 6
                    symbol "TSLA"
                    exchange null
                }
                {
                    id 7
                    symbol "AVGO"
                    exchange null
                }
                {
                    id 8
                    symbol "BRK-B"
                    exchange null
                }
                {
                    id 9
                    symbol "WMT"
                    exchange null
                }
                {
                    id 10
                    symbol "JPM"
                    exchange null
                }
                {
                    id 11
                    symbol "V"
                    exchange null
                }
                {
                    id 12
                    symbol "LLY"
                    exchange null
                }
                {
                    id 13
                    symbol "SPY"
                    exchange null
                }
                {
                    id 14
                    symbol "MA"
                    exchange null
                }
                {
                    id 15
                    symbol "NFLX"
                    exchange null
                }
                {
                    id 16
                    symbol "COST"
                    exchange null
                }
                {
                    id 17
                    symbol "ORCL"
                    exchange null
                }
                {
                    id 18
                    symbol "XOM"
                    exchange null
                }
                {
                    id 19
                    symbol "PG"
                    exchange null
                }
                {
                    id 20
                    symbol "JNJ"
                    exchange null
                }
                {
                    id 21
                    symbol "HD"
                    exchange null
                }
                {
                    id 22
                    symbol "SAP"
                    exchange null
                }
                {
                    id 23
                    symbol "BAC"
                    exchange null
                }
                {
                    id 24
                    symbol "ABBV"
                    exchange null
                }
                {
                    id 25
                    symbol "NVO"
                    exchange null
                }
                {
                    id 26
                    symbol "KO"
                    exchange null
                }
                {
                    id 27
                    symbol "PLTR"
                    exchange null
                }
                {
                    id 28
                    symbol "ASML"
                    exchange null
                }
                {
                    id 29
                    symbol "PM"
                    exchange null
                }
                {
                    id 30
                    symbol "BABA"
                    exchange null
                }
                {
                    id 31
                    symbol "TMUS"
                    exchange null
                }
                {
                    id 32
                    symbol "UNH"
                    exchange null
                }
                {
                    id 33
                    symbol "GE"
                    exchange null
                }
                {
                    id 34
                    symbol "CRM"
                    exchange null
                }
                {
                    id 35
                    symbol "TM"
                    exchange null
                }
                {
                    id 36
                    symbol "CSCO"
                    exchange null
                }
                {
                    id 37
                    symbol "WFC"
                    exchange null
                }
                {
                    id 38
                    symbol "IBM"
                    exchange null
                }
                {
                    id 39
                    symbol "CVX"
                    exchange null
                }
                {
                    id 40
                    symbol "ABT"
                    exchange null
                }
                {
                    id 41
                    symbol "NVS"
                    exchange null
                }
                {
                    id 42
                    symbol "AZN"
                    exchange null
                }
                {
                    id 43
                    symbol "MCD"
                    exchange null
                }
                {
                    id 44
                    symbol "LIN"
                    exchange null
                }
                {
                    id 45
                    symbol "INTU"
                    exchange null
                }
                {
                    id 46
                    symbol "NOW"
                    exchange null
                }
                {
                    id 47
                    symbol "HSBC"
                    exchange null
                }
                {
                    id 48
                    symbol "AXP"
                    exchange null
                }
                {
                    id 49
                    symbol "MS"
                    exchange null
                }
                {
                    id 50
                    symbol "QQQ"
                    exchange null
                }
                {
                    id 51
                    symbol "DIS"
                    exchange null
                }
                {
                    id 52
                    symbol "T"
                    exchange null
                }
                {
                    id 53
                    symbol "ISRG"
                    exchange null
                }
                {
                    id 54
                    symbol "ACN"
                    exchange null
                }
                {
                    id 55
                    symbol "SHEL"
                    exchange null
                }
                {
                    id 56
                    symbol "MRK"
                    exchange null
                }
                {
                    id 57
                    symbol "HDB"
                    exchange null
                }
                {
                    id 58
                    symbol "FMX"
                    exchange null
                }
                {
                    id 59
                    symbol "VZ"
                    exchange null
                }
                {
                    id 60
                    symbol "GS"
                    exchange null
                }
                {
                    id 61
                    symbol "RTX"
                    exchange null
                }
                {
                    id 62
                    symbol "PEP"
                    exchange null
                }
                {
                    id 63
                    symbol "RY"
                    exchange null
                }
                {
                    id 64
                    symbol "BKNG"
                    exchange null
                }
                {
                    id 65
                    symbol "AMD"
                    exchange null
                }
                {
                    id 66
                    symbol "ADBE"
                    exchange null
                }
                {
                    id 67
                    symbol "UBER"
                    exchange null
                }
                {
                    id 68
                    symbol "BX"
                    exchange null
                }
                {
                    id 69
                    symbol "PGR"
                    exchange null
                }
                {
                    id 70
                    symbol "CAT"
                    exchange null
                }
                {
                    id 71
                    symbol "TXN"
                    exchange null
                }
                {
                    id 72
                    symbol "MUFG"
                    exchange null
                }
                {
                    id 73
                    symbol "SONY"
                    exchange null
                }
                {
                    id 74
                    symbol "SCHW"
                    exchange null
                }
                {
                    id 75
                    symbol "QCOM"
                    exchange null
                }
                {
                    id 76
                    symbol "SPGI"
                    exchange null
                }
                {
                    id 77
                    symbol "UL"
                    exchange null
                }
                {
                    id 78
                    symbol "BA"
                    exchange null
                }
                {
                    id 79
                    symbol "BSX"
                    exchange null
                }
                {
                    id 80
                    symbol "AMGN"
                    exchange null
                }
                {
                    id 81
                    symbol "TMO"
                    exchange null
                }
                {
                    id 82
                    symbol "BLK"
                    exchange null
                }
                {
                    id 83
                    symbol "SYK"
                    exchange null
                }
                {
                    id 84
                    symbol "HON"
                    exchange null
                }
                {
                    id 85
                    symbol "NEE"
                    exchange null
                }
                {
                    id 86
                    symbol "TJX"
                    exchange null
                }
                {
                    id 87
                    symbol "C"
                    exchange null
                }
                {
                    id 88
                    symbol "DE"
                    exchange null
                }
                {
                    id 89
                    symbol "PDD"
                    exchange null
                }
                {
                    id 90
                    symbol "GILD"
                    exchange null
                }
                {
                    id 91
                    symbol "BUD"
                    exchange null
                }
                {
                    id 92
                    symbol "SHOP"
                    exchange null
                }
                {
                    id 93
                    symbol "DHR"
                    exchange null
                }
                {
                    id 94
                    symbol "SPOT"
                    exchange null
                }
                {
                    id 95
                    symbol "PFE"
                    exchange null
                }
                {
                    id 96
                    symbol "UNP"
                    exchange null
                }
                {
                    id 97
                    symbol "ADP"
                    exchange null
                }
                {
                    id 98
                    symbol "ARM"
                    exchange null
                }
                {
                    id 99
                    symbol "MELI"
                    exchange null
                }
            ]
        }
    }
}