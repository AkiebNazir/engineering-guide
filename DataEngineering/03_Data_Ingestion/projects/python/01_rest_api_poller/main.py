import os
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
