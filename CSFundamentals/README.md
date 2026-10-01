# CS Fundamentals — Start Here

How a computer runs your code, how machines talk to each other, how databases keep
data safe, how many services work as one system, how to keep all of it secure — and
how to explain every piece of it precisely under interview pressure.

This module is built for two readers at once. If you are **learning this for the first
time**, every chapter opens with a plain-language *Foundations* section that assumes
nothing and builds from first principles with everyday analogies. If you are
**preparing for an interview at any level**, the numbered sections go on to the
mechanism-level depth interviewers probe, with a **Precision note** wherever a common
simplification is wrong, and a table of what each level is expected to know.

## How to Learn From This Module

Every chapter gives you four things. Use all four — reading alone produces the feeling
of understanding, not the ability to explain.

| | What it is | How to use it |
|---|---|---|
| **Foundations** | The mental model in plain language, the vocabulary, and one picture of how the parts fit | Read it first, even if you think you know the topic; it is short |
| **Deep dive** | Numbered sections with the mechanism, numbers, runnable code and precision notes | Read one section per sitting; run the code |
| **Live labs** | Interactive, animated diagrams placed next to the text they explain | Do what the *Try it* paragraph says, then predict before you press play |
| **Checklist and levels table** | What a strong answer covers, by level | Close the chapter and answer each item out loud |

Then test yourself with the **interview question bank** (chapter 12): questions
tagged by level, with layered answers hidden until you've tried.

## The Learning Path

The chapters keep their original file numbers — other modules cite them as
"`CSFundamentals/03` §3" — but the best order to *learn* them is by part. The web app
lists them in this order.

| Part | Chapters | After this part you can… |
|---|---|---|
| **1 · Measuring cost** | [07 Complexity analysis](07_complexity_analysis_deep_dive.md), [06 Data structure internals](06_data_structure_internals_deep_dive.md) | Predict how code scales from its loops and its data structures, read input constraints, and explain why memory layout matters as much as Big-O |
| **2 · One machine** | [13 Computer architecture](13_computer_architecture_deep_dive.md), [01 Operating systems](01_operating_systems_deep_dive.md), [14 Memory management](14_memory_management_deep_dive.md), [05 Concurrency](05_concurrency_deep_dive.md) | Explain how bits represent numbers and text, how the CPU and caches run your code, what the OS does with processes, memory, files and I/O, how memory is allocated and garbage-collected, and write concurrent code that is correct |
| **3 · Many machines** | [02 Networking](02_networking_deep_dive.md), [03 Databases](03_databases_deep_dive.md), [15 Distributed systems](15_distributed_systems_deep_dive.md) | Trace a request across the network, explain how databases store, index, isolate, replicate and partition data, and reason about failure, time, consistency and consensus across machines |
| **4 · Systems of services** | [04 Software engineering & architecture](04_software_engineering_deep_dive.md), [11 Security](11_security_fundamentals_deep_dive.md) | Design services that survive failure and change, and reason about trust boundaries, identity and attacks |
| **5 · Performing in the interview** | [08 Python for interviews](08_python_for_coding_interviews_deep_dive.md), [09 The 45-minute coding round](09_coding_round_execution_deep_dive.md), [10 Google-style follow-ups](10_google_follow_ups_deep_dive.md), [12 Interview question bank](12_interview_question_bank_deep_dive.md) | Turn knowledge into performance: the right standard-library tool, a clean 45-minute round, strong follow-ups, and rehearsed answers at your level |

Each part only depends on the ones before it, and each chapter's Foundations section
is self-contained, so you can also jump straight to the chapter you need.

## Live Labs: Learn by Poking at It

Every lab is interactive and animated, and sits beside the section it explains. Each
has a *Try it* paragraph that says what to do and what to notice.

