import requests
from bs4 import BeautifulSoup
import json

def scrape_quotes():
    url = 'http://quotes.toscrape.com/'
    print(f"Scraping {url}...")
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve page: {response.status_code}")
        return
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    quotes_data = []
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
        
    output_file = 'quotes.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(quotes_data, f, indent=4)
        
    print(f"Scraped {len(quotes_data)} quotes and saved to {output_file}")

if __name__ == '__main__':
    scrape_quotes()
