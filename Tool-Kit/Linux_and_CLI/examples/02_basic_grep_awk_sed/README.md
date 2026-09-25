# Grep, Awk, Sed

**Goal:** Parse, filter, and modify text streams using a pipeline of classic CLI text processing tools.

**Key Concepts:** [Essential CLI Tools](../../Linux_and_CLI.md#essential-cli-tools)

**Prerequisites:** Linux or macOS environment (bash/zsh shell).

**Step-by-Step Execution:**
1. Run the script:
   ```bash
   ./process_logs.sh
   ```
2. **Expected Output:** The script creates a mock `server.log` file, filters for "ERROR" lines using `grep`, extracts the IP addresses using `awk`, finds unique ones, and formats the output string using `sed`.

**Try it yourself:** 
Modify the pipeline in `process_logs.sh` to extract the "INFO" logs instead, and format them to say `Authorized IP: <IP>`.

**Teardown:**
```bash
rm server.log
```
