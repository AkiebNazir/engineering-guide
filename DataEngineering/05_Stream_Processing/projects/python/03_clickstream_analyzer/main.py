import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, window, count
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = "localhost:9092"
INPUT_TOPIC = "clickstream"
OUTPUT_TOPIC = "clickstream_analytics"

def main():
    logger.info("Initializing Clickstream Analyzer...")
    
    spark = SparkSession.builder \
        .appName("ClickstreamAnalyzer") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Define schema for clickstream events
    click_schema = StructType([
        StructField("user_id", StringType(), True),
        StructField("page_url", StringType(), True),
        StructField("action", StringType(), True),
        StructField("event_time", TimestampType(), True)
    ])

    # Read streaming data from Kafka
    logger.info(f"Subscribing to Kafka topic: {INPUT_TOPIC}")
    raw_stream = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", INPUT_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    # Parse JSON payload and add watermark for late data handling
    parsed_stream = raw_stream.selectExpr("CAST(value AS STRING) as json_value") \
        .select(from_json(col("json_value"), click_schema).alias("data")) \
        .select("data.*") \
        .withWatermark("event_time", "5 minutes")

    # Group by window and page_url to count clicks
    windowed_counts = parsed_stream \
        .groupBy(
            window(col("event_time"), "1 minute", "30 seconds"),
            col("page_url")
        ) \
        .agg(count("*").alias("click_count"))

    # Output to console (for development/debugging)
    logger.info("Starting stream processing...")
    query = windowed_counts \
        .writeStream \
        .outputMode("update") \
        .format("console") \
        .option("truncate", "false") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
