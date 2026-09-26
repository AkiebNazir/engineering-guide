import os
import time
import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from contextlib import contextmanager

@contextmanager
def timer(description: str):
    """Context manager for timing execution."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"{description}: {elapsed:.4f} seconds")

def get_file_size_mb(filepath: str) -> float:
    """Returns the size of a file in Megabytes."""
    return os.path.getsize(filepath) / (1024 * 1024)

def benchmark():
    print("Generating large dataset (1 million rows)...")
    n_rows = 1_000_000
    
    # Using efficient NumPy generation
    df = pd.DataFrame({
        'id': np.arange(n_rows, dtype=np.int64),
        'value': np.random.randn(n_rows).astype(np.float32),
        'category': pd.Categorical(np.random.choice(['A', 'B', 'C', 'D'], size=n_rows)),
        'timestamp': pd.date_range('2023-01-01', periods=n_rows, freq='S')
    })
    
    csv_file = 'benchmark_data.csv'
    parquet_file = 'benchmark_data.parquet'
    
    print("\n--- Write Benchmarks ---")
    with timer("CSV Write Time"):
        df.to_csv(csv_file, index=False)
        
    with timer("Parquet Write Time (Snappy)"):
        # Explicitly using PyArrow engine and Snappy compression
        df.to_parquet(parquet_file, engine='pyarrow', compression='snappy')
        
    print("\n--- File Size Benchmarks ---")
    print(f"CSV File Size:     {get_file_size_mb(csv_file):.2f} MB")
    print(f"Parquet File Size: {get_file_size_mb(parquet_file):.2f} MB")
    
    print("\n--- Read Benchmarks ---")
    with timer("CSV Read Time"):
        # For fair comparison, we don't specify dtypes, letting pandas infer (which is slow for CSV)
        pd.read_csv(csv_file)
        
    with timer("Parquet Read Time"):
        # Parquet retains data types, making reading much faster
        pd.read_parquet(parquet_file, engine='pyarrow')
        
    print("\n--- Selective Column Read Benchmarks ---")
    with timer("CSV Selective Read Time"):
        pd.read_csv(csv_file, usecols=['category', 'value'])
        
    with timer("Parquet Selective Read Time"):
        # Columnar format shines when reading a subset of columns
        pd.read_parquet(parquet_file, engine='pyarrow', columns=['category', 'value'])
        
    # Cleanup
    try:
        os.remove(csv_file)
        os.remove(parquet_file)
    except OSError as e:
        print(f"Cleanup warning: {e}")

if __name__ == "__main__":
    benchmark()
