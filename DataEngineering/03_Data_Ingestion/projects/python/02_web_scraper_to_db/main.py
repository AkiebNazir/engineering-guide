import sqlite3
import re

MOCK_HTML = """
<html>
    <head><title>Mock Webpage</title></head>
    <body>
        <h1>Breaking News</h1>
        <div class="article"><h2>Python 3.12 Released!</h2></div>
        <div class="article"><h2>Data Engineering is Awesome</h2></div>
        <div class="article"><h2>PostgreSQL vs SQLite</h2></div>
    </body>
</html>
"""

def init_db(db_name="scraper.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS titles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT
        )
    ''')
    conn.commit()
    return conn

def extract_titles(html):
    pattern = r"<h2>(.*?)</h2>"
    return re.findall(pattern, html)

def save_titles(conn, titles):
    cursor = conn.cursor()
    for title in titles:
        cursor.execute('INSERT INTO titles (title) VALUES (?)', (title,))
    conn.commit()

def main():
    print('Starting Data Engineering Project: 02_web_scraper_to_db')
    conn = init_db()
    
    print("Extracting titles from mock HTML...")
    titles = extract_titles(MOCK_HTML)
    
    print(f"Extracted {len(titles)} titles. Saving to database...")
    save_titles(conn, titles)
    
    print("Titles saved successfully.")
    conn.close()

if __name__ == '__main__':
    main()
