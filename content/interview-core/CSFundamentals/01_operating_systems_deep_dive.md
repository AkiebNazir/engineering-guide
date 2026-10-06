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
| **Network stack** | Implements TCP/IP (and friends) so a process can exchange bytes with a process on another machine | §7 here; the full treatment is [Networking & Distributed Communication](02_networking_deep_dive.md) |
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
  half, and [Concurrency](05_concurrency_deep_dive.md) is the full treatment.

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

**Try it: feel the gaps.** Every idea in the list above is a response to the spread of these numbers. Switch to human scale: if an L1 cache hit took one second, a RAM access would take almost two minutes, a random SSD read five and a half hours, and a round trip from California to the Netherlands almost five years.

<div class="lab" data-viz="cs-latency"></div>

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

**Try it: the classic policies first.** CFS makes more sense once you have felt the problems it solves. Run the “one long job first” workload under first-come-first-served (the convoy effect), then shortest-job-first (the best average wait, but it needs to know the future), then round robin with a small and a large time slice (good response time, paid for in context switches). CFS answers the same questions without a fixed slice: it always runs whichever task has had the least CPU time so far.

<div class="lab" data-viz="cs-sched"></div>

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

**Try it: cache lines before coherence.** MESI tracks *cache lines*, so first see what a line does for a single core. Run the row-order loop (each miss brings the next three values along for free), then the column-order loop with a small cache (every access misses). False sharing, below, is the multi-core version of the same effect: two cores fighting over one line.

<div class="lab" data-viz="cs-locality"></div>

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

<div class="lab" data-viz="flow-page-fault"></div>

## 6. Processes, Threads, and Containers

| Concept | Isolation | Cost to create | Communication |
|---|---|---|---|
| Process | Separate address space | `fork`+`exec`; COW makes `fork` cheap until pages are written | Pipes, sockets, shared memory, signals |
| Thread | Shared address space | Cheaper (clone with shared memory) | Shared memory + locks |
| Goroutine / green thread | Scheduled by a runtime | ~2-8 KB initial stack, growable | Channels, shared memory |
| Container | Same kernel; isolated by **namespaces** (pid, net, mount, user, uts, ipc) and limited by **cgroups** (CPU, memory, I/O) | Process start + namespace setup | Network or volumes |
| VM | Separate kernel on a hypervisor | Seconds | Virtual network |

Interview-ready one-liner: **a container is a process with namespaces for isolation and cgroups for limits; it is not a lightweight VM.** Google's Borg (and its paper, see [The Papers Behind Google-Scale Systems](../SystemDesign/building_blocks/24_google_papers.md)) is where much of the cgroups work originated.

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

## 8. The Life of a Process: fork, exec, wait, Zombies and Orphans

Every process on Linux except the first is created by another one, and the kernel tracks it
through a small set of states:

```arch
%% caption: Process states: a runnable process waits for a core, a running one can block on I/O or be preempted, and an exited one stays a zombie until its parent collects the exit status.
grid 170x100
node new "Created" at 0,0 shape=pill color=slate sub="fork() / clone()"
node rdy "Runnable" at 1,0 shape=circle color=blue sub="R: waiting for a core"
node run "Running" at 2,0 shape=circle color=green sub="R: on a core"
node blk "Sleeping" at 2,2 shape=circle color=amber sub="S / D: waiting"
node zom "Zombie" at 3,0 shape=circle color=red sub="Z: not yet reaped"
node gone "Reaped" at 3,2 shape=pill color=slate sub="parent called wait()"
new -> rdy
rdy -> run : "scheduled"
run -> rdy : "preempted"
run -> blk : "blocks"
blk -> rdy : "woken"
run -> zom : "exit()"
zom -> gone : "wait()"
```

- **`fork()`** creates a copy of the calling process (cheap thanks to copy-on-write, §6);
  both continue from the same line, told apart only by `fork`'s return value (0 in the
  child). **`exec()`** replaces the current program with a new one, keeping the process ID and
  open file descriptors — which is how a shell runs a command and how `<` and `>` redirection
  work: the shell rearranges file descriptors between `fork` and `exec`.
