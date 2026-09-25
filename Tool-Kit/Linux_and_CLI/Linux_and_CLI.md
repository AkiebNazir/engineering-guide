# Linux & CLI Mastery

## Interactive Examples
We provide interactive examples to help you master these concepts practically. Check out the `examples/` directory:
- [01_basic_file_permissions](examples/01_basic_file_permissions)
- [02_basic_grep_awk_sed](examples/02_basic_grep_awk_sed)
- [03_intermediate_processes](examples/03_intermediate_processes)
- [04_advanced_networking](examples/04_advanced_networking)
- [05_advanced_systemd](examples/05_advanced_systemd)
## Linux OS Architecture

```arch
node hw "Hardware" at 0,0 icon=server
node kernel "Kernel" at 1,0 icon=cpu
node shell "Shell" at 2,0 icon=cli
node apps "Apps" at 3,0 icon=app
hw -> kernel
kernel -> shell
shell -> apps
```

## Kernel vs User Space
- **Kernel Space**: The core of the OS with full access to hardware. Manages CPU, memory, IPC, and device drivers.
- **User Space**: Where user applications run. Restricted access; must use system calls (syscalls) to request kernel services.

## File Permissions
> [!TIP]
> Practice changing permissions and ownership in the [Basic File Permissions example](examples/01_basic_file_permissions).
- **chmod**: Change access permissions. e.g., `chmod 755 file.sh` (rwx for owner, rx for group and others).
- **chown**: Change file owner and group. e.g., `chown user:group file.txt`.
- **Sticky Bit**: If set on a directory (e.g., `/tmp`), only the file owner, directory owner, or root can rename or delete files within it. Set with `chmod +t /dir` or `chmod 1777 /dir`.

## Essential CLI Tools
> [!TIP]
> Try searching and parsing text in the [Grep, Awk, Sed example](examples/02_basic_grep_awk_sed), and learn to manage processes in the [Intermediate Processes example](examples/03_intermediate_processes).
- **grep**: Search text using regex. `grep -E "^[0-9]+" file.txt`
- **awk**: Columnar data parsing. `awk -F',' '{print $1, $3}' data.csv`
- **sed**: Stream editor for regex replacements. `sed -i 's/foo/bar/g' file.txt`
- **find**: Search files and execute commands. `find /var/log -type f -name "*.log" -exec rm {} \;`
- **top/htop**: Real-time process and system resource monitors.
- **lsof**: List open files. `lsof -i :8080` to find what's listening on port 8080.
- **curl**: Transfer data from/to a server. `curl -I https://example.com` (fetch headers).
- **tar**: Archive utility. `tar -czvf archive.tar.gz /folder` (create), `tar -xzvf archive.tar.gz` (extract).

## System Administration
> [!TIP]
> Explore network sockets and DNS in the [Advanced Networking example](examples/04_advanced_networking) and practice managing systemd services in the [Advanced Systemd example](examples/05_advanced_systemd).
- **systemctl**: Control systemd services. `systemctl restart nginx`, `systemctl status postgresql`.
- **journalctl**: Query the systemd journal logs. `journalctl -u nginx.service -f` (follow logs).
- **Networking**:
  - **ss**: Socket statistics (replaces netstat). `ss -tulpn`.
  - **dig**: DNS lookup utility. `dig +short A example.com`.

## 10 MAANG-Level Interview Questions

1. **What happens when you type `ls` in the terminal and press Enter?**
   - The shell parses the input, forks a new process, and uses `execve` to load the `ls` binary. The kernel allocates memory, loads shared libraries, and executes the program. It makes `getdents` syscalls to read directory contents, formats the output, and writes to `stdout`.
2. **What is a zombie process, and how do you kill it?**
   - A process that has completed execution but still has an entry in the process table because its parent hasn't read its exit status (`wait()` syscall). You cannot `kill -9` a zombie (it's already dead); you must kill its parent or wait for init/systemd to reap it.
3. **Explain load average. What does a load of 1.0 on a single-core machine mean?**
   - It represents the average system load (processes using or waiting for CPU/uninterruptible I/O) over 1, 5, and 15 minutes. On a single core, 1.0 means the CPU is exactly at 100% capacity with no processes waiting.
4. **How do you troubleshoot a "Disk Full" issue when `df -h` shows 100% full but `du -sh *` shows only a few megabytes used?**
   - This happens when a large file is deleted but a running process still has an open file descriptor to it. Use `lsof +L1` to find open deleted files, then restart the holding process.
5. **What are inodes?**
   - Data structures that store metadata about a file (permissions, owner, size, timestamps, disk block pointers) but not the file name or data itself.
6. **Hard links vs. Soft links?**
   - Hard links point directly to the same inode as the original file (only works on the same filesystem, cannot link directories). Soft (symbolic) links point to the file path (can cross filesystems and link directories).
7. **Explain the TCP 3-way handshake and how you can observe it.**
   - SYN -> SYN-ACK -> ACK. You can observe this using `tcpdump` (e.g., `tcpdump -i eth0 tcp port 80`).
8. **What is the sticky bit, and where is it commonly used?**
   - It restricts file deletion inside a shared directory to only the file owner. Commonly used on `/tmp`.
9. **Difference between Character and Block devices?**
   - Character devices (e.g., `/dev/tty`) transfer data unbuffered, character by character. Block devices (e.g., `/dev/sda`) transfer data in blocks and usually have file systems mounted on them.
10. **How do you find the 10 largest files in a directory structure?**
    - `find . -type f -exec du -h {} + | sort -rh | head -n 10`
