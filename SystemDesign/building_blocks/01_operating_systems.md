# Operating Systems for System Design

Every service you design runs on top of an <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> scheduling processes, mapping memory, and multiplexing I/O. Interviewers rarely ask kernel trivia directly, but "why does connection pool size matter," "why did p99 latency spike under load," and "why does this server fall over at 10k connections" are all <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> questions wearing a system-design costume. This file is the mechanism layer underneath application-level resilience patterns (`12_application_resilience_patterns.md`) and scaling (`13_scaling_and_load_balancing.md`).

## Processes vs threads

| | Process | Thread |
|---|---|---|
| Memory | Own address space | Shares address space with sibling threads |
| Creation cost | Expensive (`fork`/`exec`, new page tables) | Cheap (shares page tables) |
| Context switch cost | Expensive (flush/reload <abbr title="Translation Lookaside Buffer. A memory cache that stores recent translations of virtual memory to physical addresses for faster retrieval.">TLB</abbr>, MMU state) | Cheaper (same address space, no <abbr title="Translation Lookaside Buffer. A memory cache that stores recent translations of virtual memory to physical addresses for faster retrieval.">TLB</abbr> flush needed) |
| Crash isolation | One process crashing doesn't take down another | One thread crashing (segfault) can take down the whole process |
| Communication | IPC: pipes, sockets, shared memory (explicit, costly) | Shared memory by default (implicit, needs locking) |

A **context switch** is the kernel saving one execution context's registers/program counter and loading another's. Between threads of the same process it's cheap. Between processes it's expensive because the <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>'s memory-management unit (MMU) has to reload address-translation state, and the <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> cache gets cold for the new process's working set.

**Why thread-pool sizing matters:** every thread costs a stack (default ~1-8MB virtual, less resident) and adds scheduling overhead. Too few threads under a synchronous, blocking-I/O model and requests queue behind each other even though the <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> is idle waiting on a database. Too many and the <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> spends more wall-clock time context-switching between threads than doing useful work — throughput actually drops past a certain thread count on <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>-bound work. Rule of thumb for a mixed I/O/<abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> workload:

```text
threads ≈ cores × (1 + wait_time / compute_time)
```

A thread that's 90% blocked on I/O and 10% computing justifies far more threads than cores; a <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>-bound worker pool should be sized close to core count.

## <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> scheduling

The kernel scheduler decides which runnable thread gets the <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> next. Modern general-purpose schedulers (Linux <abbr title="Completely Fair Scheduler. A process scheduler, implemented in the Linux kernel, that maximizes overall CPU utilization while also maximizing interactive performance.">CFS</abbr> — Completely Fair Scheduler) are **preemptive**: a running thread can be interrupted before it voluntarily yields, based on a time slice and priority/niceness. Real-time variants add hard priority classes.

**Noisy-neighbor <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> starvation:** on a shared host (<abbr title="Virtual Machine. The virtualization/emulation of a computer system.">VM</abbr>, container host, or a Kubernetes node with no <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> limits/requests set correctly), one process consuming all available <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> time delays every other process's scheduling — their threads are runnable but not picked. This is why <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> **limits** (hard cap) and **requests** (guaranteed share via cgroup shares) both matter in container platforms — see `16_platform_and_infra.md` for the cgroup mechanics. Symptom in production: p99 latency spikes with no code change, correlated with a co-located batch job or a runaway sibling container, not with your own request rate.

## Virtual memory

Every process sees a private, contiguous virtual address space; the MMU translates virtual addresses to physical page frames via **page tables**. Memory is managed in fixed-size **pages** (commonly 4KB).

```text
process virtual address space          physical RAM
┌────────────────┐                     ┌──────────┐
│ code            │──── page table ───▶│ frame 7  │
│ heap            │──── page table ───▶│ frame 3  │
│ stack           │──── page table ───▶│ (swap)   │  ← paged out
└────────────────┘                     └──────────┘
```

A **page fault** happens when a process touches a virtual page with no valid physical mapping — the <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> either loads it from disk (file-backed page, swap) or the process gets killed for touching unmapped memory. A *minor* fault (page exists in memory but not mapped into this process yet, e.g. shared library) is cheap; a *major* fault (page must be read from disk) costs milliseconds — this is why swapping under memory pressure destroys latency.

