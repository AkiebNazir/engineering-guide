import os
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
