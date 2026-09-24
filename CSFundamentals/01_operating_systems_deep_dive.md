# Operating Systems & Hardware Symbiosis

Every program you run eventually becomes instructions competing for a CPU, some RAM,
and a disk or network card that hundreds of other programs also want. This chapter
starts from first principles — what an operating system actually is, what its major
components are, and how they work together — then goes as deep as a Senior Software
Engineer (L5) interview loop expects: how your application's architecture interacts
with the kernel's scheduler, CPU caches, and virtual memory subsystem. Interviewers
at that level rarely ask "what is a thread" — they ask precise follow-ups, and this
file corrects several popular myths along the way; each correction is marked
**Precision note**. A side-by-side breakdown of what Junior through Staff+ engineers
are actually expected to know about this material closes out the chapter, just
before the interview checklist.

## Foundations — What Is an Operating System, and How Does It Work?

### Why Operating Systems Exist

The earliest computers ran one program at a time, start to finish, loaded by an
operator who physically fed it in. There was nothing to "share" — one program, one
machine, no other programs waiting. That stopped working the moment computers became
expensive enough that idling them between programs was wasteful, and popular enough
that many people wanted to use one at once. Two ideas fixed this, and the modern OS
is built on both of them:

- **Multiprogramming** — keep several programs loaded in memory at once, and while
  one waits for slow I/O (a disk read, say), let another use the CPU instead of
  sitting idle. This is the ancestor of everything in §1 (scheduling) and §4 (I/O
  models) below.
- **Time-sharing** — go further and give each program (and each user) the illusion
  of having the machine to itself, by rapidly switching between them many times a
  second. This is the ancestor of §5 (virtual memory) and §6 (processes/containers):
  the *illusion* of a private machine is the OS's central trick, applied to memory,
  to the CPU, and eventually to entire environments (containers, VMs).

Every idea in this file is really a more precise version of one of those two moves:
*share a physical resource among many programs*, and *make each program feel like it
has that resource to itself*.

### What an Operating System Actually Is

An **operating system (OS)** is the program that runs first when a machine boots,
and it does two jobs at once:

1. **Resource manager** — your CPU can only run one instruction stream at a time per
   core, RAM is one shared array of bytes, and there's usually one disk and one
   network card. The OS decides, continuously, who gets to use each of these next.
2. **Abstraction layer** — the OS hides the ugly, hardware-specific reality
   underneath a much simpler interface. You don't calculate which physical disk
   sectors to write; you call `write()` on a **file**. You don't manage raw physical
   memory addresses; your program gets an **address space** it can pretend is all
   its own. You don't speak directly to a specific network card's electrical
   signaling; you open a **socket**. Every "job" below is one resource, turned into
   one clean abstraction.

### The Core Components of an Operating System

An OS isn't one monolithic blob of logic — it's a handful of cooperating subsystems,
each responsible for one resource:

| Component | What it's responsible for | Covered deeper in |
|---|---|---|
| **Kernel** | The privileged core; the only code allowed to talk to hardware directly | Throughout this file |
| **Process & thread manager + scheduler** | Creates and destroys processes/threads; decides which one runs on which CPU core, and when | §1 (scheduling), §6 (processes vs. threads) |
| **Memory manager** | Gives every process the illusion of its own private, contiguous memory; maps that illusion onto real, shared RAM | §5 |
| **File system** | Organizes persistent storage into files and directories; turns raw disk blocks into `open()`/`read()`/`write()` | §5 (page cache), §7 (I/O path) |
| **I/O manager & device drivers** | Talks to disks, network cards, keyboards, and every other device through vendor-specific driver code, behind one uniform interface | §4, §7 |
| **Network stack** | Implements TCP/IP (and friends) so a process can exchange bytes with a process on another machine | §7 here; the full treatment is `02_networking_deep_dive.md` |
| **Inter-process communication (IPC)** | Controlled channels for processes to exchange data: pipes, sockets, shared memory, signals | §6 |
| **Security & access control** | Users, permissions, and isolation boundaries — decides *who* is allowed to do *what* to which resource | §6 (namespaces, cgroups, containers) |

### How the Pieces Fit Together

Every request your program makes eventually crosses one narrow, guarded boundary —
the **system call interface** — into the kernel, which routes it to the right
subsystem, which talks to the actual hardware:

```arch
%% caption: Every request crosses one guarded door, the system call interface, into the kernel subsystem that owns the hardware.
grid 130x120
group us "User Space: your code, no direct hardware access" color=blue icon=user
node app1 "Your Application" at 1,0 in us icon=app
node app2 "Another Application" at 3,0 in us icon=app
node sys "System Call Interface" at 2,1 shape=pill color=amber sub="the only door across the boundary"
group ks "Kernel Space: privileged, talks to hardware" color=purple icon=shield
node sched "Scheduler" at 0,2 in ks icon=scheduler sub="§1"
node mem "Memory Manager" at 1,2 in ks icon=memory sub="§5"
node fs "File System" at 2,2 in ks icon=folder sub="§5 / §7"
node io "I/O Manager & Drivers" at 3,2 in ks icon=plugin sub="§4 / §7"
node net "Network Stack" at 4,2 in ks icon=network sub="§7"
group hw "Hardware" color=slate icon=cpu
node cpu "CPU cores" at 0,3 in hw icon=cpu
node ram "RAM" at 1,3 in hw icon=memory
node disk "Disk" at 2,3 in hw icon=disk
node nic "Network Card" at 4,3 in hw icon=wifi
app1 -> sys
app2 -> sys
sys -> sched
sys -> mem
sys -> fs
sys -> io
sys -> net
sched -> cpu
mem -> ram
fs -> disk
io -> disk
io -> nic
net -> nic
```

<div class="lab" data-viz="os-architecture"></div>

### Kernel Space vs. User Space

The **kernel** is the only code allowed to talk to hardware directly; it runs in a
privileged CPU mode (ring 0 on x86). Your program runs in **user space**, a
deliberately restricted mode, and asks the kernel for things — read a file, send a
packet, allocate memory — through a **system call (syscall)**: a controlled,
validated door between your code and the hardware. Every "expensive" operation
you'll read about below (a context switch, a page fault, a blocking read) is
expensive largely *because* it crosses that door: the CPU has to switch privilege
modes, and the kernel has to validate and act on the request.

### Process vs. Thread — the Distinction the Rest of This File Assumes

- A **process** is a running program with its own private memory (its **address
  space**), like a self-contained office: nobody outside can see your desk.
- A **thread** is a unit of execution *inside* a process. A process can have many
  threads, and they all share that process's memory — like several workers in the
  same office, all able to read and write the same shared whiteboard. That sharing is
  convenient (no copying data between them) and dangerous (two workers can scribble
  on the whiteboard at the same time) — §2–3 below are entirely about the "dangerous"
  half, and `05_concurrency_deep_dive.md` is the full treatment.

### Why Scheduling, Memory Illusions, Caches, and Blocking All Exist

These four ideas are the connective tissue between the components table above and
the deep-dive sections below — each is a direct consequence of "one shared resource,
many programs that want it":

- **Scheduling** exists because a typical machine has far more runnable threads than
  CPU cores. The **scheduler** (§1) decides, many times a second, which thread runs
  on which core next. Switching a core from one thread to another is a **context
  switch**: the kernel saves that thread's registers and loads the next thread's —
  not free, which is why §1 cares about *how many* threads you create, not just how
  you use them.
- **Virtual memory** exists because letting programs address real RAM directly would
  mean any bug in one program could overwrite another program's data. So the memory
  manager gives every process the *illusion* of owning all of memory, and translates
  each program's addresses to real physical RAM behind the scenes (§5). "Memory
  address" in your program is never the literal RAM location.
- **CPU caches** exist because RAM is slow compared to a modern CPU core — hundreds
  of cycles away. Every core has small, fast caches (L1, L2, often a shared L3) that
  hold recently-used data so the core doesn't wait on RAM for every access. §2 covers
  what happens when *two* cores cache the *same* data.
- **Blocking** is the simplest possible answer to "what happens while I wait for
  something slow" (a disk read, a network reply): your thread stops running until the
  answer is ready. Simple to reason about, expensive at scale — §4 is entirely about
  the faster alternatives operating systems offer instead.

### Kernel Design Philosophies

Not every OS draws the kernel-space/user-space line in the same place. This matters
because it trades performance against fault isolation:

