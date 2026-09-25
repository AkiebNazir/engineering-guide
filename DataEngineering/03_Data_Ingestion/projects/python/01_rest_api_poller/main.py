import requests
import sqlite3

def init_db(db_name="data.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title TEXT,
            body TEXT
        )
    ''')
    conn.commit()
    return conn

def fetch_data(api_url):
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()

def save_data(conn, data):
    cursor = conn.cursor()
    for item in data:
        cursor.execute('''
            INSERT OR REPLACE INTO posts (id, user_id, title, body)
            VALUES (?, ?, ?, ?)
        ''', (item.get('id'), item.get('userId'), item.get('title'), item.get('body')))
    conn.commit()

def main():
    print('Starting Data Engineering Project: 01_rest_api_poller')
    api_url = "https://jsonplaceholder.typicode.com/posts"
    conn = init_db()
    
    try:
        print(f"Fetching data from {api_url}...")
        data = fetch_data(api_url)
        print(f"Fetched {len(data)} items. Saving to SQLite...")
        save_data(conn, data)
        print("Data saved successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
