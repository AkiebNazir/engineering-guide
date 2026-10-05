# CLI and Linux System Mastery

A backend engineer spends a large share of every week in a terminal: reading logs,
poking an API, finding out why a port is closed, restarting a service, and working out
why a box is slow. This chapter starts from what a shell actually is and how commands,
pipes and processes fit together, then builds the toolkit you use on a real Linux server:
text processing, `curl`/`jq`, permissions and disks, processes and signals, `systemd`,
network debugging and a first-minutes performance triage. The payoff is being the person
who can slice through gigabytes of logs and prove where a failure is, instead of
guessing from a dashboard.

## Foundations — What is a shell, and how do commands work together?

### The problem it solves

A server has no screen, no mouse and often no desktop at all. You reach it over SSH and
all you get is a text prompt. Everything you need to do (read files, start programs,
inspect the network) has to be expressible as short text commands, and many of those
jobs are bigger than any one command. The Unix answer, from the 1970s and still the way
Linux works in 2026, is: **many small programs that each do one thing well, joined by
pipes** so the output of one becomes the input of the next.

### The pieces

| Piece | What it is | Everyday analogy |
|---|---|---|
| **Terminal** (emulator) | The window that draws characters and sends your keystrokes. | The phone handset |
| **Shell** (`bash`, `zsh`, `sh`) | A program that reads a line, expands variables and wildcards, then starts the programs you named. | The operator who connects your call |
| **Command** | Almost always just an executable file somewhere on `$PATH` (`/usr/bin/grep`). A few (`cd`, `export`, `set`) are shell *builtins*. | The person you called |
| **Process** | A running copy of a program, with a PID, an owner, open files and an exit code. | The call in progress |
| **Kernel** | Runs processes, owns files, sockets and devices; everything above talks to it through system calls. | The telephone exchange |

Three facts carry most of the rest of this chapter:

1. **Every process starts with three open file descriptors**: `0` stdin, `1` stdout,
   `2` stderr. Programs read from 0 and write results to 1 and complaints to 2. The
   shell decides where each one points (the terminal, a file, a pipe).
2. **A pipe connects one process's stdout to the next one's stdin.** The processes in a
   pipeline run *at the same time*; the kernel buffers ≈64 KiB between them and makes the
   writer wait if the reader is slow. That is why `grep` on a 20 GB log piped into `head`
   finishes instantly: `head` exits after 10 lines and `grep` is killed by `SIGPIPE`.
3. **Every process ends with an exit code**: `0` means success, anything else is a
   failure. `&&`, `||`, `if` and `set -e` all read that number. This is how scripts
   make decisions.

```arch
%% caption: A pipeline runs every command at once. stdout flows through kernel pipes; stderr skips the pipe and still reaches the terminal.
grid 150x110
node sh "bash" at 1,0 icon=cli sub="parses, forks, wires fds"
node g "grep ERROR app.log" at 0,1 icon=search sub="reads the file"
node s "sort" at 1,1 icon=sort sub="buffers all input"
node u "uniq -c" at 2,1 icon=counter sub="counts runs"
node term "Terminal" at 1,2 icon=desktop sub="final stdout + all stderr"
sh -> g
sh -> s
sh -> u
g -> s : "pipe"
s -> u : "pipe"
u -> term : "stdout"
g ..> term : "stderr"
```

### A concrete example

"Which client IPs hit our API most in the last log file?"

```bash
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -5
```

`awk` prints column 1 (the IP) of each line, `sort` puts equal IPs next to each other,
`uniq -c` collapses each run into "count IP", `sort -rn` orders by count, largest first,
and `head -5` keeps the top five. Five tiny programs, one question answered, no script
written. Most of this chapter is learning more of these building blocks and knowing when
each is the right one.

### Everything is a file (mostly)

Linux exposes a surprising amount as files you can `cat`: `/proc/<pid>/` holds a live
view of each process (its command line, environment, open files, memory maps),
`/proc/meminfo` and `/proc/loadavg` hold system counters, `/sys/` exposes devices and
cgroups, and `/dev/` holds devices. Many debugging tools are thin readers of these files.
`man <command>` is the manual for any command, and `tldr <command>` (a separate package)
gives the five examples you usually want.

## 1. Shell essentials: redirection, quoting, exit codes and safe scripts

### Redirection