| Design | Where subsystems live | Trade-off | Examples |
|---|---|---|---|
| **Monolithic kernel** | Scheduler, memory manager, file systems, and drivers all run together in kernel space | Fast — no IPC needed between subsystems — but a bug in one driver can crash the whole kernel | Linux, the original Unix |
| **Microkernel** | Only the bare minimum (scheduling, basic IPC, minimal memory management) runs in kernel space; file systems and drivers run as user-space servers, talking to the kernel via message passing | More fault-isolated (a crashed file-system server doesn't take down the kernel); historically slower, because every cross-subsystem call now pays IPC + context-switch cost | Minix, QNX, seL4 |
| **Hybrid** | Mostly monolithic, with some services pulled out into more isolated, microkernel-like components | A practical middle ground | Windows NT, macOS's XNU (a Mach microkernel core plus a large monolithic BSD layer) |

**Precision note:** Linux is monolithic but *modular* — loadable kernel modules let
you add drivers without recompiling the kernel — but a loaded module still runs in
kernel space at full privilege, unlike a true microkernel's user-space servers.
"Modular" and "microkernel" are not the same claim.

### Vocabulary You'll Meet Below, in One Table

| Term | One-line meaning |
|---|---|
| Kernel | The part of the OS allowed to touch hardware directly |
| Syscall | A controlled request from your program to the kernel, crossing the user/kernel boundary |
| Process | A running program with its own private memory |
| Thread | A unit of execution sharing its process's memory with other threads |
| Context switch | The kernel swapping which thread a core is running |
| Virtual memory | The illusion that each process owns all of memory |
| Cache line | The chunk (usually 64 bytes) a CPU cache moves and tracks at a time |
| Blocking call | A syscall that pauses your thread until it completes |
| IPC | A controlled channel for processes to exchange data (pipes, sockets, shared memory, signals) |
| Monolithic / microkernel | Whether subsystems run inside the privileged kernel, or as isolated user-space services |

With the components, the layering, and that vocabulary in place, the rest of this
chapter is the precise, L5-depth version of each piece — how the scheduler actually
picks a thread, how caches actually stay consistent across cores, and so on.

## 1. Deep Linux Internals: The Scheduler

For most of the last 15 years the default Linux scheduler was the **Completely Fair Scheduler (CFS)**. Since Linux 6.6 (late 2023) the fair class uses **EEVDF** (Earliest Eligible Virtual Deadline First), which keeps CFS's virtual-runtime accounting but picks tasks by virtual deadline to give latency-sensitive tasks better treatment. The CFS model below is still the right mental model and what most interview answers reference.

### How CFS Works
CFS does not use strict fixed timeslices (e.g., "every thread gets 10ms"). Instead, it tracks the "virtual runtime" (`vruntime`) of every runnable thread in a **Red-Black Tree**.

```arch
%% caption: CFS keeps runnable threads in a red-black tree keyed by vruntime and always runs the leftmost one.
route straight
grid 110x100
node s "Scheduler" at 0,2 icon=scheduler
group rb "CFS Red-Black Tree" color=blue icon=tree
node r "50ms" at 3,0 in rb shape=circle color=blue sub="root"
node l "30ms" at 2,1 in rb shape=circle color=blue sub="left child"
node rr "80ms" at 4,1 in rb shape=circle color=blue sub="right child"
node ll "10ms" at 1,2 in rb shape=circle color=green sub="NEXT TO RUN"
r -> l
r -> rr
l -> ll
s -> ll : "Always picks leftmost"
```
*   **The Algorithm:** The scheduler picks the runnable thread with the smallest `vruntime` (the leftmost node, cached so the pick is O(1); insert/remove are O(log n)).
*   **Weighting (Niceness):** High-priority tasks don't get *more* slices in a fixed sense; their `vruntime` advances *slower* than low-priority tasks, so they are picked more often and run longer in total.
*   **L5 Implication:** If you spawn 10,000 OS threads that are mostly blocked on I/O, the cost is not the red-black tree (log2 of 10,000 is about 13). The costs are **context switches** (saving/restoring registers, kernel entry/exit), **cold CPU caches** after every switch, **memory** for each thread's kernel structures and stack, and **lock contention** when many runnable threads wake together. That is why high-concurrency runtimes (Go, Node.js, Java virtual threads, Rust async) multiplex many lightweight tasks onto a small pool of OS threads (M:N scheduling).

### Scheduling vocabulary worth knowing

| Term | Meaning | Why it matters |
|---|---|---|
| Run queue | Per-CPU set of runnable tasks | Load balancing migrates tasks between CPUs, which costs cache warmth |
| Preemption | Kernel takes the CPU from a running task | Latency-sensitive services care about scheduler latency, not just throughput |
| CPU affinity / pinning | Restrict a thread to specific cores | Keeps caches warm; used by databases, packet processing, and NUMA-aware services |
| cgroups CPU quota | Limit a container to N CPU-seconds per period | A container throttled mid-period shows latency spikes even at low average CPU. Classic Kubernetes p99 problem |
| Priority inversion | Low-priority task holds a lock a high-priority task needs | Solved with priority inheritance in real-time systems |

### Scheduling Classes, Briefly

CFS/EEVDF is only the *default* ("fair") scheduling class. Linux actually offers
several, and the kernel always prefers a higher class over a lower one:

| Class | Policy | Used for |
|---|---|---|
| Real-time (highest) | `SCHED_FIFO` (runs until it blocks or yields), `SCHED_RR` (round-robin among equal priority) | Latency-critical system tasks; almost never used by application code |
| Fair (default) | `SCHED_NORMAL`/`SCHED_OTHER` — CFS or EEVDF | Essentially everything you write |
| Idle (lowest) | `SCHED_IDLE` | Background work that should never delay anything else |

**Order of magnitude worth knowing:** a context switch on Linux is commonly cited in
the low single-digit microseconds for the switch itself, with the larger and more
variable cost coming from the *cold caches afterward* (§2) — a thread that gets
switched back in has to re-warm L1/L2 from scratch, which can cost far more than the
switch. That's the real reason "thousands of runnable threads" hurts throughput more
than the O(log n) scheduler data structure ever would.

## 2. Concurrency at the Hardware Level (MESI)

When two threads run on different CPU cores, they each have their own L1/L2 caches. If they share a variable, how do the caches stay consistent?

### The MESI Protocol (Cache Coherence)
Cache coherence protocols in the MESI family track the state of each **cache line** (usually 64 bytes on x86 and most ARM servers):

```arch
%% caption: MESI: every cache line is in one of four states, and reads and writes by other cores move it between them.
grid 150x110
node e "E" at 1,0 shape=circle color=green sub="Exclusive: only copy, clean"
node i "I" at 0,1 shape=circle color=slate sub="Invalid: stale"
node m "M" at 2,1 shape=circle color=red sub="Modified: dirty, must write back"
node s "S" at 1,2 shape=circle color=blue sub="Shared: read-only, multiple cores"
i:T -> e:L : "Core reads, no other copy"
i:B -> s:L : "Core reads, others have it"
e:R -> m:T : "Core writes"
s:B -> i:L : "Another core writes"
m:L -> i:R : "Another core reads (snoop)"
e:B -> s:T : "Another core reads"
```

<div class="lab" data-viz="false-sharing"></div>

*   **M**odified: This core has changed the data; it differs from main memory.
*   **E**xclusive: This core is the only one caching the data, and it matches main memory.
*   **S**hared: Multiple cores cache this data (read-only).
*   **I**nvalid: This copy is stale and must be re-fetched before use.

### The L5 Trap: False Sharing
Imagine `struct { int64 A; int64 B; }`. Thread 1 only modifies `A` on Core 1. Thread 2 only modifies `B` on Core 2. There is no logical race condition.
*   **The Problem:** `A` and `B` sit in the *same 64-byte cache line*. To write `A`, Core 1 needs exclusive ownership of that line, so it sends a **Read-For-Ownership (RFO)** request over the processor interconnect and Core 2's copy becomes Invalid. When Core 2 then writes `B`, it must re-acquire the line, invalidating Core 1's copy. The line ping-pongs between cores on every write.
*   **The Result:** Throughput can collapse. Published measurements range from tens of percent to several-times slowdowns depending on the write rate and core distance. **Precision note:** "10-100x" figures circulate but are workload-specific; say "significant, measure it with `perf c2c`."
*   **The Fix:** Put independently-written hot fields on different cache lines: pad the struct (e.g., `_ [56]byte` after an `int64` in Go, or `golang.org/x/sys/cpu.CacheLinePad`), use `@Contended` in Java, `alignas(64)` in C++, or give each thread its own counter and merge periodically.

```go
// Before: A and B share a 64-byte cache line -> ping-pong under concurrent writes.
type Counters struct {
    A int64
    B int64
}

// After: pad so each field owns its own cache line.
type PaddedCounters struct {
    A    int64
    _pad [56]byte // fills out the rest of a 64-byte line
    B    int64
}
```

## 3. Atomic Instructions (CAS)

How do mutexes avoid race conditions themselves? They rely on hardware atomic instructions, specifically **Compare-And-Swap (CAS)** (`LOCK CMPXCHG` on x86, `LDREX/STREX` or `CMPXCHG`-style ops on ARM).

A CAS takes 3 arguments: a memory location, an expected old value, and a new value. It writes the new value only if the location still holds the expected value, and reports whether it did, as one indivisible operation.
*   **Precision note:** Modern x86 does **not** lock the memory bus for `LOCK CMPXCHG` (that was true of very old CPUs). The `LOCK` prefix makes the instruction atomic with respect to other cores via cache-line ownership; it is not a single "clock cycle" either. What matters for the interview: CAS is atomic, lock-free, and can fail and be retried.
*   **Spinlocks:** A spinlock is essentially `while (!CAS(&lock, 0, 1)) pause();`. Good when critical sections are tiny and on other cores; terrible when the lock holder can be descheduled.
*   **Futex-based mutexes:** The uncontended path is a single CAS in user space with no syscall. Only when the CAS fails does the thread call `futex(FUTEX_WAIT)` to sleep in a kernel wait queue; the unlocker calls `futex(FUTEX_WAKE)` if there are waiters. Many mutexes spin briefly before sleeping (adaptive mutexes).
*   **ABA problem:** a CAS-based lock-free stack can see value A, get preempted while another thread pops A, pushes B, pushes A back, and then succeed incorrectly. Fixes: tagged pointers / version counters, hazard pointers, epoch-based reclamation, or a GC.

**A lock-free counter, to make CAS concrete:**

```go
// Retry loop: read, compute, try to swap in — retry if another thread won the race.
func increment(counter *int64) {
    for {
        old := atomic.LoadInt64(counter)
        if atomic.CompareAndSwapInt64(counter, old, old+1) {
            return // nobody else changed it between our read and our swap
        }
        // someone else updated it first — loop and try again with a fresh read
    }
}
```
No lock is ever held; under contention some goroutines simply retry. This is the
same shape every lock-free data structure uses, and it's why CAS retries — rather
than blocking — are the right mental model for "lock-free."

## 4. Advanced I/O Models

A classic question: "How does Nginx handle 100,000 concurrent connections when a thread-per-connection server struggles at 10,000?"

### The Evolution of I/O

```arch
%% caption: Four generations of I/O: each step cuts the work the kernel does per connection.
grid 250x90
group g1 "1. Thread-per-conn" color=red icon=thread
node a1 "10k threads" at 0,0 in g1 icon=thread
node a2 "OS Scheduler thrashes" at 1,0 in g1 icon=scheduler
group g2 "2. select/poll" color=amber icon=search
node b1 "1 thread" at 0,1 in g2 icon=thread
node b2 "Kernel checks 10k fds" at 1,1 in g2 icon=cpu
group g3 "3. epoll/kqueue" color=green icon=event
node c1 "1 thread" at 0,2 in g3 icon=thread
node c2 "Kernel returns ONLY active fds" at 1,2 in g3 icon=cpu
group g4 "4. io_uring" color=blue icon=queue
node d1 "Shared ring buffer" at 0,3 in g4 icon=memory
node d2 "Kernel and app share memory" at 1,3 in g4 icon=cpu
a1 -> a2 : "Context switch storm"
b1 -> b2 : "O(N) scan ALL fds"
c1 -> c2 : "O(ready) list"
d1 -> d2 : "Batched or no syscalls"
```
1.  **Thread-per-connection (classic Apache prefork/worker):** Each connection blocks in `read()` on its own thread or process. The limits are memory and context switching. **Precision note:** a thread's stack is *reserved virtual memory* (8 MB default on Linux glibc, configurable), and only touched pages consume RAM. So "10k x 2MB = 20GB of RAM" is wrong; real RSS per idle thread is tens of KB of stack plus kernel structures. The real problems are scheduler/context-switch overhead under load, per-thread memory at 100k+ connections, and lock contention.
2.  **`select()` / `poll()`:** One thread passes the full set of descriptors to the kernel on every call; the kernel scans all of them. O(N) per call, and `select` is also capped at `FD_SETSIZE` (usually 1024).
3.  **`epoll` (Linux) / `kqueue` (BSD, macOS):** Interest is registered once. The kernel maintains a ready list; `epoll_wait()` returns only descriptors that are ready. Cost per call is **O(number of ready events)**, independent of the total number of watched connections. Go's netpoller, Node's libuv, Nginx, and Redis all sit on this.
4.  **`io_uring` (Linux 5.1+):** Two ring buffers shared between user space and kernel: a Submission Queue and a Completion Queue. The application writes many requests and submits them with one `io_uring_enter` call (batching), or with `SQPOLL` a kernel thread polls the queue so steady-state I/O needs no syscalls at all. It also supports true async file I/O, which `epoll` never did. Trade-off: a large attack surface; several distributions and Google's own production kernels have restricted it for security reasons.

### Blocking, non-blocking, async — say it precisely

| Model | Who waits | Example |
|---|---|---|
| Blocking I/O | The thread sleeps in the syscall | `read()` on a default socket |
| Non-blocking I/O | The call returns `EAGAIN` immediately; you retry later | socket with `O_NONBLOCK` |
| I/O multiplexing (readiness) | One thread waits for *readiness* of many fds, then does non-blocking reads | `epoll`, `kqueue` |
| Asynchronous I/O (completion) | Kernel performs the I/O and notifies on *completion* | `io_uring`, Windows IOCP |

### The Same Idea, Wearing Different Names Per Language

Every high-level "async" runtime is built on the readiness or completion models
above, not on magic:

| Language / runtime | What it actually sits on |
|---|---|
| Go | Its own M:N scheduler + a netpoller built on `epoll`/`kqueue` — goroutines that block on I/O don't block an OS thread |
| Python `asyncio` | An event loop built on `select`/`epoll`/`kqueue` (via `selectors`) |
| Node.js | `libuv`, which wraps `epoll`/`kqueue`/IOCP per platform |
| Java NIO / virtual threads (21+) | `epoll`-based selectors historically; virtual threads add M:N scheduling on top |
| Nginx, Redis, HAProxy | `epoll`/`kqueue` directly, event-loop style |

Knowing this saves you in an interview: "how does `asyncio` handle 10,000
connections on one thread?" and "how does Nginx handle 100,000 connections?" are the
same question with a different label on top.

## 5. Virtual Memory & NUMA

*   **Page tables and the TLB:** Translating a virtual address walks a multi-level page table (4 levels on x86-64, 5 with LA57). The **TLB** caches recent translations. A TLB miss costs a page walk (several memory accesses).

```arch
%% caption: A TLB hit translates in one lookup; a miss walks the page table and then fills the TLB.
grid 200x100
node va "Virtual Address" at 0,0 shape=pill color=slate sub="what your program uses"
node tlb "In TLB?" at 0,1 shape=diamond color=amber sub="cache of recent translations"
node pa "Physical Address" at 0,2 shape=pill color=green sub="real RAM"
node walk "Walk the page table" at 1,1 icon=layers sub="up to 4-5 levels of memory accesses"
node fill "Fill the TLB" at 1,2 icon=cache sub="with this translation"
va -> tlb
tlb -> pa : "Hit: 1 lookup"
tlb -> walk : "Miss"
walk -> fill
fill -> pa
```
*   **Context switch cost:** Switching between *processes* changes the address space. **Precision note:** with PCID (x86) / ASID (ARM), the kernel tags TLB entries per address space and does not have to flush the whole TLB on every switch, though entries for the old process stop being useful. Switching between *threads* of the same process keeps the address space and its TLB entries.
*   **Huge pages:** 2 MB (or 1 GB) pages mean one TLB entry covers far more memory, cutting TLB misses for large heaps (databases, JVMs). Transparent Huge Pages can cause latency spikes during compaction; many databases recommend disabling THP and using explicit huge pages.
*   **Page faults:** a *minor* fault maps a page already in memory (e.g., first touch of allocated memory, copy-on-write after `fork`); a *major* fault reads from disk (swap or a memory-mapped file) and costs milliseconds.
*   **The page cache:** Linux uses free RAM to cache file contents. `read()` of a hot file never touches disk. `write()` normally lands in the page cache and returns before data is durable; **only `fsync()`/`fdatasync()` makes it durable**. This is why databases call `fsync` on their WAL and why "we wrote it" is not "it survived a power loss."
*   **OOM killer:** when memory is exhausted, Linux kills a process chosen by a badness score. In containers, exceeding the cgroup memory limit gets the container killed (exit code 137) even if the host has free memory.
*   **NUMA (Non-Uniform Memory Access):** On multi-socket servers, each CPU has its own local RAM. Accessing another socket's memory goes over the interconnect and is slower. High-performance databases pin threads to cores and allocate memory on the local NUMA node (`numactl`, `libnuma`).

## 6. Processes, Threads, and Containers

| Concept | Isolation | Cost to create | Communication |
|---|---|---|---|
| Process | Separate address space | `fork`+`exec`; COW makes `fork` cheap until pages are written | Pipes, sockets, shared memory, signals |
| Thread | Shared address space | Cheaper (clone with shared memory) | Shared memory + locks |
| Goroutine / green thread | Scheduled by a runtime | ~2-8 KB initial stack, growable | Channels, shared memory |
| Container | Same kernel; isolated by **namespaces** (pid, net, mount, user, uts, ipc) and limited by **cgroups** (CPU, memory, I/O) | Process start + namespace setup | Network or volumes |
| VM | Separate kernel on a hypervisor | Seconds | Virtual network |

Interview-ready one-liner: **a container is a process with namespaces for isolation and cgroups for limits; it is not a lightweight VM.** Google's Borg (and its paper, see `SystemDesign/building_blocks/24_google_papers.md`) is where much of the cgroups work originated.

### Why `fork()` Is Cheap: Copy-on-Write

`fork()` creates a new process that is an exact copy of the calling one. Copying an
entire address space on every `fork()` would be far too slow to use as often as Unix
does — the fix is **copy-on-write (COW)**: the child's page table initially points at
the *same physical pages* as the parent, all marked read-only. Only when either
process **writes** to a shared page does the kernel take a page fault, actually copy
that one page, and let the write proceed. A `fork()` immediately followed by `exec()`
(the classic way to launch a new program) may end up copying almost nothing at all —
this is also why "process creation is always expensive" is an oversimplification;
it's the pages you *write to afterward* that cost you.

## 7. What Happens When a Program Calls `write()` on a Socket

A good end-to-end answer that connects this file to networking:

```arch
%% caption: write() returns once the bytes are copied into the kernel; TCP, IP and the NIC deliver them later.
grid 220x95
group us "User space" color=blue icon=user
node ub "User buffer" at 0,0 in us icon=memory
node note "returns when data is COPIED, not when it's delivered" at 0,1 in us shape=text
group ks "Kernel" color=purple icon=shield
node sb "Kernel socket send buffer" at 1,0 in ks icon=queue sub="(copy)"
node tcp "TCP segments it" at 1,1 in ks icon=network sub="cwnd / MSS"
node ip "IP routing, qdisc" at 1,2 in ks icon=network
node nic "NIC driver ring buffer" at 1,3 in ks icon=plugin
node wire "wire" at 1,4 shape=pill color=slate
ub -> sb : "write() syscall"
ub .. note
sb -> tcp -> ip -> nic
nic -> wire : "DMA"
```

`write()` succeeding only means the bytes reached the kernel. If the send buffer is full, a blocking socket sleeps and a non-blocking socket returns `EAGAIN` (that is **backpressure** at the OS level). Zero-copy paths (`sendfile`, `splice`, `MSG_ZEROCOPY`) skip the user-to-kernel copy for large transfers such as serving files or video segments.

## What Each Engineering Level Should Know

Not everyone reading this file needs every sentence of it cold. This table maps this
chapter's material onto a standard industry ladder *and* the Google-style ladder this
repo's interview content is written against, side by side — the mapping between
company-specific titles and levels is approximate and varies by company, but the
*depth of understanding* described in each row is a reliable signal regardless of
which company uses which label. Use it two ways: as a syllabus (read down a column to
see what to learn next) or as a self-assessment (find the row/column that matches
where a real interview would place you).

| Topic in this chapter | Junior / New Grad (Google L3) | Mid-Level (Google L4) | Senior (Google L5) | Staff+ (Google L6–L7) |
|---|---|---|---|---|
| **Core vocabulary & components** (Foundations) | Can define process, thread, kernel vs. user space, and syscall in plain language | Can explain how the OS's components work together (the Foundations diagram) and why each exists | Connects the vocabulary across subsystems unprompted — e.g. can give §7's full `write()` walkthrough | Can explain kernel design trade-offs (monolithic vs. microkernel vs. hybrid) and how that choice shapes an entire platform's reliability story |
| **Processes, threads & scheduling** (§1, §6) | Knows a process has its own memory and a thread shares it; knows "the OS shares the CPU" | Knows a context switch has a cost and that creating too many threads is bad, without naming the specific mechanism | Explains CFS/EEVDF's `vruntime` mechanism precisely and corrects the "2MB × 10k threads = 20GB" myth | Weighs M:N scheduling (Go goroutines, Java virtual threads) against raw OS threads for a real workload, and reasons about scheduler-latency SLOs at fleet scale |
| **Hardware-level concurrency** (§2–§3) | Aware that two cores can see stale data without synchronization | Knows locks/atomics fix races; hasn't necessarily seen MESI by name | Explains MESI's four states, diagnoses false sharing, and fixes it with padding | Predicts false sharing in a design review before anyone measures it, and knows when a lock-free structure is (and isn't) worth the ABA-problem complexity |
| **I/O models** (§4) | Knows "blocking" vs. "non-blocking" as terms | Knows `epoll`/`kqueue` exist and roughly why they beat `select`/`poll` | Derives epoll's O(ready events) advantage from first principles and compares it precisely to `io_uring` | Makes the actual production adoption call — `io_uring`'s throughput win against its larger attack surface — for a real fleet |
| **Memory management** (§5) | Knows RAM is shared and programs never see real physical addresses | Knows what a page fault is, without necessarily distinguishing minor from major | Explains the TLB, huge pages, and why `fsync` — not `write()` — is what actually makes data durable | Diagnoses a NUMA-related latency regression or a Transparent-Huge-Page-induced p99 spike from symptoms alone |
| **Containers & isolation** (§6) | Believes "a container is a lightweight VM" (a common oversimplification) | Knows containers share a kernel and cost less overhead than VMs, without the precise mechanism | Corrects the VM myth precisely: namespaces for isolation, cgroups for limits, same kernel | Explains the cgroup-quota-throttling p99 problem from first principles and designs around it (e.g. CPU limits vs. requests in Kubernetes) |

**Reading this table as a study plan:** if you're aiming at a Senior/L5 bar, your
target is the whole "Senior" column — which is exactly what the numbered sections (1–7)
above already deliver in full. The "Junior" and "Mid-Level" columns describe the
partial understanding this chapter's Foundations section alone gets you to; the
"Staff+" column is judgment that mostly comes from having operated real systems at
scale, not from reading — this file gives you the vocabulary to have that
conversation, not a substitute for having had it.

## Interview checklist

- [ ] I can name an OS's core components (scheduler, memory manager, file system, I/O manager, network stack, IPC, security) and what each owns.
- [ ] I can explain the kernel/user-space boundary and why crossing it (a syscall) isn't free.
- [ ] I can explain why 10k blocked threads hurt, without the "2MB x 10k = 20GB" myth.
- [ ] I can explain false sharing and name one detection tool and one fix.
- [ ] I can explain CAS, futexes, and the ABA problem.
- [ ] I can compare select/poll, epoll, and io_uring with correct complexity.
- [ ] I can explain the page cache and why `fsync` matters for durability.
- [ ] I can explain why `fork()` is cheap (copy-on-write) and when it stops being cheap.
- [ ] I can define a container as namespaces + cgroups, and compare monolithic vs. microkernel design.

Related: `SystemDesign/building_blocks/01_operating_systems.md`, `05_concurrency_deep_dive.md` (this folder), GoEngineering topics 26, 28, 31.
