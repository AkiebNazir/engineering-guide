import hashlib
import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, udf, lit
from pyspark.sql.types import StringType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def mask_email_func(email: str) -> str:
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) > 0:
        return f"{local[0]}***@{domain}"
    return f"***@{domain}"

def hash_ssn_func(ssn: str, salt: str) -> str:
    if not ssn:
        return ssn
    salted = f"{ssn}{salt}".encode('utf-8')
    return hashlib.sha256(salted).hexdigest()

mask_email_udf = udf(mask_email_func, StringType())
hash_ssn_udf = udf(hash_ssn_func, StringType())

class PIIMaskingTransformer:
    """
    A production-grade PII Masking Transformer utilizing PySpark.
    Applies salting to hashes to prevent rainbow table attacks.
    """
    def __init__(self, salt: str = "PRODUCTION_SALT_123"):
        self.salt = salt
        self.spark = SparkSession.builder \
            .appName("PIIMaskingTransformer") \
            .getOrCreate()
        logger.info("Spark session initialized for PII Masking.")

    def transform(self, df: DataFrame) -> DataFrame:
        transformed_df = df
        
        if "email" in df.columns:
            logger.info("Masking 'email' column.")
            transformed_df = transformed_df.withColumn("email_masked", mask_email_udf(col("email")))
            transformed_df = transformed_df.drop("email")
            
        if "ssn" in df.columns:
            logger.info("Hashing 'ssn' column with salt.")
            transformed_df = transformed_df.withColumn("ssn_hashed", hash_ssn_udf(col("ssn"), lit(self.salt)))
            transformed_df = transformed_df.drop("ssn")
            
        return transformed_df

if __name__ == "__main__":
    transformer = PIIMaskingTransformer()
    
    try:
        data = [
            ("Alice", "alice@example.com", "123-456-7890"),
            ("Bob", "bob.smith@test.com", "987-654-3210")
        ]
        columns = ["user", "email", "ssn"]
        df = transformer.spark.createDataFrame(data, columns)
        
        logger.info("Original DataFrame Schema:")
        df.printSchema()
        
        masked_df = transformer.transform(df)
        
        logger.info("Masked DataFrame Results:")
        masked_df.show(truncate=False)
    finally:
        transformer.spark.stop()