| Syntax | Meaning |
|---|---|
| `cmd > out.txt` | stdout to a file (truncate) |
| `cmd >> out.txt` | stdout to a file (append) |
| `cmd 2> err.txt` | stderr to a file |
| `cmd > all.txt 2>&1` | both to the same file (order matters: redirect 1 first, then point 2 at 1) |
| `cmd &> all.txt` | bash shorthand for the line above |
| `cmd < in.txt` | stdin from a file |
| `cmd1 \| cmd2` | stdout of cmd1 into stdin of cmd2 |
| `cmd1 \|& cmd2` | stdout *and* stderr into cmd2 (bash) |
| `cmd > /dev/null 2>&1` | discard everything |
| `diff <(sort a) <(sort b)` | process substitution: pass a command's output as if it were a file |

A classic mistake: `cmd 2>&1 > file` sends stderr to the *terminal*, because `2>&1`
copies wherever fd 1 pointed at that moment (still the terminal), and only then is fd 1
moved to the file.

### Quoting and expansion

The shell rewrites your line before running anything: `$VAR` and `$(cmd)` are expanded,
unquoted results are **split on whitespace** and **globbed** (`*.log`). Rules that
prevent most shell bugs:

- Always quote variables: `rm -- "$file"`, not `rm $file`. A filename with a space in it
  becomes two arguments otherwise, and an empty variable vanishes entirely.
- Single quotes are literal (`'$HOME'` stays `$HOME`); double quotes expand variables
  but not globs.
- Use `$(...)` for command substitution, not backticks (it nests and reads cleanly).
- `--` ends option parsing, so a file named `-rf` is treated as a file.

### Exit codes and control flow

```bash
grep -q "ready" status.txt && echo "up" || echo "not up"
if ! curl -fsS http://localhost:8080/healthz > /dev/null; then
  echo "health check failed" >&2
  exit 1
fi
echo "last exit code: $?"
```

`curl -f` makes HTTP errors (≥ 400) produce a non-zero exit code; without it, a 500
response is a "successful" curl.

### A safe script template

```bash
#!/usr/bin/env bash
# Rotate old logs: compress *.log older than N days under a directory.
set -euo pipefail          # exit on error, on unset variables, and on failures inside pipes
IFS=$'\n\t'                # split only on newlines and tabs, not spaces

usage() { echo "usage: $0 <dir> [days]" >&2; exit 2; }
[[ $# -ge 1 ]] || usage
dir=$1
days=${2:-7}

tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT   # cleanup runs on success, error or Ctrl-C

count=0
while IFS= read -r -d '' f; do
  gzip -- "$f"
  count=$((count + 1))
done < <(find "$dir" -type f -name '*.log' -mtime +"$days" -print0)

echo "compressed $count file(s) in $dir" >&2
```

`set -o pipefail` matters more than it looks: without it, `false | true` succeeds,
so a failed `pg_dump | gzip > backup.gz` leaves you a "successful" empty backup. `set -e`
has well-known holes (it is ignored inside `if` conditions and in functions called from
them), so it is a safety net, not a substitute for checking the commands that matter.
Run `shellcheck` on every script; it catches unquoted variables, the `2>&1` ordering
bug and most of the rest of this section automatically.

When a script grows past ≈100 lines, needs data structures, or needs real error
handling, rewrite it in Python or Go.

## 2. Text processing: the core utilities

### `grep` (and `ripgrep`)

```bash
grep -rin "error" /var/log/app/       # recursive, case-insensitive, with line numbers
grep -v "DEBUG" app.log               # invert: drop DEBUG lines
grep -E "5[0-9]{2} " access.log       # extended regex: any 5xx status
grep -c "timeout" app.log             # count matching lines
grep -B3 -A10 "Traceback" app.log     # 3 lines before, 10 after each match
grep -F "user[42]" app.log            # fixed string, no regex (faster, no escaping)
zgrep "ERROR" app.log.1.gz            # search compressed rotated logs
```

`rg` (ripgrep) is the modern default on a workstation: recursive by default, respects
`.gitignore`, multithreaded, usually much faster on big trees. On a minimal server image
you will still only have `grep`, so know both.

### `find`

```bash
find . -name "*.log" -mtime +7                 # modified more than 7 days ago
find /var -type f -size +500M                  # files over 500 MB
find . -type d -name node_modules -prune       # match directories, don't descend
find /tmp -user appuser -mmin -30              # owned by appuser, changed in the last 30 min
find . -name "*.log" -mtime +7 -delete         # delete directly: safest
```

### `xargs`: turn lines into arguments

The owner's original example, `find . -name "*.log" -mtime +7 | xargs rm`, breaks on any
filename containing a space or newline (`my app.log` becomes `my` and `app.log`) and
runs `rm` with no arguments if nothing matched. The robust forms:

```bash
find . -name "*.log" -mtime +7 -print0 | xargs -0 -r rm --     # NUL-separated, skip if empty
find . -name "*.png" -print0 | xargs -0 -P 8 -n 50 optipng     # 8 parallel jobs, 50 files each
cat hosts.txt | xargs -I{} ssh {} uptime                        # one command per line, {} substituted
```

`find … -exec cmd {} +` does the same batching as `xargs` without a pipe.

### `awk`: columns and small programs

`awk` splits every line into fields `$1 … $NF` and runs a pattern/action program on it.

```bash
awk '{print $4, $5}' access.log                           # columns 4 and 5 (no `cat` needed)
awk -F, '$3 > 100 {print $1}' orders.csv                  # comma-separated, filter on column 3
awk '$9 >= 500 {n++} END {print n+0, "server errors"}' access.log
awk '{s += $NF; c++} END {printf "avg %.1f ms\n", s/c}' latency.log
awk '{sum[$1] += $10} END {for (ip in sum) print sum[ip], ip}' access.log | sort -rn | head
```

The last line is a GROUP BY in one line: total bytes per client IP.

### `sed`: stream editing

```bash
sed -n '100,120p' big.log                       # print only lines 100-120
sed '/^#/d' config.ini                          # delete comment lines
sed -E 's/password=[^ ]+/password=***/g' app.log  # redact
sed -i.bak 's#http://#https://#g' config.yaml   # in-place, keep a .bak copy
```

The owner's `sed -i 's/http/https/g'` would also turn every existing `https` into
`httpss`. Match what you actually mean (`http://`), and pick a delimiter such as `#`
so you don't have to escape slashes. On macOS (BSD sed) `-i` needs an explicit
argument (`sed -i '' …`); GNU sed on Linux does not. For YAML or JSON prefer a tool that
understands the format (`yq`, `jq`) over regex.

### The rest of the kit

| Tool | Job | Example |
|---|---|---|
| `sort` / `uniq` | order, dedupe, count runs | `sort \| uniq -c \| sort -rn` |
| `cut` | fixed columns by delimiter | `cut -d: -f1 /etc/passwd` |
| `tr` | translate or delete characters | `tr -s ' '` (squeeze spaces), `tr A-Z a-z` |
| `wc` | count lines/words/bytes | `wc -l` |
| `head` / `tail` | start / end of a file | `tail -F app.log` follows across log rotation (`-f` loses the file when it is renamed) |
| `less` | page a huge file without loading it | `/pattern`, `n`, `G`, `F` (follow) |
| `tee` | copy stdin to a file *and* stdout | `cmd \| tee out.log` |
| `column -t` | align columns | `mount \| column -t` |
| `comm` / `diff` | compare sorted lists / files | `comm -13 old.txt new.txt` (lines only in new) |

### A worked example: find the slow endpoints

Given an access log whose last field is the request time in seconds:

```bash
awk '{print $7, $NF}' access.log \
  | awk '{t[$1]+=$2; c[$1]++} END {for (p in t) printf "%8.3f %6d %s\n", t[p]/c[p], c[p], p}' \
  | sort -rn | head -10
```

Output: average seconds, request count, path. The same pattern (extract, aggregate,
sort, top-N) answers "which user", "which status", "which minute" questions in seconds
without loading anything into a database.

## 3. API debugging: `curl` and `jq`

### `curl`

```bash
# POST JSON with headers (--json sets Content-Type and Accept for you; curl ≥ 7.82)
curl -X POST https://api.example.com/v1/users \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "Alice"}'
curl --json '{"name": "Alice"}' -H "Authorization: Bearer $TOKEN" https://api.example.com/v1/users

curl -i  https://example.com          # include response headers
curl -I  https://example.com          # HEAD request: headers only
curl -v  https://example.com          # connection, TLS handshake, request and response headers
curl -sSfL https://example.com/x.sh   # silent, but show errors; fail on HTTP >= 400; follow redirects
curl --resolve api.example.com:443:10.0.1.5 https://api.example.com/healthz   # bypass DNS, keep SNI/Host
curl -H "Host: api.example.com" http://10.0.1.5/healthz                       # hit one backend directly
curl --retry 3 --retry-all-errors --max-time 10 https://example.com
```

Where did the time go? `curl -w` prints the timing of each phase:

```bash
curl -o /dev/null -sS -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total} code=%{http_code}\n' https://example.com
```