- **`exit()`** doesn't make a process disappear. The kernel keeps a small entry — PID and
  exit status — until the parent collects it with **`wait()`**. Until then the process is a
  **zombie**.
- If the parent dies first, the child is an **orphan** and is re-parented to PID 1 (or a
  designated "subreaper"), which reaps it.

```python
"""fork, exit, zombie, reap: the life and death of a Unix process."""
import os, time

def state(pid):
    with open(f"/proc/{pid}/status") as f:
        return next(l.split(":", 1)[1].strip() for l in f if l.startswith("State"))

pid = os.fork()
if pid == 0:                      # child: a copy of the parent, running from the same line
    time.sleep(0.1)
    os._exit(7)                   # exit code 7
print(f"parent {os.getpid()} forked child {pid}; child state: {state(pid)}")
time.sleep(0.3)                   # child has exited, but we haven't waited for it
print(f"child exited, not yet reaped; state: {state(pid)}")
_, status = os.waitpid(pid, 0)    # reap: collect the exit status, free the process entry
print(f"after waitpid: exit code {os.waitstatus_to_exitcode(status)}; /proc entry exists: {os.path.exists(f'/proc/{pid}')}")
```

```text
parent 7431 forked child 7432; child state: S (sleeping)
child exited, not yet reaped; state: Z (zombie)
after waitpid: exit code 7; /proc entry exists: False
```

The child sleeps (`S`), exits, and sits as a zombie (`Z`) until `waitpid` collects exit code 7.
Zombies use no memory or CPU, but each holds a PID; a server that forks children and never
waits for them eventually cannot create processes at all. **This is also why containers need
an init process**: in a container, your application *is* PID 1, and if it spawns subprocesses
and doesn't reap them, zombies accumulate — hence `tini`, `dumb-init` and Docker's `--init`.

The `D` state ("uninterruptible sleep") is worth knowing: a process waiting on certain disk or
NFS I/O can't even be killed until the I/O returns. A load average that climbs while the CPUs
are idle is usually processes stuck in `D`, because Linux counts them in the load average.

## 9. System Calls and Interrupts: How Control Reaches the Kernel

The CPU enters the kernel for exactly three reasons, and every "the OS did something" moment
is one of them:

| Entry | Triggered by | Examples |
|---|---|---|
| **System call** | The program, on purpose (`syscall` instruction on x86-64) | `read`, `write`, `mmap`, `futex`, `clone` |
| **Exception (fault/trap)** | The instruction the program just ran | Page fault (§5), divide by zero, invalid instruction, breakpoint |
| **Interrupt** | A device, asynchronously | Network card has packets, disk finished a request, the timer ticked |

A system call switches the CPU to kernel mode, saves registers, runs the handler, and returns.
Measured on this machine against a plain function call:

```c
// The price of crossing into the kernel: a trivial system call vs a function call.
#define _GNU_SOURCE
#include <stdio.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

__attribute__((noinline)) static long plain(long x) { __asm__ volatile(""); return x + 1; }

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec * 1e9 + t.tv_nsec; }

int main(void) {
    const int n = 5000000;
    long s = 0;
    double t = now();
    for (int i = 0; i < n; i++) s += plain(i);
    double fn = (now() - t) / n;
    t = now();
    for (int i = 0; i < n; i++) s += syscall(SYS_getppid);   // really enters the kernel
    double sc = (now() - t) / n;
    t = now();
    for (int i = 0; i < n; i++) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); s += ts.tv_nsec & 1; }
    double vd = (now() - t) / n;
    printf("function call        %6.1f ns\n", fn);
    printf("getppid() syscall    %6.1f ns\n", sc);
    printf("clock_gettime (vDSO) %6.1f ns   (answered in user space, no kernel entry)\n", vd);
    return s == 42 ? 1 : 0;   // use s so the loops are not optimised away
}
```

