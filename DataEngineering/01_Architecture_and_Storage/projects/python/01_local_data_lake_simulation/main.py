import os
import random
from datetime import datetime, timedelta
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def generate_dummy_data(num_records: int = 100) -> pd.DataFrame:
    """Generates synthetic event data for the data lake."""
    data = []
    start_date = datetime(2023, 1, 1)
    for i in range(num_records):
        date = start_date + timedelta(days=random.randint(0, 365))
        record = {
            "id": i,
            "event": random.choice(["login", "logout", "purchase", "view"]),
            "timestamp": date.isoformat(),
            "year": date.year,
            "month": date.month,
            "day": date.day
        }
        data.append(record)
    return pd.DataFrame(data)

def ingest_to_data_lake(df: pd.DataFrame, base_dir: str = "data_lake/raw") -> None:
    """
    Ingests a Pandas DataFrame into a local Data Lake partitioned by year, month, and day.
    Utilizes PyArrow for efficient Parquet writing.
    """
    os.makedirs(base_dir, exist_ok=True)
    
    # Convert Pandas DataFrame to PyArrow Table
    table = pa.Table.from_pandas(df)
    
    # Write partitioned Parquet dataset
    pq.write_to_dataset(
        table,
        root_path=base_dir,
        partition_cols=['year', 'month', 'day'],
        compression='snappy',
        use_dictionary=True
    )

if __name__ == "__main__":
    print("Generating dummy dataset...")
    df = generate_dummy_data(1000)
    
    print("Ingesting data to local data lake (Parquet Format)...")
    ingest_to_data_lake(df)
    
    print("Data ingestion complete. Check the 'data_lake/raw' directory for partitioned Parquet files.")
