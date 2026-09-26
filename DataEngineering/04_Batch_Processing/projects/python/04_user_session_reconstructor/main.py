import argparse
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag, when, sum as _sum, unix_timestamp
from pyspark.sql.window import Window

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(input_path: str, output_path: str, timeout_minutes: int):
    """
    Reconstructs user sessions based on a timeout threshold using PySpark Window functions.
    """
    logger.info("Initializing SparkSession...")
    spark = SparkSession.builder \
        .appName("UserSessionReconstructor") \
        .getOrCreate()
        
    logger.info(f"Reading event data from {input_path}...")
    try:
        df = spark.read.parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to read input data: {e}")
        spark.stop()
        return

    # Define window partitioned by user and ordered by timestamp
    window_spec = Window.partitionBy("user_id").orderBy("timestamp")
    
    # Calculate time difference in seconds between current and previous event
    df = df.withColumn("prev_timestamp", lag(col("timestamp")).over(window_spec))
    df = df.withColumn("time_diff_sec", 
                       unix_timestamp(col("timestamp")) - unix_timestamp(col("prev_timestamp")))
    
    # Determine if a new session has started (time_diff > timeout or prev_timestamp is null)
    timeout_sec = timeout_minutes * 60
    df = df.withColumn("is_new_session", 
                       when(col("time_diff_sec") > timeout_sec, 1)
                       .when(col("prev_timestamp").isNull(), 1)
                       .otherwise(0))
    
    # Generate unique session ID for each user by doing a cumulative sum of the `is_new_session` flag
    df = df.withColumn("session_id", _sum("is_new_session").over(window_spec))
    
    # Clean up intermediate columns
    df = df.drop("prev_timestamp", "time_diff_sec", "is_new_session")

    logger.info(f"Writing reconstructed session data to {output_path}...")
    try:
        df.write \
            .mode("overwrite") \
            .partitionBy("user_id") \
            .parquet(output_path)
        logger.info("Session reconstruction completed successfully.")
    except Exception as e:
        logger.error(f"Failed to write output data: {e}")
        
    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="User Session Reconstructor")
    parser.add_argument("--input-path", required=True, help="S3 URI for input events data (Parquet)")
    parser.add_argument("--output-path", required=True, help="S3 URI for sessionized output (Parquet)")
    parser.add_argument("--timeout-minutes", type=int, default=30, help="Timeout in minutes to define a new session")
    args = parser.parse_args()
    
    main(args.input_path, args.output_path, args.timeout_minutes)