Each value is cumulative from the start. A large `dns` points at the resolver; a large
gap between `tls` and `ttfb` is the server thinking (your application, or its
database). Two things to avoid: putting a real token directly on the command line (it
lands in shell history and is visible in `ps` to other users; read it from a variable or
`-H @file`), and `curl -k`, which turns off certificate checking and hides exactly the
TLS problems you are debugging.

### `jq`

```bash
curl -s https://api.github.com/repos/torvalds/linux | jq .            # pretty-print
curl -s https://api.example.com/users | jq '.[].email'                # a field from each element
jq -r '.items[] | select(.status == "failed") | .id' jobs.json        # filter; -r = raw strings
jq '[.[] | {id, name}]' users.json                                     # reshape
jq 'group_by(.region) | map({region: .[0].region, n: length})' hosts.json
kubectl get pods -o json | jq -r '.items[] | select(.status.phase != "Running") | .metadata.name'
jq -c . big.json                                                        # compact, one line
```

For structured logs (one JSON object per line), `jq` handles each line as its own input:
`jq -r 'select(.level == "error") | [.ts, .msg] | @tsv' app.jsonl`.

## 4. Files, permissions and disks

### Permissions

`ls -l` shows `-rwxr-x---  1 app app ...`: file type, then read/write/execute for the
**user** (owner), **group** and **others**. Octal packs each triplet into a digit
(r = 4, w = 2, x = 1).

| Command | Effect |
|---|---|
| `chmod 640 secret.conf` | owner rw, group r, others nothing |
| `chmod u+x deploy.sh` | add execute for the owner |
| `chown app:app /srv/app -R` | change owner and group recursively |
| `umask 027` | new files default to 640, directories to 750 |
| `sudo -u app cmd` | run as another user |
| `id`, `groups` | who am I, which groups |

On a directory, `x` means "may enter/traverse" and `r` means "may list". Special bits:
**setuid** on an executable runs it as its owner (`/usr/bin/passwd`), a classic privilege
escalation target; the **sticky bit** on `/tmp` means only a file's owner can delete it.
`Permission denied` with correct mode bits usually means a parent directory is missing
`x`, an ACL (`getfacl`) or an SELinux/AppArmor policy (`ls -Z`, `ausearch -m avc`).

### Disks and the "disk is full but `du` disagrees" puzzle

```bash
df -h                 # free space per filesystem
df -i                 # free inodes: millions of tiny files can fill a disk with space left
du -sh /var/log/* | sort -h | tail     # biggest directories
ncdu /                # interactive version
lsof +L1              # open files whose link count is 0: deleted but still held open
```

When `df` says 100% and `du` cannot find the space, a process is almost always still
writing to a log file that someone deleted with `rm`. The directory entry is gone but
the inode lives until the last file descriptor closes. Fix: restart or signal the
process to reopen its logs, or truncate through `/proc`:
`: > /proc/<pid>/fd/<n>`. Next time, use `logrotate` with `copytruncate` or have the
app reopen on `SIGHUP`.

## 5. Processes and signals

### Seeing processes

```bash
ps aux --sort=-%mem | head              # top memory users
ps -eo pid,ppid,stat,etime,cmd --forest # tree, state, elapsed time
pgrep -af gunicorn                      # PIDs + command lines by name
top / htop                              # live view; in top press 1 (per CPU), M (memory), P (CPU)
cat /proc/1234/status                   # state, threads, memory (VmRSS)
ls -l /proc/1234/fd | wc -l             # how many file descriptors are open
cat /proc/1234/limits                   # "Max open files" — the usual EMFILE culprit
```

The `STAT` column: `R` running, `S` sleeping (waiting for an event), `D`
uninterruptible sleep (almost always disk or NFS I/O; cannot be killed until the I/O
returns), `Z` zombie, `T` stopped.

### Signals

| Signal | Number | Default | Typical use |
|---|---|---|---|
| `SIGTERM` | 15 | terminate | "please shut down cleanly"; what `kill`, `systemctl stop` and Kubernetes send first |
| `SIGKILL` | 9 | terminate, cannot be caught | last resort; no cleanup, no flushing |
| `SIGINT` | 2 | terminate | Ctrl-C |
| `SIGHUP` | 1 | terminate | many daemons reload config or reopen logs on it (nginx, sshd) |
| `SIGQUIT` | 3 | core dump | Ctrl-\\; the JVM prints a thread dump, Go prints all goroutine stacks |
| `SIGSTOP` / `SIGCONT` | 19 / 18 | pause / resume | Ctrl-Z is `SIGTSTP` |
| `SIGPIPE` | 13 | terminate | writer's reader went away (the `head` example above) |
| `SIGCHLD` | 17 | ignore | a child exited; the parent should `wait()` for it |

