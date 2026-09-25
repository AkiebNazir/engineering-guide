# Intermediate Processes

**Goal:** Learn to manage background processes, find PIDs, check open files, and gracefully or forcefully terminate processes.

**Key Concepts:** [Kernel vs User Space](../../Linux_and_CLI.md#kernel-vs-user-space), [Essential CLI Tools](../../Linux_and_CLI.md#essential-cli-tools)

**Prerequisites:** Linux or macOS environment (bash/zsh shell).

**Step-by-Step Execution:**
1. Run the script:
   ```bash
   ./manage_processes.sh
   ```
2. **Expected Output:** A background `sleep` process will start. The script finds its PID using `$!`, attempts to list open files using `lsof`, gracefully kills it with `SIGTERM (15)`, and verifies its termination.

**Try it yourself:** 
Run `sleep 1000 &` in your terminal. Use `pgrep sleep` to find its PID, and manually kill it using `kill -9 <PID>`.

**Teardown:**
No cleanup is required as the script terminates the processes it creates.