A process can "have" more virtual memory than physical <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> exists because virtual address space is just a numbering scheme; pages are only backed by real frames on demand (demand paging), and inactive pages can be evicted or swapped. The **working set** is the set of pages a process actually touches in a given time window — if the working set doesn't fit in physical <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr>, the system **thrashes**: it spends more time paging data in and out than doing work.

**<abbr title="Out of Memory - An undesired state of computer operation where no additional memory can be allocated for use by programs.">OOM</abbr> killer:** on Linux, when the system is critically low on memory and cannot reclaim/swap enough, the kernel's <abbr title="Out of Memory - An undesired state of computer operation where no additional memory can be allocated for use by programs.">OOM</abbr> killer picks a process (scored by memory usage and an adjustable `oom_score_adj`) and sends it `SIGKILL`. In containers, hitting the cgroup memory limit triggers the same thing scoped to that container — this is why a container silently restarting under load, with no application-level exception logged, is almost always <abbr title="Out of Memory - An undesired state of computer operation where no additional memory can be allocated for use by programs.">OOM</abbr>, not a crash bug.

## File systems and I/O models

| Model | Mechanism | Concurrency per thread | Used by |
|---|---|---|---|
| Blocking I/O | Thread calls `read()`, sleeps until data ready | 1 connection | Thread-per-connection servers (classic Apache, Tomcat BIO) |
| Non-blocking I/O | `read()` returns immediately, EWOULDBLOCK if no data | Still needs polling | Rare alone |
| `select`/`poll` | Kernel checks a list of fds, returns which are ready | O(n) scan per call, capped fd count (`select`) | Older event loops |
| `epoll` (Linux) / `kqueue` (BSD) | Kernel maintains readiness set, returns only ready fds | O(1) amortized, scales to 10k+ fds | Nginx, Node.js (libuv), Netty, Redis |
| `io_uring` (Linux, modern) | Shared ring buffers between user/kernel, true async submit/complete, batched syscalls | Avoids per-event syscall overhead entirely | High-throughput proxies, newer databases |

This progression is *why* event-loop servers scale differently than thread-per-connection servers. A thread-per-connection model (blocking I/O) burns one <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> thread per open connection — at 10k idle keep-alive connections that's 10k stacks and 10k schedulable entities, most of them asleep waiting on I/O, and the scheduler still pays overhead tracking them. An event-loop model (epoll-based) uses a small, fixed number of threads (often one per core) and asks the kernel "wake me when any of these 10k sockets has data" — one syscall, one thread, thousands of connections. The trade-off: a single slow synchronous/<abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>-bound handler on an event loop blocks *every* connection multiplexed on that loop, whereas a blocked thread in a thread-per-connection model only stalls its own connection.

## Syscalls and kernel vs user space


```arch
%% caption: A syscall crosses the boundary from unprivileged user space to the privileged kernel.
group user "User Space" color=blue
node app "Application" at 0,0 in user icon=app
node lib "libc (wrapper)" at 0,1 in user icon=code

group kernel "Kernel Space (Privileged)" color=red
node sys "Syscall Interface" at 0,2 in kernel icon=function
node vfs "VFS / Net / Sched" at 0,3 in kernel icon=cpu
node hw "Hardware" at 0,4 in kernel icon=server

app -> lib : "write()"
lib ==> sys : "syscall (trap)"
sys -> vfs
vfs -> hw
```
A **syscall** is a controlled transition from unprivileged user space into the privileged kernel — the only way a process reads a file, opens a socket, allocates memory from the <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr>, or asks the time. Each syscall costs a context switch into kernel mode and back (hundreds of nanoseconds to low microseconds, more with mitigations like KPTI for speculative-execution vulnerabilities). A syscall-heavy hot path — e.g., calling `write()` once per log line instead of buffering, or doing a `stat()` per file access in a loop — adds up: batching I/O (buffered writes, `readv`/`writev`, `io_uring` batching) amortizes this cost.

## Concurrency primitives