`kill -9` first is a bad habit: the process cannot close connections, flush buffers or
remove its lock/PID file. Send `SIGTERM`, wait a grace period, then `SIGKILL`. That is
exactly what `systemd` (`TimeoutStopSec`, default 90 s) and Kubernetes
(`terminationGracePeriodSeconds`, default 30 s) do.

**Zombies** (`Z`) are processes that have exited but whose parent never called
`wait()`; they hold only a PID-table slot. You cannot kill a zombie; you fix or kill its
parent. **Orphans** are children whose parent died; they are adopted by PID 1 (or the
nearest subreaper). In a container, *your* app may be PID 1, which is why images use a
tiny init (`tini`, `docker run --init`) to reap zombies and forward signals.

### Load average

`uptime` prints three load averages (1, 5, 15 minutes). On Linux the number counts
tasks that are runnable **plus** tasks in `D` state, so a load of 16 on an 8-core box
can mean CPU saturation *or* a pile of threads stuck on a slow disk or NFS mount. Check
`vmstat 1` (`r` = run queue, `b` = blocked, `wa` = I/O wait) before concluding "we need
more CPU".

### Keeping work alive

`nohup cmd &` survives logout; `tmux` (or `screen`) keeps a whole interactive session
alive across disconnects and is what you want for a long migration over SSH. `jobs`,
`fg`, `bg` and `disown` manage background jobs of the current shell.

## 6. `systemd`: running services on a VM

In modern infrastructure Kubernetes restarts your processes, but on plain VMs (an EC2
instance, a bare-metal database host) and for the node's own daemons (kubelet,
containerd, sshd), **systemd** is the init system (PID 1) that starts services at boot,
restarts them when they crash, captures their logs and limits their resources through
cgroups.

A production-quality unit file (`/etc/systemd/system/myapp.service`):

```ini
[Unit]
Description=My Backend App
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=60
StartLimitBurst=5

[Service]
Type=simple
User=appuser
Group=appuser
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/server --port 8080
ExecReload=/bin/kill -HUP $MAINPID
EnvironmentFile=/etc/myapp/env
Restart=on-failure
RestartSec=2
TimeoutStopSec=30
LimitNOFILE=65536
MemoryMax=1G
CPUQuota=200%
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=/var/lib/myapp

[Install]
WantedBy=multi-user.target
```

What changed from the owner's original and why:

- `After=network.target` only orders you after the network *stack* is configured, not
  after the machine actually has an address. A service that connects out at startup
  wants `network-online.target` (both `Wants=` and `After=`).
- `Environment="DB_URL=postgres://..."` in the unit puts the secret in a file readable
  by `systemctl show` for any user. Use `EnvironmentFile=` with mode 600, or better,
  `LoadCredential=` (see [Secret Management](11_secret_management.md)).
- `Restart=always` also restarts a process that exited cleanly on purpose;
  `on-failure` is usually what you mean. `StartLimitBurst` stops a crash loop from
  restarting forever.
- `LimitNOFILE` raises the open-files limit (the default soft limit is often 1024, far
  too low for a busy server). `MemoryMax`/`CPUQuota` are cgroup limits, the same
  mechanism containers use.
- The `Protect*`/`NoNewPrivileges` lines are cheap sandboxing; `systemd-analyze security
  myapp` scores a unit.

```bash
sudo systemctl daemon-reload          # re-read unit files after editing
sudo systemctl enable --now myapp     # start at boot, and start now
systemctl status myapp                # state, last log lines, main PID, cgroup
sudo systemctl restart myapp          # stop + start
sudo systemctl reload myapp           # ExecReload (config reload without downtime)
systemctl list-units --failed         # everything that is broken
systemctl cat myapp                   # the effective unit, including drop-ins
sudo systemctl edit myapp             # create an override drop-in instead of editing the vendor file

journalctl -u myapp -f                # follow the service's logs
journalctl -u myapp --since "10 min ago" -p err   # errors only, recent
journalctl -b -1 -p warning           # warnings from the previous boot
journalctl -k                         # kernel messages (OOM kills, disk errors)
```

**Timers** replace cron for services: a `myjob.timer` with `OnCalendar=*-*-* 03:00:00`
and `Persistent=true` runs `myjob.service` daily and catches up after downtime, with its
output in the journal (`systemctl list-timers`).

## 7. Linux networking: proving where a connection fails

