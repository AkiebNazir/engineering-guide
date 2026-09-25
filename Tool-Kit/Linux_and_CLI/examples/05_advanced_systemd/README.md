# Advanced Systemd

**Goal:** Learn the typical workflow for creating, enabling, starting, and inspecting systemd services in Linux.

**Key Concepts:** [System Administration](../../Linux_and_CLI.md#system-administration)

**Prerequisites:** Linux environment with `systemd` (Note: macOS uses `launchd`, so this script acts as a simulation on non-Linux systems).

**Step-by-Step Execution:**
1. Run the script:
   ```bash
   ./setup_service.sh
   ```
2. **Expected Output:** The script outputs the standard `systemctl` and `journalctl` commands needed to install and manage a `systemd` unit file (`my-app.service`) running a python server (`server.py`).

**Try it yourself:** 
Review `my-app.service` to understand how the `ExecStart` directive points to `server.py`. If you are on a Linux machine, try actually running the commands printed by the script using `sudo`.

**Teardown:**
If you manually installed the service on Linux, remove it with:
```bash
sudo systemctl stop my-app
sudo systemctl disable my-app
sudo rm /etc/systemd/system/my-app.service
sudo systemctl daemon-reload
```
