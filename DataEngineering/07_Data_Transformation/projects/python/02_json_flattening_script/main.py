import sys
import logging
from typing import Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, explode_outer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class JSONFlattener:
    """
    A production-grade JSON flattener utilizing PySpark for distributed data processing.
    """
    def __init__(self, app_name: str = "JSONFlattener"):
        self.spark = SparkSession.builder \
            .appName(app_name) \
            .getOrCreate()
        logger.info("Spark session initialized.")

    def flatten_dataframe(self, df: DataFrame) -> DataFrame:
        """
        Recursively flattens nested structs in a DataFrame.
        """
        complex_fields = dict([
            (field.name, field.dataType)
            for field in df.schema.fields
            if type(field.dataType).__name__ == 'StructType'
        ])
        
        while len(complex_fields) != 0:
            col_name = list(complex_fields.keys())[0]
            
            expanded_cols = [
                col(f"{col_name}.{k}").alias(f"{col_name}_{k}") 
                for k in [n.name for n in complex_fields[col_name].fields]
            ]
            
            df = df.select("*", *expanded_cols).drop(col_name)
            
            complex_fields = dict([
                (field.name, field.dataType)
                for field in df.schema.fields
                if type(field.dataType).__name__ == 'StructType'
            ])
            
        return df
        
    def process_demo(self):
        try:
            logger.info("Running JSON flattener demo...")
            data = [
                ('{"user_id": 1, "profile": {"name": "Alice", "age": 30}, "location": {"city": "NYC", "zip": "10001"}}',)
            ]
            rdd = self.spark.sparkContext.parallelize(data)
            df = self.spark.read.json(rdd.map(lambda x: x[0]))
            
            flattened_df = self.flatten_dataframe(df)
            flattened_df.show(truncate=False)
            
            logger.info("Flattening process completed successfully.")
        except Exception as e:
            logger.error(f"Error during JSON flattening pipeline: {e}", exc_info=True)
            raise

    def stop(self):
        self.spark.stop()

if __name__ == "__main__":
    flattener = JSONFlattener()
    try:
        flattener.process_demo()
    finally:
        flattener.stop()
