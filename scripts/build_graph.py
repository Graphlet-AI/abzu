import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession

from abzu.baml_client import b
from abzu.spark.types import doc_schema

# from sparkdantic import create_spark_schema

# Get the Spark output schema for BAML records
# spark_schema: StructType = create_spark_schema(IndustryArticle)

spark: SparkSession = SparkSession.builder.appName("build_graph").getOrCreate()

article_df: DataFrame = spark.read.json("data/articles.jsonl")
article_df.show()


# Create UDF with the defined return type
@F.udf(returnType=doc_schema)
def parse_article(article: str) -> dict:
    # Parse the string however you need
    # Return a dict matching the schema structure
    return b.ExtractIndustryArticle(article).model_dump()


article_df = article_df.withColumn("document", F.udf(parse_article, doc_schema)("url"))
article_df.show()