- **Mutex**: mutual exclusion lock; one holder at a time, others block (sleep) until it's released.
- **Semaphore**: a counter with atomic increment/decrement; blocks when the count hits zero. Generalizes a mutex (binary semaphore) to bound concurrency (e.g., "max 10 concurrent DB connections").
- **Futex** (fast userspace mutex, Linux): the mechanism underneath most mutex implementations — the fast path (uncontended lock/unlock) happens entirely in user space with an atomic instruction; only the slow path (actual contention, need to block/wake a thread) makes a syscall into the kernel. This is why uncontended locks are nearly free and heavily contended locks are expensive — you pay for the syscall only when threads actually collide.

## `mmap` and the page cache

`mmap` maps a file directly into a process's virtual address space — reads/writes to that memory region are translated by the kernel into page-cache-backed file I/O, without explicit `read`/`write` syscalls per access. The kernel's **page cache** keeps recently-read/written file pages in <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> regardless of which process asked for them, so a second process reading the same file gets a cache hit for free, and the <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> handles eviction under memory pressure.

This matters for databases and large-file serving: a database can `mmap` its data files and let the <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> page cache absorb hot pages (simpler, but less control over eviction — which is why many databases, e.g. PostgreSQL, historically manage their own buffer cache on top of/instead of relying purely on the page cache), and a file server sending large static files benefits from `sendfile()`/`mmap` because the kernel can move bytes from page cache to socket without copying through user space at all.

## Copy-on-write `fork`, and the bridge to containers

`fork()` creates a child process by duplicating the parent's address space — but not by physically copying every page immediately. Both processes' page tables point at the same physical frames marked **copy-on-write (COW)**; only when either process writes to a shared page does the kernel actually copy it. This makes `fork()` cheap even for a large parent (classic use: a pre-fork web server model, or Redis's `fork()`-based snapshotting for `BGSAVE`, which relies on COW to avoid doubling memory for a point-in-time snapshot).

Containers are not a separate virtualization primitive — they're <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> processes with two extra pieces bolted on: **namespaces** (isolate what a process can *see* — its own PID tree, network stack, mount table, hostname) and **cgroups** (limit what a process can *use* — <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> shares, memory ceiling, I/O bandwidth, the same mechanism behind the <abbr title="Out of Memory - An undesired state of computer operation where no additional memory can be allocated for use by programs.">OOM</abbr> behavior and noisy-neighbor limits described above). A container image plus these two kernel features is the whole trick; there's no separate hypervisor. See `16_platform_and_infra.md` for how orchestrators build scheduling, service discovery, and resource requests/limits on top of this.

## Why this matters in an interview

| Symptom you're asked to explain | <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> mechanism underneath |
|---|---|
| "Increasing thread pool size made throughput worse" | Context-switch overhead exceeded parallelism gain; <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>-bound work should track core count |
| "Connection pool of 500 to a DB with 16 cores is too big" | DB backend is often ~1 process/thread per connection; oversized pools cause context-switch thrashing and lock contention server-side, not more throughput |
| "p99 spiked with no traffic change" | Noisy neighbor (<abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>/cgroup starvation) or major page faults from memory pressure |
| "One slow request stalled unrelated requests" | A blocking/<abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>-heavy call running on a shared event-loop thread |
| "Container kept restarting, no app error logged" | <abbr title="Out of Memory - An undesired state of computer operation where no additional memory can be allocated for use by programs.">OOM</abbr> killer hit the cgroup memory limit |
| "A single fsync-per-write design has terrible throughput" | Every write is a syscall + disk-flush; batch or use group commit |
| "Adding a <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> lookup in the hot path added tail latency" | A blocking syscall (network I/O) on a thread the event loop needed back |

The general interview move: connection-pool size and thread-pool size should be derived from core count and the blocking/non-blocking ratio of the workload, not picked arbitrarily — and any unexplained latency/throughput cliff is worth asking "is this scheduling, paging, or a syscall on the hot path" before reaching for a bigger instance.

## Related building blocks

- [00_overview.md](00_overview.md)
- [02_networking.md](02_networking.md)
- [13_scaling_and_load_balancing.md](13_scaling_and_load_balancing.md)
- [16_platform_and_infra.md](16_platform_and_infra.md)
- [15_observability_and_reliability.md](15_observability_and_reliability.md)
