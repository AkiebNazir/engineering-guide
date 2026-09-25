# Basic Vault CLI

**Goal:** Demonstrates how to start HashiCorp Vault in development mode and perform basic read/write operations using the Vault CLI.
**Key Concepts:** [Vault Secret Engines (KV)](../../Secret_Management.md#secret-engines)
**Prerequisites:** HashiCorp Vault installed and available in your PATH.
**Step-by-Step Execution:**
1. Run the bash script:
   ```bash
   ./run.sh
   ```
   *Expected output:* You should see Vault starting in dev mode, a secret being written to `secret/my-app`, and the same secret being read back to the console. The script will then automatically clean up and kill the Vault process.

**Try it yourself:** Modify `run.sh` to write an additional key-value pair (e.g., `api_secret=super_secret`) and read it back.
**Teardown:** The script automatically kills the background Vault process. If it fails, manually find and kill the Vault process (`pkill vault`).
