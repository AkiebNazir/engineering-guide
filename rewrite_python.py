import os

files = {}

files["/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/python/01_beginner_pandas_etl/main.py"] = """import os
import logging
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_data(file_path: str) -> pd.DataFrame:
    \"\"\"Extract data from a CSV file.\"\"\"
    logging.info(f"Extracting data from {file_path}...")
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Successfully loaded {len(df)} rows.")
        return df
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        raise

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    \"\"\"Clean and transform the data.\"\"\"
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
    \"\"\"Load the data into a PostgreSQL database using SQLAlchemy.\"\"\"
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
"""

files["/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/python/02_beginner_web_scraper/main.py"] = """import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_session() -> requests.Session:
    \"\"\"Configure a requests session with retries.\"\"\"
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def scrape_quotes(url: str, output_file: str):
    \"\"\"Scrape quotes from the target URL and save as JSON.\"\"\"
    logging.info(f"Scraping {url}...")
    session = get_session()
    
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to retrieve page: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    quotes_data = []
    
    # Extract quotes
    quotes = soup.find_all('div', class_='quote')
    for quote in quotes:
        text = quote.find('span', class_='text').text
        author = quote.find('small', class_='author').text
        tags = [tag.text for tag in quote.find_all('a', class_='tag')]
        
        quotes_data.append({
            'text': text,
            'author': author,
            'tags': tags
        })
        
    # Save output
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(quotes_data, f, indent=4)
        logging.info(f"Successfully scraped {len(quotes_data)} quotes and saved to {output_file}")
    except IOError as e:
        logging.error(f"Failed to write to file {output_file}: {e}")

def main():
    url = os.getenv("TARGET_URL", "http://quotes.toscrape.com/")
    output = os.getenv("OUTPUT_FILE", "quotes.json")
    scrape_quotes(url, output)

if __name__ == '__main__':
    main()
"""

files["/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/python/02_web_scraper_to_db/main.py"] = """import os
import logging
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

Base = declarative_base()

class ArticleTitle(Base):
    __tablename__ = 'article_titles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)

def get_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def init_db(db_url: str):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

def fetch_titles(url: str) -> list[str]:
    logging.info(f"Fetching titles from {url}...")
    session = get_session()
    response = session.get(url, timeout=15)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    # Assuming scraping a typical tech blog with h2 tags for article titles
    titles = [h2.get_text(strip=True) for h2 in soup.find_all('h2')]
    return titles

def save_titles(db_session, titles: list[str]):
    session = db_session()
    try:
        for t in titles:
            if t:
                record = ArticleTitle(title=t)
                session.add(record)
        session.commit()
        logging.info("Titles successfully saved to database.")
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to save titles: {e}")
        raise
    finally:
        session.close()

def main():
    logging.info('Starting Data Engineering Project: 02_web_scraper_to_db')
    target_url = os.getenv("SCRAPE_URL", "https://news.ycombinator.com/") 
    # Just an example target, structure may vary. 
    db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/scraper_db")
    
    try:
        db_session_factory = init_db(db_url)
        titles = fetch_titles(target_url)
        logging.info(f"Extracted {len(titles)} titles. Saving...")
        save_titles(db_session_factory, titles)
    except Exception as e:
        logging.error("Scraper pipeline failed.", exc_info=True)

if __name__ == '__main__':
    main()
"""

files["/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/python/03_beginner_api_to_postgres/main.py"] = """import os
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
"""

files["/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/python/03_cdc_log_tailer/main.py"] = """import os
import json
import logging
from confluent_kafka import Consumer, KafkaException, KafkaError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_consumer(brokers: str, group_id: str) -> Consumer:
    \"\"\"Create and return a Kafka Consumer instance.\"\"\"
    conf = {
        'bootstrap.servers': brokers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    }
    return Consumer(conf)

def process_cdc_event(event_value: bytes):
    \"\"\"Process a single CDC event.\"\"\"
    try:
        payload = json.loads(event_value.decode('utf-8'))
        op = payload.get("op") # typical Debezium op code: 'c' (create), 'u' (update), 'd' (delete)
        if op in ['c', 'u']:
            logging.info(f"Event detected (INSERT/UPDATE): {payload}")
        elif op == 'd':
            logging.info(f"Event detected (DELETE): {payload}")
    except json.JSONDecodeError:
        logging.warning(f"Could not parse event as JSON: {event_value}")

def main():
    logging.info('Starting Data Engineering Project: 03_cdc_log_tailer (Kafka Consumer)')
    
    brokers = os.getenv("KAFKA_BROKERS", "localhost:9092")
    topic = os.getenv("KAFKA_CDC_TOPIC", "dbserver1.inventory.customers")
    group_id = os.getenv("KAFKA_GROUP_ID", "cdc-tailer-group")
    
    consumer = create_consumer(brokers, group_id)
    consumer.subscribe([topic])
    
    logging.info(f"Subscribed to topic {topic}. Waiting for events...")
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition
                    continue
                else:
                    raise KafkaException(msg.error())
            
            # Process event
            process_cdc_event(msg.value())
            
            # Commit offsets manually after processing for at-least-once delivery
            consumer.commit(asynchronous=False)
            
    except KeyboardInterrupt:
        logging.info("Stopping CDC consumer...")
    except Exception as e:
        logging.error("Consumer error", exc_info=True)
    finally:
        consumer.close()

if __name__ == '__main__':
    main()
"""

