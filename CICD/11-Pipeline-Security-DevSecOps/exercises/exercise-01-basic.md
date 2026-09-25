# Exercise 1: SAST with Bandit 🟢

## 🎯 Objective
Learn how to use Static Application Security Testing (SAST) on Python code using `bandit`.

## 📋 Prerequisites
- Python 3 installed
- `pip` installed

## 📝 Instructions

1. **Create the vulnerable application**
   Create a file named `app.py`:
   ```python
   # app.py
   import sqlite3
   from flask import Flask, request
   
   app = Flask(__name__)
   
   @app.route('/user')
   def get_user():
       username = request.args.get('username')
       conn = sqlite3.connect('database.db')
       cursor = conn.cursor()
       
       # VULNERABILITY: SQL Injection
       query = f"SELECT * FROM users WHERE username = '{username}'"
       cursor.execute(query)
       
       return str(cursor.fetchall())
       
   if __name__ == '__main__':
       app.run(debug=True) # VULNERABILITY: Debug mode enabled
   ```

2. **Install Bandit**
   ```bash
   pip install bandit
   ```

3. **Run Bandit**
   ```bash
   bandit -r app.py
   ```

4. **Analyze the output**
   Notice how Bandit flags multiple issues (SQL injection, and Flask debug mode).

5. **Fix the code**
   Update `app.py` to fix the issues:
   ```python
   import sqlite3
   from flask import Flask, request
   
   app = Flask(__name__)
   
   @app.route('/user')
   def get_user():
       username = request.args.get('username')
       conn = sqlite3.connect('database.db')
       cursor = conn.cursor()
       
       # FIXED: Use parameterized queries
       query = "SELECT * FROM users WHERE username = ?"
       cursor.execute(query, (username,))
       
       return str(cursor.fetchall())
       
   if __name__ == '__main__':
       # FIXED: Debug mode disabled
       app.run(debug=False)
   ```

6. **Re-run Bandit**
   ```bash
   bandit -r app.py
   ```
   The scan should now pass with no high-severity issues.

## 💡 Hints
- Parameterized queries (`?` in sqlite3) prevent SQL injection by ensuring input is treated as data, not executable code.

## ✅ Expected Output
Before fix:
```text
Run started: ...
Test results:
>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector through string-based query construction.
   Severity: Medium   Confidence: Low
   CWE: CWE-89 (https://cwe.mitre.org/data/definitions/89.html)
   Location: app.py:12:12

>> Issue: [B201:flask_debug_true] A Flask app appears to be run with debug=True, which exposes the Werkzeug debugger and allows the execution of arbitrary code.
   Severity: High   Confidence: Medium
...
```

After fix:
```text
Run started: ...
No issues identified.
```

## 🧠 Key Takeaway
SAST tools like Bandit catch common security flaws (like SQL injection and misconfigurations) directly in the source code before the application is even built.
