# Basic Environment Variables

**Goal:** Demonstrates the traditional (and risky) way of handling secrets using a `.env` file and the `python-dotenv` library.
**Key Concepts:** [The Problem with Secret Sprawl](../../Secret_Management.md#the-problem)
**Prerequisites:** Python 3, `python-dotenv` library installed.
**Step-by-Step Execution:**
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file in this directory:
   ```env
   API_KEY=my_super_secret_key
   DB_PASSWORD=my_db_password
   ```
3. Run the Python script:
   ```bash
   python main.py
   ```
   *Expected output:*
   `API Key loaded successfully (masking for security).`

**Try it yourself:** Remove or rename the `.env` file and run the script again to see how it handles missing secrets.
**Teardown:** Delete the `.env` file you created.