When a service "can't connect", walk the layers in order. Each step either passes or
tells you exactly which team owns the problem.

```arch
%% caption: Debug "can't connect" one layer at a time. Each rung has one command, and the first rung that fails names the layer that owns the problem.
grid 190x100
node q "Service A cannot reach B" at 1,0 shape=pill color=slate
node dns "1. Name resolves?" at 1,1 shape=card icon=dns sub="dig +short db.internal"
node rt "2. Route + interface?" at 1,2 shape=card icon=network sub="ip route get 10.0.3.7"
node tcp "3. TCP port open?" at 1,3 shape=card icon=connection sub="nc -vz 10.0.3.7 5432"
node tls "4. TLS handshake ok?" at 1,4 shape=card icon=lock sub="openssl s_client -connect"
node app "5. App answers?" at 1,5 shape=card icon=api sub="curl -v, logs on B"
node fdns "resolver, /etc/hosts, search domain" at 0,1 shape=text
node ffw "refused: nothing listens\ntimeout: firewall drops" at 2,3 shape=text
node fcert "expired cert, wrong SNI, missing CA" at 0,4 shape=text
q -> dns -> rt -> tcp -> tls -> app
dns .. fdns
tcp .. ffw
tls .. fcert
```

| Question | Command | Reading the answer |
|---|---|---|
| What are my addresses and routes? | `ip -br addr`, `ip route`, `ip route get 10.0.3.7` | `ifconfig`/`route` are deprecated (net-tools) |
| Does the name resolve, and to what? | `dig +short db.internal`, `dig @10.0.0.2 db.internal`, `getent hosts db.internal` | `getent` uses the same resolver path as your app (`/etc/nsswitch.conf`, `/etc/hosts`); `dig` asks DNS directly |
| What is listening here? | `ss -tulpn` | `ss` replaces `netstat`. `0.0.0.0:8080` = all interfaces, `127.0.0.1:8080` = local only (the classic "works on the box, not from outside") |
| What connections exist? | `ss -tan state established '( dport = :5432 )'`, `ss -s` | thousands of `TIME-WAIT` = many short-lived outbound connections; use keep-alive/pooling |
| Can I open the TCP port? | `nc -vz db.example.com 5432` | *Connection refused* = host reached, nothing listening (RST). *Timed out* = packets dropped (firewall, security group, wrong route). This distinction alone settles most arguments. |
| Is TLS right? | `openssl s_client -connect api:443 -servername api.example.com` | shows the chain, expiry, negotiated version |
| What is on the wire? | `tcpdump -i any -nn port 5432`, `tcpdump -i eth0 -A port 80`, `tcpdump -w cap.pcap` then open in Wireshark | the ultimate source of truth. Encrypted traffic shows handshakes and resets but not payloads |
| Where do packets die on the path? | `mtr -rwc 50 host`, `traceroute -T -p 443 host` | loss that starts at one hop and continues to the end is real; loss at a middle hop only is often ICMP rate limiting |

`telnet host port` still works as a port check, but most images no longer ship it;
`nc` or bash's `/dev/tcp` (`timeout 3 bash -c '</dev/tcp/10.0.3.7/5432' && echo open`)
are the portable choices.

### Firewalls: `iptables` and `nftables`

```bash
# Block all incoming traffic from one address (iptables syntax)
sudo iptables -A INPUT -s 192.168.1.50 -j DROP
# The nftables equivalent (the native framework on current distributions)
sudo nft add rule inet filter input ip saddr 192.168.1.50 drop
sudo nft list ruleset
```

Modern distributions (Debian 10+, RHEL 8+, Ubuntu 20.10+) run `nftables` in the kernel;
the `iptables` command there is usually `iptables-nft`, a compatibility front end that
writes nftables rules. `-A` appends, so the rule lands *after* any earlier `ACCEPT` and
may never match; `-I INPUT 1` inserts at the top. Rules added this way vanish on reboot
unless saved (`nft list ruleset > /etc/nftables.conf`, or `iptables-save`). On cloud VMs
the security group or network ACL is a second, separate firewall in front of the host,
and Kubernetes' kube-proxy and CNI plugins also program these tables, so read rules
before adding your own.

## 8. Performance triage: the first 60 seconds on a slow box

Brendan Gregg's well-known checklist is the right reflex when someone says "the server
is slow". It looks at every resource for **U**tilization, **S**aturation and
**E**rrors (the USE method) before you form a theory.

