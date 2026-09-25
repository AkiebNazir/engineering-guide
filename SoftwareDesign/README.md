# Software Design — Start Here

> "The most fundamental problem in computer science is problem decomposition: how to take
> a complex problem and divide it up into pieces that can be solved independently."
> — John Ousterhout

This track teaches how to design **code**: functions, classes, modules, services, and the
decisions around them. It is the half of an L5 interview loop that isn't algorithms or
distributed systems — the code-quality bar in every coding round, the low-level design
(LLD) round, the "how would you structure this?" follow-ups, and the design-leadership
stories in behavioural rounds.

It is laid out as **one path**: an optional primer, 15 chapters in six parts, then 20
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
| **1** | **Part 0 · Before you start** *(optional)* | Know what a class, module, interface, and requirement actually are — the vocabulary the rest of the track assumes |
| **2–5** | **Part 1 · Foundations** | Spot complexity, model a domain with objects that protect their own rules, draw module boundaries, use patterns only where something actually varies |
| **6–8** | **Part 2 · Code that survives change** | Make code testable and refactor it safely; design failure handling, retries, and idempotency; write concurrent code that is correct by construction |
| **9–13** | **Part 3 · Services in production** | Arrange a service with ports and adapters; evolve data and schemas without downtime; make code observable, fast enough, and secure by default |
| **14–15** | **Part 4 · Leading design and the LLD interview** | Write and review design docs, turn disagreements into decisions; run a 45-minute LLD interview with a repeatable framework |
| **16** | **Part 5 · Extended toolkit and field reference** *(optional)* | Name-drop GRASP and the C4 model correctly; find any term from `01`–`14` in seconds using the topic index |
| **17–36** | **LLD practice** | Solve 20 classic LLD problems against real tests: warm-up → core set → breadth → Tier 2 → Tier 2 extended |

(Step numbers match what the workspace shows for each item — the README page itself is
implicitly step 0.)

### Part 0 · Before you start (optional)

| Step | Chapter | Read it for |
|---|---|---|
| 1 | `00_software_design_foundations.md` | What a class, function, and module actually are; abstraction vs. encapsulation; coupling and cohesion in plain terms; interfaces; functional vs. non-functional requirements — one small, fully-run Python and Go example per idea |

### Part 1 · Foundations

| Step | Chapter | Read it for |
|---|---|---|
| 2 | `01_philosophy_of_software_design.md` | What complexity is, deep modules, information hiding, errors defined out of existence, making illegal states unrepresentable — the vocabulary everything else uses |
| 3 | `02_oop_and_domain_modeling.md` | Invariants as the job of a class, composition over inheritance, entities vs. value objects, aggregates, modeling lifecycles, going from a problem statement to a model |
| 4 | `03_modularity_coupling_and_api_design.md` | Coupling and cohesion precisely, dependency direction, package design, signatures and error contracts that can't be misused, evolving APIs |
| 5 | `04_design_patterns_in_practice.md` | The patterns that matter, in idiomatic Python and Go — and how to recognise pattern overuse |

### Part 2 · Code that survives change

| Step | Chapter | Read it for |
|---|---|---|
| 6 | `05_testability_refactoring_and_legacy_code.md` | Seams, fakes over mocks, behaviour-focused tests, the refactoring catalogue, changing legacy code safely |
| 7 | `06_error_handling_and_failure_design.md` | A failure model, where to catch, timeouts and deadlines, retries with jitter, idempotency keys, compensation |
| 8 | `07_designing_concurrent_code.md` | Confine / freeze / guard / serialise, thread-safe class design, actors, async races, structured concurrency, single-flight |

### Part 3 · Services in production

| Step | Chapter | Read it for |
|---|---|---|
| 9 | `08_application_architecture_in_code.md` | Hexagonal / clean architecture as one rule, a complete runnable service, transactions, dependency injection, CQRS-lite |
| 10 | `09_data_design_and_schema_evolution.md` | Backward and forward compatibility, upcasters, zero-downtime migrations, money / time / IDs done right |
| 11 | `10_designing_observable_code.md` | Structured logs, metrics without cardinality explosions, tracing, liveness vs. readiness |
| 12 | `11_performance_aware_design.md` | Batch-shaped interfaces, streaming, cache pitfalls, tail latency, honest benchmarking |
| 13 | `12_secure_code_by_design.md` | Injection, authorization that's hard to forget, secrets and tokens, SSRF, resource limits |

### Part 4 · Leading design and the LLD interview

| Step | Chapter | Read it for |
|---|---|---|
| 14 | `13_design_docs_and_technical_leadership.md` | A complete example design doc, ADRs, reviewing, resolving disagreement, influence without authority |
| 15 | `14_low_level_design_interview_playbook.md` | The 45-minute LLD framework, what interviewers score, talk tracks, the question bank |

### Part 5 · Extended toolkit and field reference (optional)

| Step | Chapter | Read it for |
|---|---|---|
| 16 | `15_extended_principles_and_field_reference.md` | GRASP's four names <abbr title="Five core design principles intended to make software designs more understandable, flexible, and maintainable (Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion).">SOLID</abbr> doesn't cover (Creator, Information Expert, Pure Fabrication, Controller), the C4 model for drawing architecture at the right zoom level, and a topic index across every chapter |

### LLD practice (in the editor)

Each problem opens in the workspace: the **brief** on the left, a stub with a **fixed <abbr title="Application Programming Interface">API</abbr>**
in the editor, and **Run** executes the real tests. Aim for 45 minutes, then compare with the
solution and write the one design point you missed in **Notes**.

| Steps | Set | Problems | Why this order |
|---|---|---|---|
| 17–19 | **Warm-up** | 008 Tic-tac-toe · 009 <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr>/<abbr title="Least Frequently Used. A cache replacement policy that discards the least frequently used items first.">LFU</abbr> cache · 003 Vending machine | Small; exercise invariants, data structures, and the State pattern |
| 20–24 | **Core set** | 001 Parking lot · 002 Elevator · 004 Movie booking · 005 Splitwise · 006 KV store with transactions | The most-asked LLD questions; each has a concurrency or consistency twist |
| 25–28 | **Breadth** | 007 Logging framework · 010 Unix `find` · 011 Meeting rooms · 012 Rate limiter | Different shapes: pipelines, composites, intervals, time |
| 29–33 | **Tier 2** | 013 Order book · 014 Task scheduler · 015 Library · 016 Food delivery lifecycle · 017 Text editor undo/redo | Longer, with harder follow-ups |
| 34–36 | **Tier 2 extended** | 018 ATM · 019 Chess · 020 Notification service | Compensation across two systems; the deepest polymorphism exercise in the set; a full-circle callback to `00`/`04`'s Observer and `06`'s retries |

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
| **1 week** | Step 15 (the LLD playbook), then steps 20–24 (core LLD set). Skim the red-flags tables in steps 2, 3, and 8 |
| **3 weeks** | Part 1, step 8, step 15, all LLD practice |
| **6+ weeks** | The whole path in order |

## Related tracks

| Track | Relationship |
|---|---|
| **System Design** | Same trade-off thinking at the scale of many machines. Do after Part 3 |
| **CS Fundamentals** | Primitives underneath: concurrency, databases, networking, complexity |
| **Go / Py Engineering** | Runnable production projects that apply Parts 2 and 3 |
| **Google Behavioral** | Where the stories from step 14 get told |
