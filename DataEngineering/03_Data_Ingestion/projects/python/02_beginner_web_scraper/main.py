import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_session() -> requests.Session:
    """Configure a requests session with retries."""
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
    """Scrape quotes from the target URL and save as JSON."""
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
