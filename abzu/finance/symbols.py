"Exchange suffix to exchange mapping for financial symbols."

# Note: Some data providers use different conventions Bloomberg uses different suffixes than
# Reuters/Refinitiv. Yahoo Finance often uses different conventions as well


# Define known exchange suffixes for validation
EXCHANGE_SUFFIX_MAP = {
    # United States
    "O": "NASDAQ",  # NASDAQ (Reuters convention)
    "Q": "NASDAQ",  # NASDAQ (alternative)
    "N": "NYSE",  # New York Stock Exchange
    "A": "AMEX",  # NYSE American (formerly AMEX)
    "P": "ARCA",  # NYSE Arca
    "Z": "BATS",  # BATS Exchange
    "K": "OTC",  # OTC Markets
    "OB": "OTCBB",  # OTC Bulletin Board
    "PK": "OTCPK",  # OTC Pink Sheets
    # Canada
    "TO": "TSX",  # Toronto Stock Exchange
    "V": "TSXV",  # TSX Venture Exchange
    "CN": "CSE",  # Canadian Securities Exchange
    "NE": "NEO",  # NEO Exchange
    # United Kingdom & Ireland
    "L": "LSE",  # London Stock Exchange
    "LON": "LSE",  # London Stock Exchange (alternative)
    "IL": "ISEQ",  # Irish Stock Exchange (Euronext Dublin)
    "DUB": "ISEQ",  # Irish Stock Exchange (alternative)
    # Europe - Major Markets
    "PA": "EPA",  # Euronext Paris
    "AS": "AMS",  # Euronext Amsterdam
    "BR": "EBR",  # Euronext Brussels
    "LS": "ELI",  # Euronext Lisbon
    "MI": "MIL",  # Borsa Italiana (Milan)
    "MC": "MCE",  # Madrid Stock Exchange
    "DE": "XETRA",  # XETRA (Deutsche Börse)
    "F": "FRA",  # Frankfurt Stock Exchange
    "BE": "BER",  # Berlin Stock Exchange
    # Two values for DU, usign Dubai Stock Exchange (see below)
    # "DU": "DUS",  # Düsseldorf Stock Exchange
    "HA": "HAM",  # Hamburg Stock Exchange
    "HM": "HAN",  # Hanover Stock Exchange
    "MU": "MUN",  # Munich Stock Exchange
    "SG": "STU",  # Stuttgart Stock Exchange
    "SW": "SWX",  # SIX Swiss Exchange
    "S": "SWX",  # SIX Swiss Exchange (alternative)
    "VX": "VTX",  # SIX Swiss Exchange (third alternative)
    "CO": "CPH",  # Nasdaq Copenhagen
    "ST": "STO",  # Nasdaq Stockholm
    "HE": "HEL",  # Nasdaq Helsinki
    "IC": "ICE",  # Nasdaq Iceland
    "OL": "OSL",  # Oslo Stock Exchange
    "VS": "VSE",  # Vienna Stock Exchange
    "PR": "PRA",  # Prague Stock Exchange
    "WA": "WSE",  # Warsaw Stock Exchange
    "BD": "BUD",  # Budapest Stock Exchange
    "BU": "BUC",  # Bucharest Stock Exchange
    "AT": "ATH",  # Athens Stock Exchange
    "IS": "IST",  # Borsa Istanbul
    # Asia - China & Hong Kong
    "HK": "HKEX",  # Hong Kong Exchange
    "SS": "SSE",  # Shanghai Stock Exchange
    "SZ": "SZSE",  # Shenzhen Stock Exchange
    "SH": "SSE",  # Shanghai Stock Exchange (alternative)
    # Asia - Japan
    "T": "TSE",  # Tokyo Stock Exchange
    "TYO": "TSE",  # Tokyo Stock Exchange (alternative)
    "OS": "OSE",  # Osaka Exchange
    "NK": "NSE",  # Nagoya Stock Exchange
    "SP": "SSE",  # Sapporo Securities Exchange
    "FS": "FSE",  # Fukuoka Stock Exchange
    # Asia - South Korea
    "KS": "KOSPI",  # Korea Exchange (KOSPI)
    "KQ": "KOSDAQ",  # Korea Exchange (KOSDAQ)
    # Asia - India
    "NS": "NSE",  # National Stock Exchange of India
    "BO": "BSE",  # Bombay Stock Exchange
    # Asia - Other Markets
    "SI": "SGX",  # Singapore Exchange
    "TW": "TWSE",  # Taiwan Stock Exchange
    "TWO": "TPE",  # Taipei Exchange
    "TB": "TFEX",  # Thailand Futures Exchange
    "BK": "SET",  # Stock Exchange of Thailand
    "KL": "KLSE",  # Bursa Malaysia
    "JK": "IDX",  # Indonesia Stock Exchange
    "PS": "PSE",  # Philippine Stock Exchange
    "VN": "HOSE",  # Ho Chi Minh Stock Exchange
    "HN": "HNX",  # Hanoi Stock Exchange
    "CM": "CSE",  # Colombo Stock Exchange
    "KA": "KSE",  # Pakistan Stock Exchange
    "DSE": "DSE",  # Dhaka Stock Exchange
    # Oceania
    "AX": "ASX",  # Australian Securities Exchange
    "NZ": "NZX",  # New Zealand Exchange
    # Middle East
    "TA": "TASE",  # Tel Aviv Stock Exchange
    "TLV": "TASE",  # Tel Aviv Stock Exchange (alternative)
    "AB": "ADX",  # Abu Dhabi Securities Exchange
    "DU": "DFM",  # Dubai Financial Market
    "QA": "QSE",  # Qatar Stock Exchange
    "SR": "TADAWUL",  # Saudi Stock Exchange (Tadawul)
    "KW": "KSE",  # Kuwait Stock Exchange
    "BH": "BSE",  # Bahrain Bourse
    "OM": "MSM",  # Muscat Securities Market
    "AM": "ASE",  # Amman Stock Exchange
    "CA": "EGX",  # Egyptian Exchange
    # Africa
    "JO": "JSE",  # Johannesburg Stock Exchange
    "CAS": "CASE",  # Casablanca Stock Exchange
    "NBO": "NSE",  # Nairobi Securities Exchange
    "NASE": "NASE",  # Nigerian Stock Exchange
    "DSM": "DSE",  # Dar es Salaam Stock Exchange
    "LUS": "LUSE",  # Lusaka Stock Exchange
    "ZSE": "ZSE",  # Zimbabwe Stock Exchange
    "BRVM": "BRVM",  # Bourse Régionale des Valeurs Mobilières
    # Latin America
    "MX": "BMV",  # Mexican Stock Exchange
    "BVMF": "B3",  # B3 (Brasil Bolsa Balcão)
    "SA": "B3",  # B3 (alternative)
    "SN": "BCS",  # Santiago Stock Exchange
    "BA": "BCBA",  # Buenos Aires Stock Exchange
    "LM": "BVL",  # Lima Stock Exchange
    "CR": "BVC",  # Colombia Stock Exchange
    "CCS": "BVCV",  # Caracas Stock Exchange
    # Cryptocurrency/Digital (increasingly common)
    "CC": "CRYPTO",  # Generic cryptocurrency
    "COIN": "CRYPTO",  # Alternative cryptocurrency
    # Commodities/Futures
    "CBT": "CBOT",  # Chicago Board of Trade
    "CME": "CME",  # Chicago Mercantile Exchange
    "NYM": "NYMEX",  # New York Mercantile Exchange
    "CMX": "COMEX",  # Commodity Exchange
    "ICE": "ICE",  # Intercontinental Exchange
    "LME": "LME",  # London Metal Exchange
}
