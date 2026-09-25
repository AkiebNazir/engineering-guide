import pandas as pd
import sqlite3
import os

def create_sample_csv(filename):
    data = {
        'id': [1, 2, 2, 3, 4, 5, None],
        'name': ['Alice', 'Bob', 'Bob', 'Charlie', None, 'Eve', 'Frank'],
        'age': [25, 30, 30, 35, 28, None, 40]
    }
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Sample data created at {filename}")

def etl(csv_filename, db_filename):
    # Extract
    print(f"Reading from {csv_filename}...")
    df = pd.read_csv(csv_filename)
    
    # Transform
    print("Cleaning data...")
    # Drop rows with any null values
    df_cleaned = df.dropna()
    # Deduplicate
    df_cleaned = df_cleaned.drop_duplicates()
    # Convert types if necessary
    df_cleaned['id'] = df_cleaned['id'].astype(int)
    
    print(f"Data transformed. {len(df_cleaned)} rows remaining.")
    
    # Load
    print(f"Loading data into {db_filename}...")
    conn = sqlite3.connect(db_filename)
    df_cleaned.to_sql('users', conn, if_exists='replace', index=False)
    conn.close()
    print("ETL process completed successfully.")

if __name__ == "__main__":
    csv_file = "sample_data.csv"
    db_file = "output.db"
    
    create_sample_csv(csv_file)
    etl(csv_file, db_file)
