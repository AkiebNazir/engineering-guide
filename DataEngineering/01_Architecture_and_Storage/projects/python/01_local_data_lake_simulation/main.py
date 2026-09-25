import os
import json
import random
from datetime import datetime, timedelta

def generate_dummy_data(num_records=100):
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
    return data

def ingest_to_data_lake(data, base_dir="data_lake/raw"):
    for record in data:
        # Create partition directory
        partition_path = os.path.join(
            base_dir,
            f"year={record['year']}",
            f"month={record['month']:02d}",
            f"day={record['day']:02d}"
        )
        os.makedirs(partition_path, exist_ok=True)
        
        # Write record to file
        file_path = os.path.join(partition_path, f"event_{record['id']}.json")
        with open(file_path, "w") as f:
            json.dump(record, f)

if __name__ == "__main__":
    print("Generating dummy data...")
    dummy_data = generate_dummy_data(100)
    print("Ingesting data to local data lake...")
    ingest_to_data_lake(dummy_data)
    print("Data ingestion complete. Check the 'data_lake/raw' directory.")
