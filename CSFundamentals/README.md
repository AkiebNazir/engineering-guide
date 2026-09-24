# CS Fundamentals

Ten self-contained guides that cover the computer-science core every backend/systems
engineer eventually needs: how a computer schedules and runs your code, how machines
talk to each other, how databases actually store and protect data, how to design
systems that survive multiple teams and multiple years, and how to reason about all
of it precisely under interview pressure.

**This module is for two overlapping readers, and every file now serves both:**

- **You're learning this for the first time** — a student, or an engineer who has
  used threads/indexes/APIs without ever seeing *why* they work. Every file opens
  with a plain-language **Foundations** section: no prior OS/networking/database
  background assumed, built up from first principles with everyday analogies.
- **You're prepping for a Senior/Staff-level interview loop** (this repo was built
  around Google's L5 bar, but the content generalizes to any senior interview). Past
  the Foundations section, each file goes straight into the precise, myth-correcting
  depth a strong interviewer probes for — marked **Precision note** wherever a common
  simplification is wrong.

You don't have to pick one mode and stay in it. Read Foundations, stop if that's all
you needed today, come back for the deep-dive half once you're ready — or skip
straight to the deep dive if you already have the basics and just need the precise,
interview-ready version.

---

## How this guide is structured

Every file follows the same shape:

```text
# Title                          ← plain, no jargon in the heading
intro paragraph                  ← what this file covers and why it matters

## Foundations — Start Here If You're New to <Topic>
   plain-language mental model, everyday analogies, the vocabulary
   you need before the deep dive makes sense

## 1. <First deep-dive topic>    ← numbered sections = the original interview-depth
## 2. <Next topic>                 content, unchanged, so every existing cross-reference
   ...                             (§N) from other modules still points at the right place

## Interview checklist
Related: <links to SystemDesign / SoftwareDesign / SQL / NoSQL / GoEngineering / PyEngineering>
```

The numbered `## N.` sections and their order were left exactly as they were — dozens
of files elsewhere in this repo (`SQL/`, `SoftwareDesign/`, `GOOGLE_INTERVIEW_PREP.md`)
cross-reference them by number (e.g. "`CSFundamentals/03` §3"). Only the on-ramp
(**Foundations**) is new, and it's additive: skip it entirely and the file reads
exactly as it did before.

---

## Two ways to read this module

### Track A — Learn CS fundamentals from scratch

Read in **this** order, not the file-number order. Each step lists the specific
prerequisite it leans on from the step before it.

