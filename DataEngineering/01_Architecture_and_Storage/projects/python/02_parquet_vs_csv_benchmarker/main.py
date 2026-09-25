import os
import time
import pandas as pd
import numpy as np

def benchmark():
    print("Generating large dataset...")
    # Create a DataFrame with 1 million rows
    n_rows = 1_000_000
    df = pd.DataFrame({
        'id': np.arange(n_rows),
        'value': np.random.randn(n_rows),
        'category': np.random.choice(['A', 'B', 'C', 'D'], size=n_rows),
        'timestamp': pd.date_range('2023-01-01', periods=n_rows, freq='S')
    })
    
    csv_file = 'data.csv'
    parquet_file = 'data.parquet'
    
    # Write Benchmarks
    print("\n--- Write Benchmarks ---")
    start = time.time()
    df.to_csv(csv_file, index=False)
    csv_write_time = time.time() - start
    print(f"CSV Write Time: {csv_write_time:.4f} seconds")
    
    start = time.time()
    df.to_parquet(parquet_file, engine='pyarrow')
    parquet_write_time = time.time() - start
    print(f"Parquet Write Time: {parquet_write_time:.4f} seconds")
    
    # Size Benchmarks
    print("\n--- File Size Benchmarks ---")
    csv_size = os.path.getsize(csv_file) / (1024 * 1024)
    parquet_size = os.path.getsize(parquet_file) / (1024 * 1024)
    print(f"CSV File Size: {csv_size:.2f} MB")
    print(f"Parquet File Size: {parquet_size:.2f} MB")
    
    # Read Benchmarks
    print("\n--- Read Benchmarks ---")
    start = time.time()
    pd.read_csv(csv_file)
    csv_read_time = time.time() - start
    print(f"CSV Read Time: {csv_read_time:.4f} seconds")
    
    start = time.time()
    pd.read_parquet(parquet_file, engine='pyarrow')
    parquet_read_time = time.time() - start
    print(f"Parquet Read Time: {parquet_read_time:.4f} seconds")
    
    # Cleanup
    os.remove(csv_file)
    os.remove(parquet_file)

if __name__ == "__main__":
    benchmark()
