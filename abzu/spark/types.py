import pyspark.sql.types as T

author_type = T.StructType(
    [
        T.StructField("name", T.StringType(), nullable=False),
        T.StructField("profile_url", T.StringType(), nullable=True),
    ]
)

ticker_type = T.StructType(
    [
        T.StructField("name", T.StringType(), nullable=False),
        T.StructField("symbol", T.StringType(), nullable=False),
        T.StructField("exchange", T.StringType(), nullable=True),
    ]
)

company_type = T.StructType(
    [
        T.StructField("name", T.StringType(), nullable=False),
        T.StructField("ticker", ticker_type, nullable=True),
        T.StructField("description", T.StringType(), nullable=False),
        T.StructField("website_url", T.StringType(), nullable=True),
        T.StructField("headquarters_location", T.StringType(), nullable=True),
        T.StructField("revenue_usd", T.IntegerType(), nullable=True),
        T.StructField("employees", T.IntegerType(), nullable=True),
        T.StructField("founded_year", T.IntegerType(), nullable=True),
        T.StructField("ceo", T.StringType(), nullable=True),
        T.StructField("linkedin_url", T.StringType(), nullable=True),
    ]
)

product_type = T.StructType(
    [
        T.StructField("name", T.StringType(), nullable=False),
        T.StructField("company", company_type, nullable=False),
        T.StructField("description", T.StringType(), nullable=False),
    ]
)

technology_type = T.StructType(
    [
        T.StructField("name", T.StringType(), nullable=False),
        T.StructField("developer", company_type, nullable=False),
        T.StructField("description", T.StringType(), nullable=False),
    ]
)

partnership_type = T.StructType(
    [
        T.StructField("src_company", company_type, nullable=False),
        T.StructField("dst_company", company_type, nullable=False),
        T.StructField("description", T.StringType(), nullable=False),
    ]
)

customer_type = T.StructType(
    [
        T.StructField("src_company", company_type, nullable=False),
        T.StructField("dst_company", company_type, nullable=False),
        T.StructField("description", T.StringType(), nullable=False),
    ]
)

doc_schema = T.StructType(
    [
        T.StructField("title", T.StringType(), nullable=False),
        T.StructField("collected_at", T.DateType(), nullable=False),
        T.StructField("published_at", T.DateType(), nullable=False),
        T.StructField(
            "authors",
            T.ArrayType(author_type),
            nullable=True,
        ),
        T.StructField("summary", T.StringType(), nullable=True),
        T.StructField("companies", T.ArrayType(company_type), nullable=True),
        T.StructField("tickers", T.ArrayType(ticker_type), nullable=True),
        T.StructField("products", T.ArrayType(product_type), nullable=True),
        T.StructField("technologies", T.ArrayType(technology_type), nullable=True),
    ]
)