```bash
uptime                 # load averages: rising, falling, or flat?
dmesg -T | tail        # OOM kills, disk errors, TCP drops, hardware trouble
vmstat 1 5             # r (run queue) vs CPUs, free memory, si/so (swapping), us/sy/wa/st
mpstat -P ALL 1 3      # one hot CPU = a single-threaded bottleneck
pidstat 1 3            # which process uses the CPU
iostat -xz 1 3         # per-disk %util, await (ms), queue size
free -m                # "available" is what matters; "free" is low on a healthy box (page cache)
sar -n DEV 1 3         # network throughput per interface vs link speed
sar -n TCP,ETCP 1 3    # new connections/s, retransmits
top                    # confirm the picture
```

How to read the common outcomes:

| Symptom | Likely cause | Next tool |
|---|---|---|
| `us` high, one process on top | the app is CPU-bound | `perf top -p PID`, a profiler, a flame graph |
| `sy` high | syscall storm, lock contention, too many small writes | `strace -c -p PID` (short runs only: it slows the target a lot), `perf` |
| `wa` high, `iostat` await large | disk saturated | `iotop`, `pidstat -d 1` |
| `st` (steal) high | noisy neighbour on a shared VM | move instance type / host |
| `si`/`so` non-zero | swapping: memory pressure | `ps aux --sort=-rss`, check for leaks |
| `dmesg`: `Out of memory: Killed process` | the kernel OOM killer picked a victim | `journalctl -k`, cgroup `memory.max`, the app's real footprint |
| retransmits rising | network loss or a congested peer | `ss -ti` (per-connection `retrans`, `rtt`), `mtr` |
| `Too many open files` (EMFILE) | fd limit hit, or an fd leak | `/proc/PID/limits`, `ls /proc/PID/fd \| wc -l` |

`strace -f -e trace=network,file -p PID` shows what a stuck process is asking the kernel
for (waiting on `connect()` to a dead host, or looping on `open()` of a missing file).
`perf` and eBPF tools (`bpftrace`, the `bcc` tools such as `execsnoop`, `opensnoop`,
`biolatency`, `tcpretrans`) answer the same questions with far lower overhead and are
safe to use in production. The kernel side of all of this (scheduler, page cache, epoll)
is in [Operating Systems & Hardware Symbiosis](../../interview-core/CSFundamentals/01_operating_systems_deep_dive.md).

## 9. Working remotely: SSH, files and sessions

```bash
ssh-keygen -t ed25519 -C "you@laptop"                  # modern key type
ssh-copy-id app@10.0.1.5                               # install your public key on a host
ssh -J bastion.example.com app@10.0.1.5                # jump through a bastion (ProxyJump)
ssh -L 5433:db.internal:5432 bastion.example.com       # local forward: localhost:5433 -> db via bastion
rsync -avz --partial --progress ./build/ app@host:/srv/app/   # resumable, only changed files
scp file.tar.gz app@host:/tmp/
```

`~/.ssh/config` saves typing and keeps settings consistent:

```text
Host bastion
  HostName bastion.example.com
  User ops
  IdentityFile ~/.ssh/id_ed25519

Host 10.0.*
  User app
  ProxyJump bastion
  ServerAliveInterval 30
```

Avoid `ForwardAgent yes` to hosts you do not fully trust: root on that host can use your
agent socket to log in anywhere your key can. `ProxyJump` gives the same convenience
without exposing the agent. Many organizations now replace long-lived SSH keys with
short-lived SSH certificates or with a session manager (AWS Systems Manager Session
Manager, Teleport, Tailscale SSH), so access is tied to identity and audited.

## Common interview questions

