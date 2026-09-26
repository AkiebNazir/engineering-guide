import argparse
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, window, to_timestamp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(input_path: str, output_path: str, window_duration: str):
    """
    Process log data to aggregate error counts over a specified time window.
    """
    logger.info("Initializing SparkSession...")
    spark = SparkSession.builder \
        .appName("LogProcessorBatchJob") \
        .getOrCreate()
        
    logger.info(f"Reading logs from {input_path}...")
    try:
        # Assuming logs are in JSON or Parquet format in production. 
        # Using parquet as standard.
        df = spark.read.parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to read input data: {e}")
        spark.stop()
        return
        
    # Ensure timestamp is proper type. Assuming it might be a string column initially.
    # If it's already a timestamp, this is safe if cast correctly, or we can assume it's string.
    if dict(df.dtypes).get("timestamp", "string") == "string":
        df = df.withColumn("timestamp", to_timestamp(col("timestamp")))
        
    logger.info("Aggregating metrics (error counts by window)...")
    errors_df = df.filter(col("level") == "ERROR")
    
    # Group by tumbling window and aggregate
    agg_df = errors_df \
        .groupBy(window(col("timestamp"), window_duration)) \
        .agg(count("*").alias("error_count")) \
        .orderBy("window.start")

    logger.info(f"Writing results to {output_path}...")
    try:
        agg_df.write \
            .mode("overwrite") \
            .parquet(output_path)
        logger.info("Batch job completed successfully.")
    except Exception as e:
        logger.error(f"Failed to write output data: {e}")
        
    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Intermediate PySpark Batch Job")
    parser.add_argument("--input-path", required=True, help="S3 URI for input logs (Parquet)")
    parser.add_argument("--output-path", required=True, help="S3 URI for aggregated output (Parquet)")
    parser.add_argument("--window-duration", default="1 hour", help="Window duration for aggregation (e.g., '1 hour', '15 minutes')")
    args = parser.parse_args()
    
    main(args.input_path, args.output_path, args.window_duration)