files["/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/python/04_webhook_listener/main.py"] = """import os
import json
import uuid
import logging
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
import uvicorn
import boto3
from botocore.exceptions import BotoCoreError, ClientError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Webhook Listener API")

S3_BUCKET = os.getenv("S3_BUCKET", "my-webhook-payloads")
s3_client = boto3.client('s3', region_name=os.getenv("AWS_REGION", "us-east-1"))

@app.post("/webhook")
async def receive_webhook(request: Request):
    \"\"\"
    Endpoint to receive webhook payloads and upload them directly to AWS S3.
    \"\"\"
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Generate a unique object key based on timestamp and uuid
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    file_id = str(uuid.uuid4())
    object_key = f"webhooks/{timestamp}_{file_id}.json"
    
    try:
        # Upload the payload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=object_key,
            Body=json.dumps(payload),
            ContentType="application/json"
        )
        logging.info(f"Successfully uploaded payload to s3://{S3_BUCKET}/{object_key}")
    except (BotoCoreError, ClientError) as e:
        logging.error(f"Failed to upload to S3: {e}")
        # In a real scenario, you might write to a local fallback or Kafka dead-letter queue
        raise HTTPException(status_code=500, detail="Failed to persist webhook payload")

    return {"status": "success", "key": object_key}

def main():
    logging.info('Starting Data Engineering Project: 04_webhook_listener (FastAPI + Boto3)')
    port = int(os.getenv("PORT", 8080))
    # Uvicorn is a standard ASGI server for FastAPI
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == '__main__':
    main()
"""

files["/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/python/05_ftp_file_downloader/main.py"] = """import os
import logging
import paramiko
from paramiko.ssh_exception import SSHException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_sftp_file(host: str, port: int, user: str, pkey_path: str, remote_path: str, local_path: str):
    \"\"\"
    Connects to an SFTP server using an SSH key and downloads a file.
    \"\"\"
    logging.info(f"Connecting to SFTP server {host}:{port} as {user}...")
    
    try:
        # Setup SSH Client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load private key
        try:
            private_key = paramiko.RSAKey.from_private_key_file(pkey_path)
        except Exception as e:
            logging.error(f"Failed to load SSH private key: {e}")
            raise
            
        ssh.connect(hostname=host, port=port, username=user, pkey=private_key, timeout=10)
        logging.info("SSH connection established. Opening SFTP session...")
        
        sftp = ssh.open_sftp()
        logging.info(f"Downloading {remote_path} to {local_path}...")
        
        sftp.get(remote_path, local_path)
        logging.info("Download complete.")
        
        sftp.close()
        ssh.close()
    except SSHException as e:
        logging.error(f"SSH/SFTP error occurred: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise

def main():
    logging.info('Starting Data Engineering Project: 05_ftp_file_downloader (Paramiko SFTP)')
    host = os.getenv("SFTP_HOST", "sftp.example.com")
    port = int(os.getenv("SFTP_PORT", 22))
    user = os.getenv("SFTP_USER", "demo")
    pkey_path = os.getenv("SFTP_PKEY_PATH", "/path/to/private/key")
    remote_path = os.getenv("SFTP_REMOTE_PATH", "/incoming/data.csv")
    local_path = os.getenv("LOCAL_DOWNLOAD_PATH", "./data.csv")
    
    try:
        # In a real environment, you must provide a valid key path
        if not os.path.exists(pkey_path):
            logging.warning(f"Private key not found at {pkey_path}. Ensure it exists for actual execution.")
            
        download_sftp_file(host, port, user, pkey_path, remote_path, local_path)
    except Exception as e:
        logging.error("SFTP download pipeline failed.", exc_info=True)

if __name__ == '__main__':
    main()
"""

files["/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/python/01_rest_api_poller/main.py"] = """import os
import time
import logging
import requests
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

Base = declarative_base()

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    title = Column(String)
    body = Column(String)

def init_db(db_url: str):
    engine = create_engine(db_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

def get_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session

def fetch_data(session: requests.Session, api_url: str) -> list[dict]:
    response = session.get(api_url, timeout=10)
    response.raise_for_status()
    return response.json()

def save_data(db_session_factory, data: list[dict]):
    session = db_session_factory()
    try:
        for item in data:
            post = session.query(Post).filter_by(id=item.get('id')).first()
            if not post:
                post = Post(id=item.get('id'))
                session.add(post)
            
            post.user_id = item.get('userId')
            post.title = item.get('title')
            post.body = item.get('body')
            
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving to database: {e}")
        raise
    finally:
        session.close()

def main():
    logging.info('Starting Data Engineering Project: 01_rest_api_poller')
    api_url = os.getenv("API_URL", "https://jsonplaceholder.typicode.com/posts")
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/poller_db")
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", 60))
    
    db_session_factory = init_db(db_url)
    http_session = get_session()
    
    while True:
        try:
            logging.info(f"Polling data from {api_url}...")
            data = fetch_data(http_session, api_url)
            logging.info(f"Fetched {len(data)} items. Saving to Postgres...")
            
            save_data(db_session_factory, data)
            logging.info("Data saved successfully.")
            
        except Exception as e:
            logging.error(f"Polling failed: {e}")
            
        logging.info(f"Sleeping for {poll_interval} seconds...")
        time.sleep(poll_interval)

if __name__ == '__main__':
    main()
"""

for path, content in files.items():
    with open(path, "w") as f:
        f.write(content)
