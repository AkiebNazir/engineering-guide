# Advanced AppRole Authentication

**Goal:** Shows how to configure AppRole authentication, which is designed for machine-to-machine (M2M) communication. Applications use a RoleID and SecretID to authenticate.
**Key Concepts:** [AppRole Authentication Method](../../Secret_Management.md#authentication-methods)
**Prerequisites:** HashiCorp Vault installed and available in your PATH.
**Step-by-Step Execution:**
1. Start a local Vault dev server in a new terminal:
   ```bash
   vault server -dev -dev-root-token-id="root"
   ```
2. Run the bash script:
   ```bash
   ./run.sh
   ```
   *Expected output:* The script will enable AppRole, create a policy, create an AppRole, fetch the RoleID and SecretID, and finally log in using those credentials. You should see a successful authentication response returning a Vault token.

**Try it yourself:** Modify the script to use the generated Vault token to read a secret from `secret/data/my-app`.
**Teardown:** Stop the Vault dev server running in the other terminal.
