import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_json, struct, window
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = "localhost:9092"
INPUT_TOPIC = "transactions"
OUTPUT_TOPIC = "fraud_alerts"

def main():
    logger.info("Initializing Fraud Detection Engine...")
    
    # Initialize SparkSession
    spark = SparkSession.builder \
        .appName("FraudDetectionEngine") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Define schema for the incoming transaction events
    transaction_schema = StructType([
        StructField("transaction_id", StringType(), True),
        StructField("user_id", StringType(), True),
        StructField("amount", DoubleType(), True),
        StructField("location", StringType(), True),
        StructField("timestamp", TimestampType(), True)
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

    # Parse JSON payload
    parsed_stream = raw_stream.selectExpr("CAST(value AS STRING) as json_value") \
        .select(from_json(col("json_value"), transaction_schema).alias("data")) \
        .select("data.*")

    # Fraud Detection Logic: Flag transactions with amount > 10,000 as potential fraud
    fraud_stream = parsed_stream.filter(col("amount") > 10000.0) \
        .withColumn("alert_reason", col("amount").cast(StringType())) \
        .select(
            col("transaction_id").alias("key"),
            to_json(struct(
                col("transaction_id"),
                col("user_id"),
                col("amount"),
                col("timestamp")
            )).alias("value")
        )

    # Write anomalies back to Kafka
    logger.info(f"Publishing fraud alerts to Kafka topic: {OUTPUT_TOPIC}")
    query = fraud_stream \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("topic", OUTPUT_TOPIC) \
        .option("checkpointLocation", "/tmp/checkpoints/fraud_detection") \
        .outputMode("append") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
