import argparse
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum, to_date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(input_path: str, output_path: str):
    """
    Aggregates daily sales by product and writes the output back to S3.
    """
    logger.info("Initializing SparkSession...")
    spark = SparkSession.builder \
        .appName("DailySalesAggregator") \
        .getOrCreate()
        
    logger.info(f"Reading input data from {input_path}...")
    try:
        # Assuming input is parquet format
        df = spark.read.parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to read input data: {e}")
        spark.stop()
        return

    # Clean and aggregate data
    # Input schema expected: date (string or timestamp), product (string), amount (double)
    agg_df = df \
        .withColumn("date", to_date(col("date"))) \
        .groupBy("date", "product") \
        .agg(_sum("amount").alias("total_sales")) \
        .orderBy("date", "product")

    logger.info(f"Writing aggregated data to {output_path}...")
    try:
        agg_df.write \
            .mode("overwrite") \
            .partitionBy("date") \
            .parquet(output_path)
        logger.info("Job completed successfully.")
    except Exception as e:
        logger.error(f"Failed to write output data: {e}")
        
    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Sales Aggregator")
    parser.add_argument("--input-path", required=True, help="S3 URI for input sales data (Parquet)")
    parser.add_argument("--output-path", required=True, help="S3 URI for aggregated output data (Parquet)")
    args = parser.parse_args()
    
    main(args.input_path, args.output_path)
