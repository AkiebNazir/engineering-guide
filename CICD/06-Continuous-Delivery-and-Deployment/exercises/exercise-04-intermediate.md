# Exercise 4: Database Migration in the CD Pipeline 🗄️

## 🎯 Objective
Write a Python script that simulates applying database schema migrations before deploying the application code.

## 📋 Prerequisites
- Python 3 installed
- SQLite3 (built into Python)

## 📝 Instructions
1. Create a script named `migrate_and_deploy.py`.
2. The script should connect to a local SQLite database file `app.db`.
3. It should check the current schema version (create a `schema_info` table if it doesn't exist).
4. Apply pending migrations sequentially (e.g., V1: create users table, V2: add email column).
5. Only after migrations are successful, simulate the app code deployment.

## 💡 Hints
- Use the `sqlite3` module.
- Keep a list of migration SQL statements and their corresponding version numbers.

## ✅ Expected Output / Solution

```python
# migrate_and_deploy.py
import sqlite3
import sys

MIGRATIONS = [
    {
        "version": 1,
        "sql": "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT);"
    },
    {
        "version": 2,
        "sql": "ALTER TABLE users ADD COLUMN email TEXT;"
    }
]

def init_db(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_info (
            version INTEGER PRIMARY KEY
        )
    ''')
    cursor.execute('SELECT MAX(version) FROM schema_info')
    row = cursor.fetchone()
    return row[0] if row[0] is not None else 0

def run_migrations(conn):
    cursor = conn.cursor()
    current_version = init_db(cursor)
    print(f"Current DB Version: {current_version}")

    for migration in MIGRATIONS:
        if migration["version"] > current_version:
            print(f"Applying migration v{migration['version']}...")
            try:
                cursor.execute(migration["sql"])
                cursor.execute(
                    'INSERT INTO schema_info (version) VALUES (?)', 
                    (migration["version"],)
                )
                conn.commit()
                print(f"✅ Migration v{migration['version']} applied successfully.")
            except sqlite3.Error as e:
                print(f"❌ Database error during migration: {e}")
                conn.rollback()
                return False
    
    print("All migrations up to date.")
    return True

def deploy_code():
    print("🚀 Deploying new application code...")
    # Simulate code deployment
    print("✅ Deployment successful!")

if __name__ == "__main__":
    print("Starting CD Pipeline Phase...")
    conn = sqlite3.connect("app.db")
    
    if not run_migrations(conn):
        print("Pipeline aborted due to migration failure.")
        sys.exit(1)
        
    deploy_code()
    conn.close()
```

## 🧠 Key Takeaway
Database schemas must evolve alongside your code. In CD, migrations *must* run automatically and deterministically. If a migration fails, the code deployment is halted, preventing a state where new code tries to talk to an old database schema.