| Chapter | Lab | What you see |
|---|---|---|
| 07 | Growth-rate race | Steps and wall-clock time for O(1) … O(n!) as n grows, and the largest n each class handles in one second |
| 07 | Recursion tree and the master theorem | Work per level of a divide-and-conquer recursion, and which of the three cases applies |
| 07, 06 | Dynamic-array growth | Why append is O(1) amortized with doubling, and O(n) with a constant increment |
| 06, 01 | Cache lines and loop order | Row-order vs column-order loops through a small LRU cache: same Big-O, very different hit rates |
| 06 | Hash table internals | Chaining vs linear probing, clustering, load factor, resizing and tombstones |
| 06 | Binary heap | Push, pop and heapify, shown as a tree and as the array it really is |
| 06, 03 | B+ tree | Splits, growth at the root, search paths and why lookups take 3–4 page reads |
| 06 | Dict lookup flow | One CPython dictionary lookup, step by step |
| 01 | Latency numbers | Order-of-magnitude costs on a log scale, in human time, against a latency budget |
| 01 | CPU scheduling | FCFS, shortest-job-first, shortest-remaining-time and round robin on a Gantt chart |
| 01 | OS architecture, false sharing, page fault | Data flow through the OS, cache-line ping-pong between cores, and a page fault resolved |
| 05 | A data race you can step through | You choose the interleaving of `counter += 1` on two threads; then a mutex and an atomic |
| 05 | Producer–consumer | A bounded buffer, blocking and backpressure vs an unbounded queue that grows forever |
| 05 | Deadlock flow | Two threads acquiring locks in opposite order |
| 02 | Web request, DNS, TCP, TLS 1.3, L4/L7 flows | Each protocol step by step, with timings |
| 02 | TCP sliding window | Window, ACKs, loss, retransmission and the bandwidth-delay product |
| 02 | CUBIC vs BBR | Two congestion-control algorithms racing on the same link |
| 03 | LSM tree, MVCC, Spanner commit, CAP partition | Compaction, snapshot reads, TrueTime commit wait, CP vs AP behaviour |
| 03 | Isolation levels vs anomalies | Two transactions stepped statement by statement at each isolation level, with the anomaly table generated live |
| 03 | Logical clocks | Lamport and vector clocks: happened-before vs concurrent |
| 03 | Consistent hashing | How few keys move when a server joins or leaves the ring |
| 04 | Outbox, saga, circuit breaker | Reliable events, compensations, failing fast |
| 04 | Availability arithmetic | Series vs redundant components, soft dependencies, a simulated year against an SLO |
| 04 | Queueing and utilization | Why latency explodes as servers near 100% busy |
| 10 | Bloom filter and count-min sketch | Trading accuracy for memory in stream follow-ups |
| 13 | Cache lines and loop order | The memory hierarchy from the CPU's side, next to a measured pointer-chase curve |
| 15 | Logical clocks, replication, quorums, Raft, idempotency, gossip | Failure and agreement across machines, each beside a runnable simulation |
| 11 | OAuth PKCE, TLS 1.3, CORS | The security protocols, step by step |

## Study Plan by Target Level

The same chapters serve every level; what changes is how far into each you go.

| Target | Read | You should be able to |
|---|---|---|
| **L3 · Junior / new grad** | Parts 1 and 5 fully; `13` §1–§5; the Foundations of every other chapter; the L3 questions in the bank | Explain Big-O with examples, pick the right data structure, describe process vs thread, stack vs heap, TCP vs UDP, what an index and a transaction are, why floats are inexact |
| **L4 · Mid** | Everything above, plus the deep dives of 01, 14, 05, 02 and 03; L3–L4 questions | Explain mechanisms: hash-map internals, context switches, reference counting and GC, deadlock prevention, the TCP handshake, isolation anomalies, replication lag |
| **L5 · Senior** | The whole module, including 04, 11, 13 and 15; every lab; L3–L5 questions | Quantify and compare: latency numbers, branch and cache effects, GC trade-offs, BDP, B-tree vs LSM, linearizability, Raft, CAP and PACELC, retries and circuit breakers, SLOs; raise failure modes unprompted |
| **L6+ · Staff** | The whole module, then the System Design module; the L6 questions | Reason across systems: debug tail latency from the OS up, plan a database scaling path, design secrets management, set SLOs and error-budget policy |

