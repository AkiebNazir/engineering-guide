import os
import logging
import requests
import pandas as pd
from sqlalchemy import create_engine
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_http_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session

def fetch_data(url: str) -> list[dict]:
    logging.info(f"Fetching data from {url}...")
    session = get_http_session()
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data: {e}")
        raise

def transform_data(raw_data: list[dict]) -> pd.DataFrame:
    logging.info("Transforming data...")
    users = []
    for item in raw_data:
        # Robust extraction in case of missing keys
        address = item.get('address', {})
        users.append({
            'id': item.get('id'),
            'name': item.get('name'),
            'username': item.get('username'),
            'email': item.get('email'),
            'city': address.get('city')
        })
    df = pd.DataFrame(users)
    # Basic cleaning
    df = df.dropna(subset=['id'])
    return df

def load_data(df: pd.DataFrame, db_url: str):
    logging.info("Loading data into PostgreSQL...")
    try:
        engine = create_engine(db_url, pool_pre_ping=True, pool_size=5)
        df.to_sql('api_users', engine, if_exists='replace', index=False)
        logging.info("Data loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to connect or load to Postgres: {e}")
        raise

def main():
    api_url = os.getenv("API_URL", "https://jsonplaceholder.typicode.com/users")
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/postgres")
    
    try:
        raw_data = fetch_data(api_url)
        df = transform_data(raw_data)
        load_data(df, db_url)
    except Exception as e:
        logging.error("ETL process failed.", exc_info=True)

if __name__ == "__main__":
    main()
