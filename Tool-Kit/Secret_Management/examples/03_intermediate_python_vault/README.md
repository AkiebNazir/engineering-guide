# Intermediate Python Vault

**Goal:** Demonstrates how to connect to HashiCorp Vault using the Python `hvac` library to securely fetch secrets at runtime.
**Key Concepts:** [Python Code Example](../../Secret_Management.md#python-example)
**Prerequisites:** HashiCorp Vault installed, Python 3, and `hvac` library installed.
**Step-by-Step Execution:**
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start a local Vault dev server in a new terminal:
   ```bash
   vault server -dev -dev-root-token-id="root"
   ```
3. In your current terminal, write a secret for the Python script to read:
   ```bash
   export VAULT_ADDR='http://127.0.0.1:8200'
   vault kv put secret/my-app my_key="my_value"
   ```
4. Run the Python script:
   ```bash
   python main.py
   ```
   *Expected output:*
   ```
   Successfully authenticated to Vault!
   Retrieved keys: ['my_key']
   ```

**Try it yourself:** Modify the Python script to print out the actual values of the secrets retrieved, rather than just the keys.
**Teardown:** Stop the Vault dev server running in the other terminal.