A good weekly rhythm: one part per week — Foundations first, then one deep-dive section
a day with its lab, then that part's questions from the bank at the end of the week.

## Two Ways to Read This Module

**Track A — learn it from scratch.** Follow the parts in order, 1 to 5. Each step
builds on the one before: complexity is the vocabulary for everything; data structures
are what the OS, databases and caches are built from; the hardware chapter explains what
those structures cost on a real CPU; the OS and memory chapters explain what runs your
program and who frees its memory; concurrency only makes sense once you know what a
thread and a core are; networking is the OS's I/O model stretched across two machines;
databases are data structures plus concurrency control, made durable and replicated;
distributed systems generalise replication into failure, time and agreement; architecture
and security are about many such systems working together.

**Track B — interview fast track.** If the basics are familiar and you are following the
12-week plan in [Google Interview Master Study Plan (L5 / Senior SWE)](../GOOGLE_INTERVIEW_PREP.md), read the
chapters in file order (01 → 12) alongside that schedule, skimming Foundations sections
you already know, then 13–15 for the hardware, memory and distributed-systems depth that
Senior loops probe. Re-read `09` and `10` the week before an onsite, and drill the
question bank daily in the last two weeks.

## The Chapters at a Glance

| # | Chapter | Foundations covers | The deep dive adds |
|---|---|---|---|
| 01 | [Operating Systems & Hardware](01_operating_systems_deep_dive.md) | What an OS, kernel, process and thread are, why a scheduler exists, RAM vs cache in one picture | CFS/EEVDF scheduling, MESI cache coherence, false sharing, CAS and futexes, epoll vs io_uring, virtual memory and NUMA, process lifecycle, syscalls and interrupts, signals, IPC, file systems and durability, page replacement |
| 02 | [Networking & Distributed Communication](02_networking_deep_dive.md) | Client/server, IP addresses and ports, what TCP and UDP guarantee, HTTP in one round trip | TCP handshake internals, CUBIC vs BBR, HTTP/1.1 → 2 → 3, L4 vs L7 load balancing, the TLS 1.3 handshake, DNS; measured: connection reuse, the 40 ms Nagle stall, client-side failure modes, head-of-line blocking |
| 03 | [Database Storage Engines](03_databases_deep_dive.md) | Why databases exist, their components and one query's path through them, ACID, design trade-offs | B+ trees vs LSM trees, MVCC, isolation levels, replication, Paxos/Raft, TrueTime, CAP and PACELC, query planning, crash recovery, partitioning; measured: anomalies in a small MVCC engine, LSM amplification, random-key B-tree writes, commit cost |
| 04 | [Software Engineering & Architecture](04_software_engineering_deep_dive.md) | Why architecture exists, the parts of a service-based system, monolith vs microservices, sync calls vs events | DDD, event sourcing and CQRS, a runnable outbox, 2PC vs sagas, API evolution, resilience patterns, canaries, SLOs |
| 05 | [Concurrency](05_concurrency_deep_dive.md) | Why concurrency exists, concurrency vs parallelism, threads sharing a heap, five concurrency models | Locks, conditions and semaphores with their measured cost under contention, runnable race and deadlock demos, a bounded blocking queue, a Go worker pool, the GIL, memory models, event loops |
| 06 | [Data Structure Internals](06_data_structure_internals_deep_dive.md) | Abstract type vs implementation, invariants, contiguous vs linked memory, cache lines | How CPython, Go and Java implement hash maps, dynamic arrays, heaps, balanced trees, tries and graphs; a from-scratch hash map and heap, measured |
| 07 | [Complexity Analysis](07_complexity_analysis_deep_dive.md) | Why complexity analysis exists, the cost model, a growth-rate table with real numbers | Recursion trees, the master theorem, amortized analysis, reading constraints, runnable growth experiments, lower bounds, NP-hardness |
| 08 | [Python for Coding Interviews](08_python_for_coding_interviews_deep_dive.md) | What CPython does with your code, names vs objects, mutability and hashability | Every built-in's cost and traps, `collections`/`heapq`/`bisect`/`itertools`, classic algorithms written cold |
| 09 | [Running the 45-Minute Coding Round](09_coding_round_execution_deep_dive.md) | Why coding interviews exist, the four signals, solving vs demonstrating | The minute-by-minute timeline, clarifying questions, edge cases, recovering when stuck, verifying by trace |
| 10 | [Google-Style Follow-Ups](10_google_follow_ups_deep_dive.md) | Why follow-ups exist, silent assumptions, exact vs approximate answers | Toolkits for streams, scale, precomputation, concurrency and changed constraints; runnable stream algorithms and external sort |
| 11 | [Security Fundamentals](11_security_fundamentals_deep_dive.md) | The CIA triad, threat modelling, trust boundaries, design principles | Authn vs authz, sessions vs tokens, OAuth 2.0/OIDC, hashing vs encryption, TLS, secrets, the OWASP Top 10, supply chain |
| 12 | [Interview Question Bank](12_interview_question_bank_deep_dive.md) | How interviewers ask, and what each level must show | 62 questions across every chapter, tagged L3–L6+, each with a 30-second answer, the full mechanism and the next follow-up, plus a rapid-fire table |
| 13 | [Computer Architecture & Data Representation](13_computer_architecture_deep_dive.md) | What a computer is, the stored-program model, why bits mean nothing without a type | Two's complement and overflow, bit tricks, IEEE 754, endianness and alignment, UTF-8, how the CPU runs a loop, pipelining, branch prediction and the memory hierarchy — all measured |
| 14 | [Memory Management & Garbage Collection](14_memory_management_deep_dive.md) | A process's address space, stack vs heap, the four ways memory gets freed | Allocators and fragmentation (a toy allocator), reference counting, mark-sweep, generational and concurrent GC with write barriers (a toy collector), Go's `GOGC`/`GOMEMLIMIT`, escape analysis, finding leaks |
| 15 | [Distributed Systems Fundamentals](15_distributed_systems_deep_dive.md) | Why distribute, the fallacies, system models, what's impossible | Failure detection, logical and hybrid clocks, linearizability (a checker), quorums, a complete runnable Raft, leases and fencing, exactly-once effects, gossip, CRDTs, cross-partition transactions |

