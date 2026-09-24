# Software Design — Start Here

> "The most fundamental problem in computer science is problem decomposition: how to take
> a complex problem and divide it up into pieces that can be solved independently."
> — John Ousterhout

This track teaches how to design **code**: functions, classes, modules, services, and the
decisions around them. It is the half of an L5 interview loop that isn't algorithms or
distributed systems — the code-quality bar in every coding round, the low-level design
(LLD) round, the "how would you structure this?" follow-ups, and the design-leadership
stories in behavioural rounds.

It is laid out as **one path**: an optional primer, 14 chapters in five parts, then 17
LLD problems you solve in the editor and check with real tests. Work top to bottom.
Every chapter builds on the ones before it, and later chapters point back with short
references like `02` §7 (chapter 02, section 7).

**New to software design?** Start with `00_software_design_foundations.md` — it assumes
only that you can write a function and a loop, and builds the vocabulary (class,
encapsulation, coupling, interface, requirement) that chapter `01` onward takes for
granted, with the smallest possible examples in both Python and Go. **Already comfortable
with that vocabulary?** Skip it and start at `01` — nothing later repeats it.

---

## The path

| Step | Part | What you'll be able to do |
|---|---|---|
| **0** | **Part 0 · Before you start** *(optional)* | Know what a class, module, interface, and requirement actually are — the vocabulary the rest of the track assumes |
| **1–4** | **Part 1 · Foundations** | Spot complexity, model a domain with objects that protect their own rules, draw module boundaries, use patterns only where something actually varies |
| **5–7** | **Part 2 · Code that survives change** | Make code testable and refactor it safely; design failure handling, retries, and idempotency; write concurrent code that is correct by construction |
| **8–12** | **Part 3 · Services in production** | Arrange a service with ports and adapters; evolve data and schemas without downtime; make code observable, fast enough, and secure by default |
| **13–14** | **Part 4 · Leading design and the LLD interview** | Write and review design docs, turn disagreements into decisions; run a 45-minute LLD interview with a repeatable framework |
| **15–31** | **LLD practice** | Solve 17 classic LLD problems against real tests: warm-up → core set → breadth → Tier 2 |

### Part 0 · Before you start (optional)

| Step | Chapter | Read it for |
|---|---|---|
| 0 | `00_software_design_foundations.md` | What a class, function, and module actually are; abstraction vs. encapsulation; coupling and cohesion in plain terms; interfaces; functional vs. non-functional requirements — one small, fully-run Python and Go example per idea |

### Part 1 · Foundations

| Step | Chapter | Read it for |
|---|---|---|
| 1 | `01_philosophy_of_software_design.md` | What complexity is, deep modules, information hiding, errors defined out of existence, making illegal states unrepresentable — the vocabulary everything else uses |
| 2 | `02_oop_and_domain_modeling.md` | Invariants as the job of a class, composition over inheritance, entities vs. value objects, aggregates, modeling lifecycles, going from a problem statement to a model |
| 3 | `03_modularity_coupling_and_api_design.md` | Coupling and cohesion precisely, dependency direction, package design, signatures and error contracts that can't be misused, evolving APIs |
| 4 | `04_design_patterns_in_practice.md` | The patterns that matter, in idiomatic Python and Go — and how to recognise pattern overuse |

### Part 2 · Code that survives change

| Step | Chapter | Read it for |
|---|---|---|
| 5 | `05_testability_refactoring_and_legacy_code.md` | Seams, fakes over mocks, behaviour-focused tests, the refactoring catalogue, changing legacy code safely |
| 6 | `06_error_handling_and_failure_design.md` | A failure model, where to catch, timeouts and deadlines, retries with jitter, idempotency keys, compensation |
| 7 | `07_designing_concurrent_code.md` | Confine / freeze / guard / serialise, thread-safe class design, actors, async races, structured concurrency, single-flight |

### Part 3 · Services in production

| Step | Chapter | Read it for |
|---|---|---|
| 8 | `08_application_architecture_in_code.md` | Hexagonal / clean architecture as one rule, a complete runnable service, transactions, dependency injection, CQRS-lite |
| 9 | `09_data_design_and_schema_evolution.md` | Backward and forward compatibility, upcasters, zero-downtime migrations, money / time / IDs done right |
| 10 | `10_designing_observable_code.md` | Structured logs, metrics without cardinality explosions, tracing, liveness vs. readiness |
| 11 | `11_performance_aware_design.md` | Batch-shaped interfaces, streaming, cache pitfalls, tail latency, honest benchmarking |
| 12 | `12_secure_code_by_design.md` | Injection, authorization that's hard to forget, secrets and tokens, SSRF, resource limits |

### Part 4 · Leading design and the LLD interview

| Step | Chapter | Read it for |
|---|---|---|
| 13 | `13_design_docs_and_technical_leadership.md` | A complete example design doc, ADRs, reviewing, resolving disagreement, influence without authority |
| 14 | `14_low_level_design_interview_playbook.md` | The 45-minute LLD framework, what interviewers score, talk tracks, the question bank |

### LLD practice (in the editor)

Each problem opens in the workspace: the **brief** on the left, a stub with a **fixed API**
in the editor, and **Run** executes the real tests. Aim for 45 minutes, then compare with the
solution and write the one design point you missed in **Notes**.

| Steps | Set | Problems | Why this order |
|---|---|---|---|
| 15–17 | **Warm-up** | 008 Tic-tac-toe · 009 LRU/LFU cache · 003 Vending machine | Small; exercise invariants, data structures, and the State pattern |
| 18–22 | **Core set** | 001 Parking lot · 002 Elevator · 004 Movie booking · 005 Splitwise · 006 KV store with transactions | The most-asked LLD questions; each has a concurrency or consistency twist |
| 23–26 | **Breadth** | 007 Logging framework · 010 Unix `find` · 011 Meeting rooms · 012 Rate limiter | Different shapes: pipelines, composites, intervals, time |
| 27–31 | **Tier 2** | 013 Order book · 014 Task scheduler · 015 Library · 016 Food delivery lifecycle · 017 Text editor undo/redo | Longer, with harder follow-ups |

---

## How to use each chapter

1. **Read one chapter per session** (35–45 minutes). Tick **Got it** at the end of each
   section only when you could explain it to someone else.
2. **Run the examples.** Every complete example in chapters 06–12 was executed, and its
   real output is printed beneath it. Change something and see what breaks.
3. **Use the red-flags table in code review** — yours and other people's.
4. **Answer the interview questions out loud** before reading the model answers.
5. **Revisit the checklist** a week later. Anything you can't tick goes back on the list.

## If your interview is soon

| Time left | Do this |
|---|---|
| **1 week** | Step 14 (the LLD playbook), then steps 18–22 (core LLD set). Skim the red-flags tables in steps 1, 2, and 7 |
| **3 weeks** | Part 1, step 7, step 14, all LLD practice |
| **6+ weeks** | The whole path in order |

## Related tracks

| Track | Relationship |
|---|---|
| **System Design** | Same trade-off thinking at the scale of many machines. Do after Part 3 |
| **CS Fundamentals** | Primitives underneath: concurrency, databases, networking, complexity |
| **Go / Py Engineering** | Runnable production projects that apply Parts 2 and 3 |
| **Google Behavioral** | Where the stories from step 13 get told |
