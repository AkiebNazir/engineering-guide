from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, window, to_timestamp

def create_dummy_logs(filename):
    data = """2023-10-01T10:00:00Z,INFO,User login
2023-10-01T10:05:00Z,ERROR,Database connection failed
2023-10-01T10:15:00Z,ERROR,Timeout occurred
2023-10-01T11:00:00Z,INFO,User logout
2023-10-01T11:30:00Z,ERROR,Null pointer exception
"""
    with open(filename, 'w') as f:
        f.write(data)
    print(f"Created sample logs at {filename}")

def run_batch_job():
    spark = SparkSession.builder \
        .appName("LogProcessorBatch") \
        .getOrCreate()
        
    log_file = "sample_logs.csv"
    create_dummy_logs(log_file)
    
    print("Reading logs...")
    df = spark.read.csv(log_file, inferSchema=True)
    df = df.toDF("timestamp_str", "level", "message")
    
    df = df.withColumn("timestamp", to_timestamp(col("timestamp_str")))
    
    print("Aggregating metrics (error counts by hour)...")
    errors_df = df.filter(col("level") == "ERROR")
    agg_df = errors_df.groupBy(window(col("timestamp"), "1 hour")).agg(count("*").alias("error_count"))
    
    output_dir = "output_parquet"
    print(f"Writing results to {output_dir}...")
    agg_df.write.mode("overwrite").parquet(output_dir)
    
    agg_df.show(truncate=False)
    
    spark.stop()
    print("Batch job completed.")

if __name__ == "__main__":
    run_batch_job()