## How Every Chapter Is Structured

```text
# Title
intro paragraph                 ← what the chapter covers and why it matters

## Foundations — …              ← plain-language model, analogies, vocabulary table
## 1. <First deep-dive topic>   ← numbered sections: mechanism, numbers, runnable code,
## 2. <Next topic>                live labs, precision notes
   …
## What Each Engineering Level Should Know   ← Junior → Staff+ table
## Interview checklist
Related: links to the System Design, Software Design, SQL, NoSQL and language modules
```

The numbered sections never move: dozens of files elsewhere in the repository
(`SQL/`, `SoftwareDesign/`, [Google Interview Master Study Plan (L5 / Senior SWE)](../GOOGLE_INTERVIEW_PREP.md)) cite them by number. New
material is only ever added — a new section after the existing ones, a lab beside a
section, a new chapter at the end — so an existing reference like "`03` §3" always
points at the right place.

## Where the Deeper Material Lives

| Topic | Go deeper in |
|---|---|
| System design at scale (caching, sharding, real designs) | `SystemDesign/building_blocks/`, `SystemDesign/problems/`, and its question bank [System Design Interview Question Bank](../SystemDesign/07_interview_question_bank.md) |
| Code-level design (testability, error handling, LLD interviews) | `SoftwareDesign/` |
| PostgreSQL, MongoDB and Redis hands-on | `SQL/`, `NoSQL/` |
| Language-specific engineering depth | `PyEngineering/`, `GoEngineering/` |
| Security in system design; OIDC and SSO in depth | [Security](../SystemDesign/building_blocks/14_security.md), [OpenID Connect and Single Sign-On](../API/Fundamentals/05_openid_connect_and_sso.md) |
| DSA problems to apply all of this to | `PyDSA/`, `GoDSA/`, [Curriculum Index](../CURRICULUM.md) |
