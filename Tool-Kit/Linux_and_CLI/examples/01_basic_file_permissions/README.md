# Basic File Permissions

**Goal:** Understand how to view and modify file permissions (`chmod`), ownership (`chown`), and apply the sticky bit on directories.

**Key Concepts:** [File Permissions](../../Linux_and_CLI.md#file-permissions)

**Prerequisites:** Linux or macOS environment (bash/zsh shell).

**Step-by-Step Execution:**
1. Run the script:
   ```bash
   ./setup_permissions.sh
   ```
2. **Expected Output:** You will see a `shared_dir` created with `755` permissions, a file inside with `644` permissions, and the sticky bit `+t` applied to the directory.

**Try it yourself:** 
Create a new file `test.txt`. Use `chmod 600 test.txt` and try to read it with another user account (if available) or observe the restricted access permissions using `ls -l`.

**Teardown:**
```bash
rm -rf shared_dir
```