```text
$ gcc -O2 -Wall -o syscall syscall.c && ./syscall
function call           1.3 ns
getppid() syscall      95.9 ns
clock_gettime (vDSO)   19.9 ns   (answered in user space, no kernel entry)
```

- **A trivial syscall costs ~100 ns here — about 70× a function call.** The kernel does almost
  nothing for `getppid`; the cost is the mode switch plus the Spectre/Meltdown mitigations on
  entry and exit ([Computer Architecture & Data Representation](13_computer_architecture_deep_dive.md) §10). On bare metal without
  mitigations it is several times cheaper, which is why published figures vary.
- **The vDSO avoids the trip entirely.** The kernel maps a small shared library into every
  process that answers `clock_gettime` and `gettimeofday` from memory the kernel keeps updated —
  a syscall made cheap by not being one.
- **Batching is the performance lever.** Reading a file 1 byte per `read()` pays the entry cost
  per byte; buffered I/O (Python's `open`, Go's `bufio`) reads 8 KB or more per call. `io_uring`
  (§4) and `sendfile` exist to amortise or skip crossings.

`strace` shows every call a program makes. Even `python3 -c "pass"` is not quiet:

```text
$ strace -c -f python3 -c "pass"
...
100.00    0.002708           7       364        49 total
```

364 system calls — opening and `stat`-ing modules, setting up signal handlers — just to start
and exit the interpreter. `strace` is the first tool to reach for when a program hangs ("which
syscall is it blocked in?") or is slow for no visible reason; `perf trace` and eBPF tools do the
same with far less overhead in production.

**Interrupts and the timer.** Devices signal the CPU with interrupts; the kernel runs a short
top-half handler immediately and defers the rest to *softirqs* or kernel threads. A periodic
**timer interrupt** is what lets the scheduler preempt a thread that never blocks (§1): without
it, a busy loop would hold a core forever. High-rate network traffic can spend a large share of a
core in interrupt and softirq processing, which is why NICs coalesce interrupts, why kernels
switch to polling under load (NAPI), and why `/proc/interrupts` and the `si` column in `top` are
worth checking when a network-heavy service burns CPU it can't account for.

## 10. Signals: Asynchronous Notifications to a Process

A signal is the kernel interrupting a *process* the way a hardware interrupt interrupts a CPU.
It arrives between any two instructions and runs a handler, or a default action.

| Signal | Sent when | Default | Can be handled? |
|---|---|---|---|
| `SIGTERM` | "Please stop" — `kill`, Kubernetes, systemd on shutdown | Terminate | Yes: clean up and exit |
| `SIGINT` | Ctrl-C in a terminal | Terminate | Yes (Python raises `KeyboardInterrupt`) |
| `SIGKILL` | `kill -9`, the OOM killer | Terminate | **No** — can't be caught, blocked or ignored |
| `SIGSEGV` | Invalid memory access | Terminate + core dump | Technically, but only to log and die |
| `SIGCHLD` | A child exited | Ignore | Yes: reap it with `wait()` (§8) |
| `SIGPIPE` | Writing to a pipe or socket nobody reads | Terminate | Yes; servers usually ignore it and handle `EPIPE` |
| `SIGHUP` | Terminal closed; by convention "reload config" for daemons | Terminate | Yes |

Graceful shutdown is the case every service must get right:

```python
"""SIGTERM can be handled (graceful shutdown); SIGKILL cannot."""
import os, signal, subprocess, sys, time

CHILD = r'''
import signal, sys, time
stopping = False
def on_term(signum, frame):
    global stopping
    stopping = True                         # only set a flag: keep handlers tiny
signal.signal(signal.SIGTERM, on_term)
print("worker: ready", flush=True)
done = 0
while not stopping:
    time.sleep(0.01)                        # "process one request"
    done += 1
print(f"worker: SIGTERM after {done} requests; finished the current one, exiting cleanly", flush=True)
sys.exit(0)
'''
for sig in (signal.SIGTERM, signal.SIGKILL):
    p = subprocess.Popen([sys.executable, "-c", CHILD], stdout=subprocess.PIPE, text=True)
    p.stdout.readline()
    time.sleep(0.2)
    p.send_signal(sig)
    out = p.stdout.read().strip()
    print(f"{sig.name}: exit code {p.wait()}  {out or '(no chance to clean up)'}")
```

```text
SIGTERM: exit code 0  worker: SIGTERM after 20 requests; finished the current one, exiting cleanly
SIGKILL: exit code -9  (no chance to clean up)
```

With `SIGTERM`, the worker's handler sets a flag, the loop finishes the request in progress, and
the process exits with 0. With `SIGKILL` the process simply vanishes mid-request (Python reports
−9; a shell shows exit code 137 = 128 + 9, the number to recognise in container logs as "killed,"
very often by the OOM killer, §5).

This is exactly Kubernetes' termination contract: it sends `SIGTERM`, waits
`terminationGracePeriodSeconds` (30 s by default), then sends `SIGKILL`. A service that ignores
`SIGTERM` drops every in-flight request on every deploy.

Two rules for handlers: **keep them tiny** (set a flag, write to a self-pipe) because they
interrupt arbitrary code — calling `malloc`, taking a lock or logging inside a C signal handler
can deadlock if the interrupted code held the same lock; and **handle `SIGTERM` in PID 1**,
because the kernel doesn't apply default "terminate" actions to a container's init process that
hasn't installed a handler — the classic "my container takes 30 seconds to stop" bug.

## 11. Inter-Process Communication

Threads share memory for free; processes are isolated by design (§6), so they communicate
through the kernel:

| Mechanism | Shape | Typical use |
|---|---|---|
| **Pipe** | One-way byte stream between related processes | Shell pipelines (`a \| b`), parent ↔ child |
| **Unix domain socket** | Bidirectional stream or datagrams, addressed by a file path | Local database connections (PostgreSQL, MySQL), Docker's API, sidecars; can pass file descriptors and credentials |
| **TCP/UDP over loopback** | The network stack, pointed at `127.0.0.1` | Same code path for local and remote peers |
| **Shared memory** (`mmap`, `shm_open`) | The same physical pages mapped into both processes | High-throughput data exchange; needs its own synchronisation |
| **Signals** | A number, no data | Notifications (§10) |
| **Message queues, files, `eventfd`** | Various | Less common today |

Throughput for moving 1 GiB between two processes in 1 MiB chunks, three runs:

```python
"""Move 1 GiB between two processes four ways, in 1 MiB chunks."""
import os, socket, time
from multiprocessing import shared_memory

CHUNK, TOTAL = 1 << 20, 1 << 30
payload = b"x" * CHUNK

def recv_all(read, n):
    got = 0
    while got < n:
        b = read(min(CHUNK, n - got))
        if not b:
            break
        got += len(b)
    return got

def bench(name, make_pair):
    a_write, b_read, closers = make_pair()
    t = time.perf_counter()
    pid = os.fork()
    if pid == 0:                                   # child: the sender
        for _ in range(TOTAL // CHUNK):
            view = memoryview(payload)
            while view:
                view = view[a_write(view):]
        os._exit(0)
    got = recv_all(b_read, TOTAL)
    os.waitpid(pid, 0)
    dt = time.perf_counter() - t
    for c in closers:
        c()
    print(f"{name:26} {got / dt / 1e9:5.2f} GB/s")

def pipe_pair():
    r, w = os.pipe()
    return (lambda b: os.write(w, b)), (lambda n: os.read(r, n)), [lambda: os.close(r), lambda: os.close(w)]

def big_pipe_pair():
    import fcntl
    r, w = os.pipe()
    fcntl.fcntl(w, fcntl.F_SETPIPE_SZ, 1 << 20)          # 64 KiB default -> 1 MiB buffer
    return (lambda b: os.write(w, b)), (lambda n: os.read(r, n)), [lambda: os.close(r), lambda: os.close(w)]

def unix_pair():
    s1, s2 = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    return s1.send, s2.recv, [s1.close, s2.close]

def tcp_pair():
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1)
    c = socket.create_connection(srv.getsockname()); s, _ = srv.accept()
    return c.send, s.recv, [c.close, s.close, srv.close]

bench("pipe (64 KiB buffer)", pipe_pair)
bench("pipe (1 MiB buffer)", big_pipe_pair)
bench("Unix domain socket", unix_pair)
bench("TCP over loopback", tcp_pair)

# Shared memory: no kernel copy per message; both processes map the same pages.
shm = shared_memory.SharedMemory(create=True, size=CHUNK)
t = time.perf_counter()
pid = os.fork()
if pid == 0:
    for _ in range(TOTAL // CHUNK):
        shm.buf[:CHUNK] = payload                  # the writer's only cost: one memcpy
    os._exit(0)
os.waitpid(pid, 0)
dt = time.perf_counter() - t
print(f"{'shared memory (write only)':26} {TOTAL / dt / 1e9:5.2f} GB/s  (no synchronisation: an upper bound)")
shm.close(); shm.unlink()
```

| Mechanism | Throughput (three runs) |
|---|---|
| pipe, default 64 KiB buffer | 0.70–0.85 GB/s |
| pipe, 1 MiB buffer | 1.87–2.16 GB/s |
| Unix domain socket | 1.66–1.94 GB/s |
| TCP over loopback | 1.72–1.88 GB/s |
| shared memory, writer only | 13–17 GB/s |

- **Every kernel-mediated mechanism copies twice** (sender's buffer → kernel → receiver's buffer)
  and pays a syscall per chunk; that is why they land together, at 1–2 GB/s.
- **The default pipe is slowest because its buffer is small.** With 64 KiB the writer blocks
  every 64 KiB and the two processes take turns; raising it to 1 MiB (`F_SETPIPE_SZ`) closes the
  gap — the same buffer-size effect as TCP's window (`02` §2).
- **Shared memory avoids the kernel on the data path**, so the only cost is one `memcpy` — about
  8–10× faster here. But this figure has no synchronisation at all; a real shared-memory channel
  needs a lock-free ring buffer or a futex to tell the reader when data is ready, and every bug in
  that code is yours (§2–§3). Databases (PostgreSQL's shared buffers), browsers and high-frequency
  trading systems pay that price.

For small messages the story changes. A 1-byte ping-pong between two processes took **~51 µs
per round trip over a Unix socket and ~53 µs over loopback TCP** here: almost all of it is waking
the other process and switching to it, not the protocol. Chatty IPC is latency-bound; batch
messages or share memory when round trips dominate.

## 12. File Systems: Inodes, Links, the Page Cache, and Durability

A file system maps names to data on a block device. The key design idea, from the original Unix,
is to separate the two:

- An **inode** holds everything about a file except its name: size, owner, permissions,
  timestamps, and pointers to the data blocks (in ext4, a tree of *extents*).
- A **directory** is just a file mapping names to inode numbers.
- So a file can have several names (**hard links**), and "deleting a file" (`unlink`) only
  removes one name. The inode and its data are freed when the link count reaches zero **and no
  process has the file open**.

```python
"""Inodes, links, deleting an open file, and the cost of durability."""
import os, shutil, tempfile, time

d = tempfile.mkdtemp(dir=".")
p = lambda name: os.path.join(d, name)

# 1) A file name is just a directory entry pointing at an inode.
with open(p("data.txt"), "w") as f:
    f.write("hello\n")
os.link(p("data.txt"), p("hard.txt"))           # a second name for the same inode
os.symlink("data.txt", p("soft.txt"))           # a separate file holding a path
for name in ("data.txt", "hard.txt", "soft.txt"):
    st = os.lstat(p(name))
    print(f"1) {name:9} inode {st.st_ino}  links {st.st_nlink}  {'symlink' if os.path.islink(p(name)) else 'regular'}")
os.remove(p("data.txt"))
print("   after deleting data.txt: hard.txt reads", repr(open(p("hard.txt")).read()),
      "| soft.txt exists?", os.path.exists(p("soft.txt")))

# 2) Deleting an open file removes the name, not the data.
big = p("big.log")
with open(big, "wb") as f:
    f.write(os.urandom(50 << 20))
f = open(big, "rb")
before = shutil.disk_usage(d).free
os.remove(big)
print(f"2) name removed; open handle still reads {len(f.read(10))} bytes; "
      f"space freed so far: {(shutil.disk_usage(d).free - before) >> 20} MB")
f.close()
print(f"   after close: space freed: {(shutil.disk_usage(d).free - before) >> 20} MB")

# 3) write() lands in the page cache; fsync() waits for the device.
def append(n, sync):
    with open(p("wal.log"), "ab") as f:
        t = time.perf_counter()
        for i in range(n):
            f.write(b"record %06d\n" % i)
            f.flush()                            # Python buffer -> kernel page cache
            if sync:
                os.fsync(f.fileno())             # page cache -> disk, and wait
        return (time.perf_counter() - t) / n * 1e6
print(f"3) append without fsync: {append(2000, False):7.1f} µs/record")
print(f"   append with fsync:    {append(2000, True):7.1f} µs/record")

# 4) Replace a file atomically: write a temp file, fsync it, rename over the old one.
def atomic_write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())                     # the new contents are durable...
    os.replace(tmp, path)                        # ...then the swap is one atomic rename
    dfd = os.open(os.path.dirname(path), os.O_RDONLY)
    os.fsync(dfd)                                # ...and the rename itself is durable
    os.close(dfd)
atomic_write(p("config.json"), b'{"version": 2}')
print("4) config.json:", open(p("config.json")).read(), "| readers saw either the old or the new file, never half")
shutil.rmtree(d)
```

```text
1) data.txt  inode 1884402  links 2  regular
1) hard.txt  inode 1884402  links 2  regular
1) soft.txt  inode 1884417  links 1  symlink
   after deleting data.txt: hard.txt reads 'hello\n' | soft.txt exists? False
2) name removed; open handle still reads 10 bytes; space freed so far: 0 MB
   after close: space freed: 50 MB
3) append without fsync:     1.2 µs/record
   append with fsync:      218.5 µs/record
4) config.json: {"version": 2} | readers saw either the old or the new file, never half
```

(ext4 on a virtual disk.)

1. **Hard vs symbolic links.** `hard.txt` is the same inode as `data.txt` (link count 2), so it
   survives the deletion of `data.txt`. `soft.txt` is its own tiny file containing the *path*
   `data.txt`; once that path is gone it dangles.
2. **Deleting an open file frees nothing** until the last handle closes. This is the classic
   "`df` says the disk is full but `du` can't find the files" incident: a process still holds a
   deleted log file open. `lsof +L1` lists such files; restarting the process (or truncating the
   file through `/proc/<pid>/fd`) releases the space.
3. **`write()` is not durable; `fsync()` is.** Appending a record without `fsync` costs ~1 µs —
   it only copies into the page cache (§5). With `fsync` after every record it costs ~220 µs,
   because each call waits for the device to confirm the data is stored. On laptop SSDs and
   network block devices the gap is often milliseconds. This is the central trade-off of every
   database's commit path: **group commit** amortises one `fsync` over many transactions, and
   settings like PostgreSQL's `synchronous_commit` or Redis's `appendfsync` choose between
   durability and throughput (`03` §9).
4. **Atomic replacement.** The only safe way to update a whole file is: write a temporary file in
   the same directory, `fsync` it, `rename` it over the original (rename within one file system is
   atomic), then `fsync` the directory so the rename itself survives a crash. Readers see the old
   file or the new one, never a torn mix. Editors, package managers and config-reload code all
   rely on this recipe; skipping either `fsync` is how "the config file was empty after the power
   cut" happens.

**Journaling.** A crash in the middle of an operation that touches several blocks (allocate a
block, update the inode, update the directory) would leave the file system inconsistent. Journaling
file systems (ext4, XFS, NTFS) first write the intended changes to a **journal**, then apply them;
after a crash they replay or discard journal entries instead of scanning the whole disk. By
default ext4 journals only metadata (`data=ordered`), so the file system stays consistent, but
the *contents* of a file written without `fsync` can still be lost — the application's
responsibility, as item 3 shows. Copy-on-write file systems (ZFS, Btrfs) never overwrite in place
and get the same consistency from atomic pointer swaps — the same idea as an LSM tree or MVCC
(`03` §1–§2).

## 13. Page Replacement: Choosing What to Evict

When physical memory is full and a process touches a page that isn't resident (a major fault,
§5), the kernel must evict another page — write it back if it's dirty, or simply drop it if it's a
clean copy of a file. Which page to evict is the same problem as evicting from any cache, which is
why interviewers ask it both ways. A simulation of the classic policies on the same reference
stream:

```python
"""Page replacement: count page faults for FIFO, LRU, CLOCK and the optimal
(clairvoyant) policy on the same stream of page references."""
import random
from collections import OrderedDict, deque


def fifo(refs, frames):
    mem, order, faults = set(), deque(), 0
    for p in refs:
        if p not in mem:
            faults += 1
            if len(mem) == frames:
                mem.discard(order.popleft())     # evict the page loaded longest ago
            mem.add(p); order.append(p)
    return faults


def lru(refs, frames):
    mem, faults = OrderedDict(), 0
    for p in refs:
        if p in mem:
            mem.move_to_end(p)
        else:
            faults += 1
            if len(mem) == frames:
                mem.popitem(last=False)          # evict the least recently used
            mem[p] = True
    return faults


def clock(refs, frames):
    slots, ref, hand, where, faults = [None] * frames, [0] * frames, 0, {}, 0
    for p in refs:
        if p in where:
            ref[where[p]] = 1                    # hardware sets the accessed bit
            continue
        faults += 1
        while ref[hand]:                         # second chance: clear bits until one is 0
            ref[hand] = 0
            hand = (hand + 1) % frames
        if slots[hand] is not None:
            del where[slots[hand]]
        slots[hand], ref[hand], where[p] = p, 1, hand
        hand = (hand + 1) % frames
    return faults


def opt(refs, frames):
    mem, faults = set(), 0
    for i, p in enumerate(refs):
        if p in mem:
            continue
        faults += 1
        if len(mem) == frames:                   # evict the page used furthest in the future
            future = {q: next((j for j in range(i + 1, len(refs)) if refs[j] == q), 1 << 30) for q in mem}
            mem.discard(max(future, key=future.get))
        mem.add(p)
    return faults


rng = random.Random(9)
hot = [rng.randrange(12) for _ in range(3000)]                       # 12 hot pages
workload = [p if rng.random() < 0.8 else rng.randrange(12, 400) for p in hot]  # + cold pages
loop = list(range(12)) * 200                                          # a loop over 12 pages
for name, refs, frames in [("80% hot / 20% cold, 16 frames", workload, 16),
                           ("loop over 12 pages, 11 frames", loop, 11)]:
    print(f"{name}:")
    for policy in (fifo, lru, clock, opt):
        f = policy(refs, frames)
        print(f"   {policy.__name__:5} {f:5} faults ({100 * f / len(refs):4.1f}%)")

belady = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
print("Belady's anomaly, FIFO:", {k: fifo(belady, k) for k in (3, 4)}, "faults for 3 vs 4 frames")
print("LRU on the same string:", {k: lru(belady, k) for k in (3, 4)})
```

```text
80% hot / 20% cold, 16 frames:
   fifo   1181 faults (39.4%)
   lru     885 faults (29.5%)
   clock   988 faults (32.9%)
   opt     516 faults (17.2%)
loop over 12 pages, 11 frames:
   fifo   2400 faults (100.0%)
   lru    2400 faults (100.0%)
   clock  2400 faults (100.0%)
   opt     229 faults ( 9.5%)
Belady's anomaly, FIFO: {3: 9, 4: 10} faults for 3 vs 4 frames
LRU on the same string: {3: 10, 4: 8}
```

- **LRU is the practical ideal.** On a workload with a hot set that fits in memory, LRU faults
  least of the real policies (29.5% vs FIFO's 39.4%). **OPT** — evict the page used furthest in the
  future — is optimal but needs to know the future; it's the benchmark, not an algorithm.
- **CLOCK approximates LRU cheaply** (32.9%). Exact LRU would need to update a list on *every
  memory access*, which hardware can't afford. Instead the MMU sets an *accessed bit* in the page
  table entry; CLOCK sweeps a hand over the frames, clearing bits and evicting the first page whose
  bit is already clear ("second chance"). Linux uses a refinement of this idea — active and inactive
  lists, and since 6.1 the multi-generational LRU.
- **A loop slightly larger than memory defeats LRU completely.** Cycling over 12 pages with 11
  frames, LRU always evicts exactly the page needed next: 100% faults. This is **thrashing** in
  miniature — a working set just over memory makes the system spend its time paging, and
  throughput collapses. It is also why databases use scan-resistant policies (PostgreSQL's ring
  buffers for sequential scans, LRU-K, 2Q, ARC) instead of plain LRU.
- **Belady's anomaly:** with FIFO, *more* memory can mean *more* faults (9 faults with 3 frames,
  10 with 4). LRU can't do this — it's a *stack algorithm*: the pages held with *k* frames are
  always a subset of those held with *k* + 1.

[Python for Coding Interviews](08_python_for_coding_interviews_deep_dive.md) §8 and `PyDSA/08_linked_list/013_lru_cache` implement an LRU cache in O(1)
with a hash map and a doubly linked list — the same policy, in software, where the cost of
tracking every access *is* affordable.

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
| **Process lifecycle & signals** (§8, §10) | Knows a process can be killed | Explains fork/exec/wait and handles SIGTERM for graceful shutdown | Explains zombies, orphans, PID 1 in containers, SIGKILL vs SIGTERM and exit code 137 | Designs shutdown and draining behaviour for a fleet (grace periods, preStop hooks, connection draining) |
| **Syscalls, interrupts, IPC** (§9, §11) | Knows programs ask the OS for I/O | Knows syscalls cost more than calls; knows pipes and sockets | Quantifies syscall cost, uses `strace`, compares IPC mechanisms and buffer effects | Chooses batching, `io_uring`, shared memory or Unix sockets from measurements |
| **File systems & page replacement** (§12, §13) | Knows files have names and contents | Knows `fsync` makes data durable; knows LRU | Explains inodes and links, deleted-but-open files, atomic rename, journaling, CLOCK and thrashing | Sets durability and caching policy for storage-heavy systems (group commit, scan-resistant caches) |

**Reading this table as a study plan:** if you're aiming at a Senior/L5 bar, your
target is the whole "Senior" column — which is exactly what the numbered sections (1–13)
above deliver in full. The "Junior" and "Mid-Level" columns describe the
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
- [ ] I can draw the process state diagram and explain fork/exec/wait, zombies, orphans, and why containers need an init.
- [ ] I can list the three ways into the kernel (syscall, exception, interrupt) and quantify a syscall's cost.
- [ ] I can explain SIGTERM vs SIGKILL, exit code 137, and how a service shuts down gracefully in Kubernetes.
- [ ] I can compare pipes, Unix sockets, loopback TCP and shared memory, and say what limits each.
- [ ] I can explain inodes, hard vs soft links, why deleting an open file frees no space, and the atomic-rename recipe.
- [ ] I can compare FIFO, LRU, CLOCK and OPT, explain thrashing, and state Belady's anomaly.

Related: [Operating Systems for System Design](../SystemDesign/building_blocks/01_operating_systems.md), [Concurrency](05_concurrency_deep_dive.md) (this folder), GoEngineering topics 26, 28, 31.