**What happens when you type `ls -l | grep foo` and press Enter?**
The shell parses the line, creates a pipe, forks two children, connects the first
child's stdout and the second child's stdin to the pipe, and each child `exec`s its
program (found via `$PATH`). Both run concurrently; the shell waits for both, and the
pipeline's exit code is `grep`'s (the last command's) unless `pipefail` is set.

**How do you find the 10 IPs sending the most requests?**
`awk '{print $1}' access.log | sort | uniq -c | sort -rn | head`. Explain why `sort`
comes before `uniq` (uniq only collapses adjacent duplicates).

**The disk is full, but `du` shows plenty of space. Why?**
A process holds a deleted file open; the space is freed only when the last descriptor
closes. `lsof +L1` finds it; restart the process or truncate via `/proc/PID/fd/N`. Also
check `df -i` for inode exhaustion.

**`kill -9` versus `kill`?**
`kill` sends `SIGTERM`, which the process can catch to finish requests and clean up.
`SIGKILL` cannot be caught; the kernel removes the process immediately, so buffers are
lost and locks may be left behind. Use TERM, wait, then KILL.

**A service can't connect to the database. How do you debug it?**
Walk the ladder: DNS (`dig`/`getent`), route (`ip route get`), TCP (`nc -vz`: refused
means nothing listening, timeout means a firewall or security group drops it), TLS
(`openssl s_client`), then credentials and app logs. Check `ss -tulpn` on the DB host to
confirm it listens on the right interface, not only `127.0.0.1`.

**Load average is 20 on an 8-core machine. Is the CPU the problem?**
Not necessarily. Linux load counts runnable tasks plus tasks in uninterruptible I/O
sleep. Check `vmstat 1`: a large `r` with high `us`+`sy` is CPU; a large `b` with high
`wa` is storage or NFS.

**What is a zombie process and how do you get rid of it?**
A child that has exited but not been reaped by its parent's `wait()`. It uses only a
PID slot. Kill or fix the parent; PID 1 then adopts and reaps it. In containers, run an
init such as `tini` as PID 1.

**Why `set -euo pipefail` in bash scripts?**
Stop on failed commands, fail on unset variables (catches typos like `rm -rf "$DIRR"/`),
and make a pipeline fail when any stage fails, not just the last. Know its limits:
`set -e` is suppressed inside conditions.

**How would you make an app start on boot and restart on crash on a plain VM?**
A systemd unit with `Restart=on-failure`, `WantedBy=multi-user.target`, `systemctl
enable --now`, logs in `journalctl -u`. Mention running as a non-root user, the fd limit
and a stop timeout.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — | Navigate the filesystem, read files with `less`/`tail`, use `grep` and pipes, understand stdin/stdout and exit codes, run `ssh` and `git` from a terminal. |
| Junior (L3) | Software Engineer I | L3 | Write safe small bash scripts (quoting, `set -euo pipefail`), slice logs with `grep`/`awk`/`sort`/`uniq`, debug APIs with `curl -v` and `jq`, read `systemctl status` and `journalctl`, check `ss -tulpn` and `nc -vz`. |
| Mid (L4) | Software Engineer II | L4 | Diagnose "can't connect" layer by layer, explain refused vs timeout, use `lsof`, `/proc`, signals and graceful shutdown correctly, write a hardened systemd unit, run the 60-second triage and read `vmstat`/`iostat`. |
| Senior (L5) | Senior Software Engineer | L5 | Use `strace`, `perf`, `tcpdump` and eBPF tools under production constraints, reason about load average, OOM kills, fd limits, TIME-WAIT and page cache, and turn a one-off investigation into a runbook or automated check. |
| Staff+ (L6+) | Staff / Principal Engineer | L6+ | Set fleet standards (base images, access via short-lived certificates or session managers, observability agents instead of SSH debugging), decide when shell automation should become a real tool, and lead incident investigations across OS, network and application layers. |

## Interview checklist

- [ ] I can explain stdin/stdout/stderr, pipes, exit codes and why `2>&1 > file` differs from `> file 2>&1`.
- [ ] I can write a bash script with `set -euo pipefail`, quoted variables, `trap` cleanup and `find -print0 | xargs -0`.
- [ ] I can answer a top-N question from a log with `awk | sort | uniq -c | sort -rn | head`.
- [ ] I can use `curl -v`, `curl -w` timing and `jq` filters to debug an API.
- [ ] I can explain file permissions in octal and the `x` bit on directories.
- [ ] I can solve "disk full but `du` says no" with `lsof +L1` and check inodes with `df -i`.
- [ ] I can list the main signals, explain TERM-then-KILL, zombies and why containers need an init.
- [ ] I can write a systemd unit with restart policy, user, limits and `journalctl` usage.
- [ ] I can debug connectivity through DNS, route, TCP, TLS and application, and tell refused from timeout.
- [ ] I can run a first-60-seconds performance triage and say what `r`, `b`, `wa`, `st` mean.

Related: [Operating Systems & Hardware Symbiosis](../../interview-core/CSFundamentals/01_operating_systems_deep_dive.md) (processes, signals, page
cache, epoll), [Networking & Distributed Communication](../../interview-core/CSFundamentals/02_networking_deep_dive.md) (TCP, DNS, TLS),
[Docker and Containerization](01_docker_and_containers.md) (namespaces, cgroups, PID 1 in containers),
[Observability and Monitoring](06_observability_and_monitoring.md) (logs and metrics instead of SSH),
[Secret Management](11_secret_management.md) (keeping secrets out of unit files and shell history).
