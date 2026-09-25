import requests
import pandas as pd
from sqlalchemy import create_engine

def fetch_data():
    url = "https://jsonplaceholder.typicode.com/users"
    print(f"Fetching data from {url}...")
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def transform_data(raw_data):
    print("Transforming data...")
    users = []
    for item in raw_data:
        users.append({
            'id': item['id'],
            'name': item['name'],
            'username': item['username'],
            'email': item['email'],
            'city': item['address']['city']
        })
    return pd.DataFrame(users)

def load_data(df):
    db_url = "postgresql://postgres:password@localhost:5432/postgres"
    print(f"Loading data into PostgreSQL at {db_url}...")
    try:
        engine = create_engine(db_url)
        df.to_sql('api_users', engine, if_exists='replace', index=False)
        print("Data loaded successfully.")
    except Exception as e:
        print(f"Failed to connect or load to Postgres: {e}")

if __name__ == "__main__":
    raw_data = fetch_data()
    df = transform_data(raw_data)
    load_data(df)
