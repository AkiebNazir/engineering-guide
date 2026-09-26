import argparse
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, coalesce, lit, to_date, mean

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(input_path: str, output_path: str):
    """
    Cleans dirty data containing nulls, invalid formats, and messy strings.
    """
    logger.info("Initializing SparkSession...")
    spark = SparkSession.builder \
        .appName("DataCleansingJob") \
        .getOrCreate()
        
    logger.info(f"Reading dirty data from {input_path}...")
    try:
        # Assuming input is CSV format with headers
        df = spark.read.csv(input_path, header=True, inferSchema=True)
    except Exception as e:
        logger.error(f"Failed to read input data: {e}")
        spark.stop()
        return

    # 1. Clean names: strip whitespace and handle nulls
    df = df.withColumn("name", trim(col("name")))
    df = df.withColumn("name", coalesce(col("name"), lit("Unknown")))
    
    # 2. Clean price: cast to double, impute invalid values with mean
    df = df.withColumn("price", col("price").cast("double"))
    
    # Calculate mean price to fill nulls
    mean_price_row = df.select(mean(col("price")).alias("mean_price")).collect()[0]
    mean_price = mean_price_row['mean_price'] if mean_price_row['mean_price'] is not None else 0.0
    
    df = df.withColumn("price", coalesce(col("price"), lit(mean_price)))
    
    # 3. Clean date: cast to date and drop rows with invalid dates
    # Assuming multiple formats could exist, PySpark's to_date handles standard formats well.
    # We can cast it directly. Invalid dates will become null.
    df = df.withColumn("date", to_date(col("date")))
    df = df.dropna(subset=["date"])

    logger.info(f"Writing cleaned data to {output_path}...")
    try:
        df.write \
            .mode("overwrite") \
            .parquet(output_path)
        logger.info("Data cleansing job completed successfully.")
    except Exception as e:
        logger.error(f"Failed to write cleaned data: {e}")
        
    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Cleansing Job")
    parser.add_argument("--input-path", required=True, help="S3 URI for input dirty data (CSV)")
    parser.add_argument("--output-path", required=True, help="S3 URI for cleaned output data (Parquet)")
    args = parser.parse_args()
    
    main(args.input_path, args.output_path)
