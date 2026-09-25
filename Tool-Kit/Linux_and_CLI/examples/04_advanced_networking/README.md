# Advanced Networking

**Goal:** Debug and inspect networking connections, DNS resolution, and listening ports using common network tools.

**Key Concepts:** [System Administration](../../Linux_and_CLI.md#system-administration)

**Prerequisites:** Linux or macOS environment (bash/zsh shell). Some tools like `ss` are Linux-specific but a fallback is provided.

**Step-by-Step Execution:**
1. Run the script:
   ```bash
   ./network_debug.sh
   ```
2. **Expected Output:** The script will `ping` a target, resolve its DNS using `dig`, fetch HTTP headers via `curl -I`, and list active listening ports using `ss` (or `netstat` on macOS).

**Try it yourself:** 
Change the `TARGET` variable in the script to a different domain like `google.com` and observe the differences in HTTP headers and DNS resolution records.

**Teardown:**
No cleanup is required.
