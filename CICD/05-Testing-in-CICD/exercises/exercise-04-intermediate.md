# Exercise 04: Python Integration Testing with SQLite 🟡

## 🎯 Objective
Write an integration test in Python that interacts with a real (but temporary) SQLite database using pytest fixtures.

## 📋 Prerequisites
- Python installed.
- `pip install pytest`

## 📝 Instructions

1. Write a simple Python module that saves users to an SQLite database.
2. Write an integration test that creates a temporary database on disk (or in memory) using a fixture, runs the database operations, and tears it down afterwards.

### Step 1: Write the Database Code
Create `db.py`:

```python
import sqlite3

class UserRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            ''')

    def add_user(self, name):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
            return cursor.lastrowid

    def get_user_by_name(self, name):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM users WHERE name = ?", (name,))
            return cursor.fetchone()
```

### Step 2: Write the Integration Test
Create `test_db.py`. We will use Pytest's built-in `tmp_path` fixture to create a temporary database file.

```python
import pytest
from db import UserRepository

# Setup a fixture that provides a fresh database for each test
@pytest.fixture
def repo(tmp_path):
    # tmp_path is a built-in pytest fixture providing a temporary directory unique to the test invocation
    db_file = tmp_path / "test_users.db"
    
    # Initialize repository with the temporary db file
    repository = UserRepository(str(db_file))
    
    # Yield the repo to the test
    yield repository
    
    # Teardown: No strict manual deletion is required since tmp_path is managed by pytest,
    # but you could add cleanup logic here if needed.

def test_add_and_retrieve_user(repo):
    # 1. Action: Add a user
    user_id = repo.add_user("Alice")
    
    # 2. Assert: Check return ID
    assert user_id is not None
    
    # 3. Action: Retrieve the user
    user = repo.get_user_by_name("Alice")
    
    # 4. Assert: Check the retrieved data matches database state
    assert user is not None
    assert user[0] == user_id
    assert user[1] == "Alice"

def test_user_not_found(repo):
    user = repo.get_user_by_name("NonExistent")
    assert user is None
```

### Step 3: Run the Tests
```bash
pytest -v test_db.py
```

## 💡 Hints
- The `yield` statement in a pytest fixture separates setup code (before `yield`) from teardown code (after `yield`).
- `tmp_path` is extremely useful for file-system-level integration tests because pytest automatically cleans up the temporary directories later.
- Why is this an integration test? Because it tests the integration between our Python code and the actual SQLite database engine, rather than mocking it out.

## 🧠 Key Takeaway
Integration tests verify that your code works properly with external systems (like files or databases). By utilizing temporary databases and fixtures, you ensure that tests are repeatable and don't pollute your local environment.
