import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Denormalizer Engine using Apache Spark (PySpark).
    In a real-world scenario, this handles terabytes of data by distributing 
    the join operations across a cluster (e.g., EMR, Databricks).
    """
    # Initialize Spark Session
    spark = SparkSession.builder \
        .appName("DenormalizerEngine") \
        .master("local[*]") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    # 1. Load Normalized Tables (Dimensions & Facts)
    # In production, these would be loaded from S3/HDFS/Snowflake (e.g., spark.read.parquet("s3://bucket/dim_product"))
    dim_product_data = [
        (1, 'Widget A', 'Widgets'),
        (2, 'Widget B', 'Widgets')
    ]
    dim_product = spark.createDataFrame(dim_product_data, schema=['product_id', 'product_name', 'category'])
    
    dim_store_data = [
        (10, 'North Branch', 'Chicago'),
        (20, 'South Branch', 'Houston')
    ]
    dim_store = spark.createDataFrame(dim_store_data, schema=['store_id', 'store_name', 'city'])
    
    fact_sales_data = [
        (100, 1, 10, 50.0),
        (101, 2, 10, 75.0),
        (102, 1, 20, 50.0)
    ]
    fact_sales = spark.createDataFrame(fact_sales_data, schema=['sale_id', 'product_id', 'store_id', 'amount'])
    
    logger.info("--- Normalized Fact Table ---")
    fact_sales.show()
    
    # 2. Denormalizer Engine: Join everything into one wide table
    # Using left outer joins ensures we keep facts even if a dimension is missing (handling late-arriving dimensions)
    denormalized_df = fact_sales \
        .join(dim_product, on='product_id', how='left') \
        .join(dim_store, on='store_id', how='left')
                                
    logger.info("--- Denormalized Wide Table (Ready for Analytics/ML) ---")
    denormalized_df.show()

    # In production, we would write this denormalized dataframe out to an analytical store (e.g., Delta Lake, Iceberg, Parquet)
    # denormalized_df.write.format("delta").mode("overwrite").save("s3://bucket/analytics_gold_layer/denormalized_sales")

    spark.stop()

if __name__ == '__main__':
    main()
