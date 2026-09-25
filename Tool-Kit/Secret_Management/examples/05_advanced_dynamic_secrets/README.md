# Advanced Dynamic Secrets (Database)

**Goal:** Demonstrates generating short-lived PostgreSQL credentials on-demand, eliminating the need for long-lived, shared credentials.
**Key Concepts:** [Dynamic Secrets](../../Secret_Management.md#secret-engines)
**Prerequisites:** HashiCorp Vault installed, PostgreSQL running locally (on port 5432 with user `postgres` and password `rootpassword`).
**Step-by-Step Execution:**
1. Start a local Vault dev server in a new terminal:
   ```bash
   vault server -dev -dev-root-token-id="root"
   ```
2. Run the bash script:
   ```bash
   ./run.sh
   ```
   *Expected output:* The script enables the database engine, configures the connection, creates a role, and requests dynamic credentials. You should see a set of dynamically generated credentials (`username` and `password`) output to the console, valid for 1 hour.

**Try it yourself:** Try changing the `default_ttl` in the role creation command to `5m` (5 minutes) and request new credentials.
**Teardown:** Stop the Vault dev server running in the other terminal.