| Step | File | What it builds on | Why it comes here |
|---|---|---|---|
| 1 | [`07_complexity_analysis_deep_dive.md`](07_complexity_analysis_deep_dive.md) | Nothing | Big-O is the vocabulary every other file uses to describe cost. Learn it first. |
| 2 | [`06_data_structure_internals_deep_dive.md`](06_data_structure_internals_deep_dive.md) | Big-O (step 1) | Arrays, hash maps, trees, and heaps are the building blocks every system below is made of. |
| 3 | [`01_operating_systems_deep_dive.md`](01_operating_systems_deep_dive.md) | Data structures (step 2: the scheduler is a tree, the page cache is a hash map) | Everything your program does runs on top of the OS's process/thread/memory model. |
| 4 | [`05_concurrency_deep_dive.md`](05_concurrency_deep_dive.md) | OS threads & processes (step 3) | Concurrency bugs only make sense once you know what a thread and a CPU core actually are. |
| 5 | [`02_networking_deep_dive.md`](02_networking_deep_dive.md) | OS I/O model (step 3 §4: sockets, epoll) | Networking is "the OS's I/O model, stretched across two machines." |
| 6 | [`03_databases_deep_dive.md`](03_databases_deep_dive.md) | Data structures (step 2: B+ trees, LSM trees), concurrency (step 4: MVCC is concurrency control) | Databases are data structures + concurrency control, made durable and distributed. |
| 7 | [`04_software_engineering_deep_dive.md`](04_software_engineering_deep_dive.md) | Databases & networking (steps 5–6: sagas coordinate services over the network; events are stored like a database's WAL) | The macro layer: how you architect *many* of the systems above working together. |
| 8 | [`08_python_for_coding_interviews_deep_dive.md`](08_python_for_coding_interviews_deep_dive.md) | Data structures (step 2) | Turns the theory into muscle memory: the exact standard-library tool for each structure. |
| 9 | [`09_coding_round_execution_deep_dive.md`](09_coding_round_execution_deep_dive.md) | Nothing technical — this is a skill, not a concept | How to *perform* what you know, live, in 45 minutes. |
| 10 | [`10_google_follow_ups_deep_dive.md`](10_google_follow_ups_deep_dive.md) | Everything above | The capstone: takes a solved problem and stretches it with the follow-ups a strong interviewer asks (streams, scale, concurrency, changed constraints). |

Each file's own **Foundations** section is self-contained, so you *can* jump straight
to file 5 without reading 1–4 first — but if a term feels unexplained, the step it
says "builds on" is where it was introduced.

### Track B — Interview fast track (numeric order)

If you're already comfortable with the basics and are running the structured
12-week plan in [`GOOGLE_INTERVIEW_PREP.md`](../GOOGLE_INTERVIEW_PREP.md), read the
files in their numbered order (01→10) alongside the weekly schedule there — that
file's table already maps each week to specific sections. Skim or skip each file's
Foundations section if it's already familiar; nothing later in the file depends on
you having read it.

---

## The ten files at a glance

| # | File | Foundations covers | The deep dive adds |
|---|---|---|---|
| 01 | [Operating Systems & Hardware](01_operating_systems_deep_dive.md) | What an OS/kernel/process/thread is, why a scheduler exists, RAM vs. cache in one picture | CFS/EEVDF scheduling, MESI cache coherence, false sharing, CAS/futexes, epoll vs. io_uring, virtual memory & NUMA |
| 02 | [Networking & Distributed Communication](02_networking_deep_dive.md) | Client/server, IP addresses & ports, what TCP and UDP each guarantee, HTTP request/response in one round trip | TCP handshake internals, CUBIC vs. BBR congestion control, HTTP/1.1→2→3, L4 vs. L7 load balancing, the full TLS 1.3 handshake |
| 03 | [Database Storage Engines](03_databases_deep_dive.md) | What a database/table/row is, why indexes speed up reads, what ACID means in one sentence each | B+ trees vs. LSM trees, MVCC, isolation levels and the anomalies they allow, replication, Paxos/Raft, Spanner's TrueTime |
| 04 | [Software Engineering & Architecture](04_software_engineering_deep_dive.md) | Monolith vs. microservices, synchronous calls vs. events, what an API contract is | Domain-Driven Design, event sourcing & CQRS, the outbox pattern, 2PC vs. Sagas, backward-compatible API evolution |
| 05 | [Concurrency](05_concurrency_deep_dive.md) | What a thread is, why two threads touching the same variable can corrupt it | Locks/condition variables/semaphores, the four deadlock conditions, a verified bounded blocking queue and Go worker pool, the GIL |
| 06 | [Data Structure Internals](06_data_structure_internals_deep_dive.md) | Array vs. linked list vs. hash map in one table, what "O(1) lookup" really means | How CPython/Go/Java implement hash maps, dynamic array growth, heaps, balanced trees, tries, graph representations |
| 07 | [Complexity Analysis](07_complexity_analysis_deep_dive.md) | What Big-O measures, a plain-language walk through one O(n) and one O(n²) example | Recursion trees, the master theorem, amortized analysis, reading input constraints to predict the intended algorithm |
| 08 | [Python for Coding Interviews](08_python_for_coding_interviews_deep_dive.md) | — (already a hands-on reference; read after 06–07) | Every built-in type's cost and traps, `collections`/`heapq`/`bisect`/`itertools`, Dijkstra/LRU/Trie written cold |
| 09 | [Running the 45-Minute Coding Round](09_coding_round_execution_deep_dive.md) | — (a skill guide: what "good" looks like before the timeline) | The minute-by-minute timeline, clarifying questions, edge-case checklist, recovering when stuck |
| 10 | [Google-Style Follow-Ups](10_google_follow_ups_deep_dive.md) | — (read this last — it assumes you can already solve the base problem) | Toolkits for streams, distributed scale, precomputation, concurrency, and changed constraints, applied to six worked problems |

---

## If you're completely new to this: start here

1. Read `07` then `06` end to end (Foundations *and* deep dive) — nothing else in
   this module makes sense without Big-O and a mental model of a hash map.
2. Pick **one** systems file next based on what you're curious about — `01` (how
   programs run), `02` (how the internet works), or `03` (how databases work). They
   don't depend on each other, only on `06`.
3. Read `05` once you've read `01` — concurrency without a model of threads and
   cores is memorizing vocabulary, not understanding it.
4. Read `04` last among the concept files — it's the one file that assumes you
   already believe distributed systems are hard (`02`, `03`) and shows how to design
   around that.
5. Only then move to `08`–`10` — they assume you're about to solve or have just
   solved a coding problem and want to talk about it well.

If you get stuck on vocabulary a Foundations section didn't define, it's almost
always covered in `07` (for complexity terms) or `06` (for data-structure terms) —
both are meant to be read first.

## Already prepping for interviews?

- The structured 12-week plan that schedules these files week by week:
  [`GOOGLE_INTERVIEW_PREP.md`](../GOOGLE_INTERVIEW_PREP.md).
- Every file ends with an **Interview checklist** — a fast self-test of what a strong
  answer covers. Use it as spaced-repetition material, not just a first-read tick box.
- `09` and `10` are interview *execution* skills, not new CS content — read them once
  you're comfortable with `01`–`07`, and re-read them the week before an onsite.

## Where the deeper material lives

This module stays intentionally tight (a few hundred lines per topic). For more
depth on any topic, each file's own "Related" line at the bottom points further, and
in general:

| Topic | Go deeper in |
|---|---|
| System design at scale (caching, sharding, real designs) | `SystemDesign/building_blocks/`, `SystemDesign/problems/` |
| Code-level design (testability, error handling, LLD interviews) | `SoftwareDesign/` |
| PostgreSQL and MongoDB/Redis hands-on, with runnable labs | `SQL/`, `NoSQL/` |
| Language-specific engineering depth | `PyEngineering/`, `GoEngineering/` |
| DSA problems to apply all of this to | `PyDSA/`, `GoDSA/`, `CURRICULUM.md` |

Related modules cross-reference specific sections of these files by number (e.g.
`CSFundamentals/03_databases_deep_dive.md` §3) — that's why section numbers inside
each file are stable and won't be renumbered even as content is added around them.
