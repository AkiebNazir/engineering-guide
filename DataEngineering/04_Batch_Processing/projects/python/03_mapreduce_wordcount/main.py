import argparse
import logging
import re
from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(input_path: str, output_path: str):
    """
    Classic MapReduce Word Count using PySpark RDD API.
    """
    logger.info("Initializing SparkSession...")
    spark = SparkSession.builder \
        .appName("MapReduceWordCount") \
        .getOrCreate()
        
    sc = spark.sparkContext
    
    logger.info(f"Reading text data from {input_path}...")
    try:
        # Read text file into an RDD of strings (one per line)
        lines = sc.textFile(input_path)
    except Exception as e:
        logger.error(f"Failed to read input data: {e}")
        spark.stop()
        return

    logger.info("Running MapReduce word count...")
    
    # 1. Map phase: split lines into words and emit (word, 1)
    def extract_words(line):
        return re.findall(r'\b\w+\b', line.lower())
    
    word_counts = lines \
        .flatMap(extract_words) \
        .map(lambda word: (word, 1)) \
        .reduceByKey(lambda a, b: a + b) # 2. Reduce phase: aggregate counts by key
        
    logger.info(f"Writing results to {output_path}...")
    try:
        # Sort by count descending before saving (optional, but nice)
        sorted_word_counts = word_counts.sortBy(lambda x: x[1], ascending=False)
        
        # Convert to DataFrame to write out gracefully as CSV or Parquet
        # Or we could just use saveAsTextFile
        df = spark.createDataFrame(sorted_word_counts, ["word", "count"])
        df.write.mode("overwrite").csv(output_path, header=True)
        
        logger.info("Word Count MapReduce job completed successfully.")
    except Exception as e:
        logger.error(f"Failed to write output data: {e}")
        
    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MapReduce Word Count")
    parser.add_argument("--input-path", required=True, help="S3 URI for input text file")
    parser.add_argument("--output-path", required=True, help="S3 URI for word counts output (CSV)")
    args = parser.parse_args()
    
    main(args.input_path, args.output_path)
