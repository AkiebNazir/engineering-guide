import argparse
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_extract, count, when

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(input_path: str, output_path: str, threshold: int):
    """
    Detect anomalies in logs based on high 404 error rates per IP.
    """
    logger.info("Initializing SparkSession...")
    spark = SparkSession.builder \
        .appName("LogAnomalyDetector") \
        .getOrCreate()
        
    logger.info(f"Reading raw log lines from {input_path}...")
    try:
        # Read raw text lines
        raw_logs = spark.read.text(input_path)
    except Exception as e:
        logger.error(f"Failed to read input data: {e}")
        spark.stop()
        return

    # Extract IP and HTTP status code using regex
    # Common Apache/Nginx format: 192.168.1.1 - - [10/Oct/... "GET /..." 404 232
    ip_pattern = r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    status_pattern = r'"\s+(\d{3})\s+'

    df = raw_logs.select(
        regexp_extract(col("value"), ip_pattern, 1).alias("ip"),
        regexp_extract(col("value"), status_pattern, 1).alias("status")
    )

    # Filter out unparsed lines (where IP or status could not be extracted)
    df = df.filter((col("ip") != "") & (col("status") != ""))

    logger.info("Aggregating 404 errors by IP...")
    # Count occurrences of 404 status per IP
    error_counts = df.filter(col("status") == "404") \
        .groupBy("ip") \
        .agg(count("*").alias("error_count"))

    logger.info(f"Filtering IPs with error count > {threshold}...")
    anomalous_ips = error_counts.filter(col("error_count") > threshold)

    logger.info(f"Writing anomalous IPs to {output_path}...")
    try:
        anomalous_ips.write \
            .mode("overwrite") \
            .csv(output_path, header=True)
        logger.info("Anomaly detection completed successfully.")
    except Exception as e:
        logger.error(f"Failed to write output data: {e}")
        
    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log Anomaly Detector")
    parser.add_argument("--input-path", required=True, help="S3 URI for input raw logs (Text)")
    parser.add_argument("--output-path", required=True, help="S3 URI for anomalous IPs output (CSV)")
    parser.add_argument("--threshold", type=int, default=10, help="Error count threshold to flag as anomaly")
    args = parser.parse_args()
    
    main(args.input_path, args.output_path, args.threshold)
