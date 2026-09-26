import os
import logging
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_data(file_path: str) -> pd.DataFrame:
    """Extract data from a CSV file."""
    logging.info(f"Extracting data from {file_path}...")
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Successfully loaded {len(df)} rows.")
        return df
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        raise

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and transform the data."""
    logging.info("Starting data transformation...")
    # Drop rows with any null values
    df_cleaned = df.dropna().copy()
    
    # Deduplicate
    df_cleaned = df_cleaned.drop_duplicates()
    
    # Type conversion
    if 'id' in df_cleaned.columns:
        df_cleaned['id'] = df_cleaned['id'].astype(int)
        
    logging.info(f"Transformation complete. {len(df_cleaned)} rows remaining.")
    return df_cleaned

def load_data(df: pd.DataFrame, db_url: str, table_name: str):
    """Load the data into a PostgreSQL database using SQLAlchemy."""
    logging.info(f"Loading data into {table_name} table...")
    try:
        # Create an engine with connection pooling
        engine = create_engine(db_url, pool_size=5, max_overflow=10)
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        logging.info("Data successfully loaded into PostgreSQL.")
    except SQLAlchemyError as e:
        logging.error(f"Database error occurred: {e}")
        raise

def main():
    logging.info("Starting Data Engineering Project: 01_beginner_pandas_etl")
    csv_file = os.getenv("INPUT_CSV_PATH", "sample_data.csv")
    db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/etl_db")
    
    try:
        df_raw = extract_data(csv_file)
        df_clean = transform_data(df_raw)
        load_data(df_clean, db_url, "users_cleaned")
    except Exception as e:
        logging.error("ETL pipeline failed.", exc_info=True)

if __name__ == "__main__":
    main()
