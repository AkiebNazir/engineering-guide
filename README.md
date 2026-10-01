# Start Here

This repository is a complete, offline study library for software-engineering interviews
at the senior (L5) level and around it. Three modules are the core, and everything else is
elective:

| Core module | What it gives you | Where it starts |
|---|---|---|
| **DSA** (data structures and algorithms) | 353 problems in 28 pattern topics, each with a question file you solve, a tested reference solution, a topic guide and a step-by-step visualizer | [Curriculum Index](CURRICULUM.md), then `PyDSA/<topic>/_TOPIC_GUIDE.md` |
| **CS Fundamentals** | 15 chapters from complexity to distributed systems, with runnable measurements, live labs and a 62-question bank | [CS Fundamentals — Start Here](CSFundamentals/README.md) |
| **System Design** | 33 building blocks, 41 practice problems with reference designs, spoken walkthroughs and a 42-question bank | [System Design Mastery Curriculum](SystemDesign/README.md) |

One **supporting module** feeds all three: **Maths for CS Engineers**
([Maths for CS Engineers — Start Here](Maths/README.md)), 15 chapters from reading notation to probability and
complexity theory, with 45 labs and machine-checked code. Section 2 schedules each chapter next
to the work that uses it.

This page tells you **what to study in which order**, how to spend a day, when you're ready
to move on, and how to set the library up so it works with no internet at all.

---

## 1. The order, on one screen

```text
Phase 0   Setup and orientation ............................ 2-3 days
Phase 1   Coding foundations + DSA linear patterns ......... weeks 1-6
          + CS Part 1 (measuring cost), Python and the coding round
Phase 2   DSA trees, graphs, recursion ...................... weeks 7-12
          + CS Part 2 (one machine), then CS Part 3 (many machines)
Phase 3   DSA dynamic programming and the rest ............. weeks 13-17
          + System Design building blocks and first problems
Phase 4   Performance: timed problems, mocks, behavioral ... weeks 18-20
          + CS Parts 4-5, System Design problems at 45 minutes, both question banks
```

The logic behind the order:

- **DSA is the daily spine** from day one to the end, because coding rounds are the most
  numerous and skill decays fastest without practice.
- **CS Fundamentals runs beside it**, one part at a time. Each part only depends on the one
  before, and Part 3 (networking, databases, distributed systems) is exactly the foundation
  System Design assumes.
- **System Design starts once the DSA core is done and CS Part 3 is read**, so every building
  block lands on concepts you already own.
- **Phase 4 turns knowledge into performance**: timing, speaking out loud, follow-ups, stories.

The pace assumes about 2–3 hours on weekdays and 5–6 on weekend days (about 20 hours a
week). With less time, stretch the phases; don't skip them. With a fixed date sooner than
20 weeks away, use the compressed plan in section 5.

---

## 2. Phase by phase

### Phase 0 · Setup and orientation (2–3 days)

1. Do the offline setup in section 6 while you still have internet.
2. Start the app (`make app`, then open http://127.0.0.1:8080) and click around: the DSA
   dashboard, one problem, one topic guide, one CS chapter.
3. Read [How Google Scores You](GoogleBehavioral/01_how_google_scores_and_googleyness.md):
   how every round is scored. It changes how you practise everything else.
4. If maths feels rusty, read [Maths 01 Reading maths like code](Maths/01_reading_maths_like_code.md)
   now; every later chapter assumes you can read Σ, logs and exponents as code.
5. Read §0 of [MAANG/FAANG DSA Master Plan](master_dsa_plan.md), especially the status legend and the hint
   ladder: the solved-versus-mastered distinction, and the 25/40-minute rule the app's timer
   follows.

### Phase 1 · Coding foundations and linear patterns (weeks 1–6)

| Week | DSA topics (problems) | Reading alongside |
|---|---|---|
| 1 | 01 Arrays & Hashing (14), 02 Two Pointers (11) | CS [08 Python for interviews](CSFundamentals/08_python_for_coding_interviews_deep_dive.md), CS [07 Complexity](CSFundamentals/07_complexity_analysis_deep_dive.md) |
| 2 | 03 Sliding Window (15), 04 Prefix Sum (8) | CS [09 The 45-minute coding round](CSFundamentals/09_coding_round_execution_deep_dive.md): use its timeline from now on; Maths [06 Sums and recurrences](Maths/06_sequences_sums_recurrences.md) |
| 3 | 05 Binary Search (12), 22 Sorting Algorithms (8) | CS [06 Data structure internals](CSFundamentals/06_data_structure_internals_deep_dive.md), first half; Maths [03 Logic and proofs](Maths/03_logic_and_proofs.md) (loop invariants) |
| 4 | 06 Stack (16), 07 Queue & Deque (6) | CS 06, second half |
| 5 | 08 Linked List (15) | Start your story list: [Your Story Bank](GoogleBehavioral/04_story_bank_worksheet.md), step 1 |
| 6 | 27 Classic Algorithms (9), then redo every problem you logged as missed | Catch-up week for CS Part 1; Maths [05 Counting](Maths/05_counting_and_combinatorics.md) before backtracking and DP |

**Ready to move on when:** you can solve an unseen Medium from topics 01–08 in about 25
minutes while talking, state its complexity without hesitating, and tick the interview
checklists at the end of CS 07 and CS 06.

### Phase 2 · Trees, graphs, recursion (weeks 7–12)

| Week | DSA topics (problems) | Reading alongside |
|---|---|---|
| 7 | 10 Trees (21) | CS [13 Computer architecture](CSFundamentals/13_computer_architecture_deep_dive.md) (Maths [02 Number systems](Maths/02_number_systems_and_binary.md) covers the same ground more gently) |
| 8 | 11 Binary Search Tree (11), 13 Trie (7) | CS [01 Operating systems](CSFundamentals/01_operating_systems_deep_dive.md) |
| 9 | 12 Heap / Priority Queue (12), 09 Recursion & Backtracking (14) | CS [14 Memory management](CSFundamentals/14_memory_management_deep_dive.md), CS [05 Concurrency](CSFundamentals/05_concurrency_deep_dive.md) |
| 10 | 14 Graphs (19) | CS [02 Networking](CSFundamentals/02_networking_deep_dive.md); Maths [08 Graph theory](Maths/08_graph_theory.md) |
| 11 | 15 Advanced Graphs (15) | CS [03 Databases](CSFundamentals/03_databases_deep_dive.md) |
| 12 | 28 Recursion Mastery (25): the ones you find hard, not all | CS [15 Distributed systems](CSFundamentals/15_distributed_systems_deep_dive.md). First timed mock: two problems in 45 minutes |

**Ready to move on when:** graph and tree problems feel like choosing a traversal, not
inventing one; you can answer the L4–L5 questions in sections 2–5 and 9–11 of the
[CS question bank](CSFundamentals/12_interview_question_bank_deep_dive.md) out loud; and
you have a first draft of five behavioral stories.

### Phase 3 · Dynamic programming, the rest of DSA, and System Design (weeks 13–17)

| Week | DSA topics (problems) | System Design |
|---|---|---|
| 13 | 16 DP 1D (17) | [Google L5 System Design Playbook](SystemDesign/00_google_l5_playbook.md), then building blocks `00`–`04` |
| 14 | 17 DP 2D (22) | Building blocks `05`–`09` |
| 15 | 18 Greedy (10), 19 Intervals (11) | Building blocks `10`–`13` and `18` (estimation); Maths [10 Probability](Maths/10_probability.md) |
| 16 | 20 Bit Manipulation (10), 21 Math & Geometry (10), 23 String Algorithms (8) | Building blocks `14`–`17`; first problems `001`–`004`, untimed; Maths [07 Number theory](Maths/07_number_theory.md) with topic 21 |
| 17 | 24 Matrix (8), 25 Design (13), 26 Segment Tree & Fenwick (6) | Building blocks `19`–`25`; problems `005`–`010`; Maths [11 Statistics](Maths/11_statistics.md) (percentiles, A/B tests) |

Work each System Design problem the way [System Design Mastery Curriculum](SystemDesign/README.md)
describes: the question file first, your own design, then the solution, then its follow-ups
out loud.

**Ready to move on when:** you can open any building block's interview checklist and tick
most of it, and your problem designs start with numbers and end with failure modes without
prompting.

### Phase 4 · Performance (weeks 18–20)

| Week | Coding | System Design and the rest |
|---|---|---|
| 18 | Mixed sets from all topics, timed; the follow-up drills in CS [10 Google-style follow-ups](CSFundamentals/10_google_follow_ups_deep_dive.md) | Building blocks `26`–`32` as your level needs; problems `011`–`020` at 45 minutes; CS [04 Software engineering](CSFundamentals/04_software_engineering_deep_dive.md) and [11 Security](CSFundamentals/11_security_fundamentals_deep_dive.md) |
| 19 | Full mock loops: 2 coding + 1 design + 1 behavioral in one day | Problems `021`–`030` (L6 targets: `031`–`041`); the [SD question bank](SystemDesign/07_interview_question_bank.md); one [spoken walkthrough](SystemDesign/06_spoken_walkthroughs.md) aloud against a timer |
| 20 | Redo everything in your missed log; light practice only in the last days | Behavioral `02`, `03`, `05`–`08`; finish the story bank; Maths [15 Interview maths toolkit](Maths/15_interview_maths_toolkit.md) and its question bank; rest before the loop |

The Maths chapters not scheduled above are electives: [04 Sets, relations and functions](Maths/04_sets_relations_functions.md)
for precision in general, [09 Linear algebra](Maths/09_linear_algebra.md) and [12 Calculus](Maths/12_calculus.md)
for ML roles, and [13 Information theory](Maths/13_information_theory_and_coding.md) and
[14 Automata and complexity](Maths/14_automata_computability_complexity.md) for "is this NP-hard?"
questions and staff-level depth.

If your loop includes a low-level (object-oriented) design round, add the
[Software Design module](SoftwareDesign/README.md) in Phase 4, starting with
[Low-Level Design (LLD) Interview Playbook](SoftwareDesign/14_low_level_design_interview_playbook.md)
and its `lld/` problems.

---

## 3. A day of study

| Block | Weekday (2–3 h) | Weekend day (5–6 h) |
|---|---|---|
| Review queue | 15 min: the app's **Review queue** (cold re-solves at 1, 3, 10 and 30 days) | 30 min |
| New problems | 60–90 min: 2–3 problems, 25 minutes each before the first hint, 40 before the solution (the app's timer warns you) | 2–3 h, including one timed pair at 45 minutes |
| Reading | 45–60 min: one section of the current CS chapter or building block; run its demos and labs | 1–2 h, plus the chapter's checklist |
| Log | 5 min: every miss gets one sentence, "the insight I needed was …", in the problem's Notes tab | Redo last week's misses |

Rules that make the hours count:

- **Say it out loud.** Interviews are spoken; practise explaining while you code and design.
- **Solved isn't mastered.** A problem counts only when you can solve it cold, first run, in
  about 20 minutes, while narrating (`[★]` in [MAANG/FAANG DSA Master Plan](master_dsa_plan.md)).
- **Run the demos.** The CS and System Design chapters contain programs with their real
  output. Change a parameter and predict the result before running it.
- **Depth over count.** 250 problems you understand beat 500 you've seen.

---

## 4. Level targets

| Target level | DSA | CS Fundamentals | System Design |
|---|---|---|---|
| **L3–L4** (junior to mid) | Topics 01–19, Mediums in 25 minutes | Foundations sections and the Mid-Level column of each chapter's level table | Building blocks `00`–`13`, problems `001`–`010` |
| **L5** (senior) | All 28 topics, Mediums in 20 minutes and Hards attempted | Every numbered section; the Senior column of the level tables | Building blocks `00`–`20`, problems `001`–`030` at 45 minutes, every lab |
| **L6+** (staff) | As L5 | As L5, plus the Staff column's judgment | All 33 blocks (`21`–`32` add staff depth), problems `031`–`041`, each solution's "Going from L5 to L6" |

Every CS chapter and every deepened building block ends with a **What each level should
know** table and an **interview checklist**; use them as the exit test for that chapter.

---

## 5. Compressed plan (about 10 weeks)

[MAANG/FAANG DSA Master Plan](master_dsa_plan.md) names **Monday 7 December 2026** as a target. If that date still holds,
run the same order with less breadth:

| Weeks | DSA | CS Fundamentals | System Design and behavioral |
|---|---|---|---|
| 1–2 | 01, 02, 03, 05, 06 | 07, 08, 09 | Behavioral 01, start the story bank |
| 3–4 | 08, 10, 11, 12 | 06, 05 | — |
| 5–6 | 14, 15 (Dijkstra, union-find, topological sort), 09 | 02, 03 | Playbook, building blocks `00`–`05` |
| 7–8 | 16, 17 (first half), 18, 19 | 15 (sections 1–8); Maths 06 and 10 | Building blocks `07`, `09`, `12`, `13`, `18`, `25`; problems `001`, `002`, `004`, `006`, `007` |
| 9 | Mixed timed sets, redo misses | 10, 12 (question bank) | SD question bank; two mocks; behavioral 02, 05, 08; Maths 15 |
| 10 | Light review only | — | Rest |

Skip for now (and come back later): topics 04, 07, 13, 20–28 beyond what you meet in mixed
sets; CS 13, 14, 01, 04, 11; building blocks beyond the list above.

---

## 6. Going offline: setup and what was checked

### Do this before you disconnect

1. **Get the latest version** of this repository (merge or check out the branch with the
   newest work) onto the machine you'll use.
2. **Install the toolchains:** Python 3.12 or newer (3.11 runs everything except
   PyEngineering's 3.12 features), Go 1.21 or newer, a C compiler (`gcc` or `clang`, for a
   few CS Fundamentals demos) and `git`. Optional: `strace` on Linux for CS 01.
3. **Start the app once** (`make app`) and open a DSA problem, a CS chapter and a page
   with math, to confirm it works on your machine.
4. **Only if you'll use the elective tracks**, install their packages while you're online:

   | Track | Command, from the repo root |
   |---|---|
   | PyEngineering | `python3 -m venv PyEngineering/.venv && PyEngineering/.venv/bin/pip install -r PyEngineering/requirements.txt` |
   | API | `python3 -m venv API/.venv && API/.venv/bin/pip install -r API/requirements.txt`, then `cd API && go mod download` |
   | GoEngineering | `cd GoEngineering && go mod download` |
   | SQL and NoSQL | `pip install -r SQL/requirements.txt -r NoSQL/requirements.txt`, and `docker compose -f docker-compose.databases.yml pull` (PostgreSQL 16, MongoDB 7, Redis 7) |
   | AI Roadmap practice | `pip install -r AI-road-map/practice-guide/requirements.txt` |
   | Agentic AI projects | each project's `requirements.txt`, plus the Ollama models they name (large downloads) |

5. **Turn the network off and start the app again.** Everything in the core modules should
   still work.
6. **Back up your progress** now and then: it all lives in `webapp/data/progress.json`
   (drafts, solved status, notes, timers, review schedule).

### What was verified for offline use (30 September 2026)

- The web app loads **no external resources**. The markdown renderer, code editor, syntax
  highlighter, math typesetting, diagram library and all fonts are served from
  `webapp/static/vendor/`. Pages were loaded in a browser with every non-local request
  blocked: DSA problems, the visualizer, topic guides, CS chapters, System Design blocks and
  math-heavy AI Roadmap pages all rendered with zero errors.
- All **353 Python DSA solutions** pass their tests; all **49 Go solutions written so far**
  pass (the other Go files are the planned second pass, marked "not implemented yet").
- All **353 visualizers** play end to end, all **546 architecture diagrams** pass the layout
  checker, and every Python file outside `_archive/` parses under Python 3.12 without
  warnings.
- The **Maths module's** 16 pages render offline with all 1,033 formulas and 0 errors, and its
  own checker runs 148 code blocks and confirms all 295 printed claims.
- **No broken links** between the learning materials (1,892 relative links checked).
- The core modules (DSA, CS Fundamentals, System Design) need only Python's standard
  library, Go's standard library and a C compiler.

What won't work offline: the external links inside chapters (LeetCode pages, papers, vendor
documentation). Nothing in the core path depends on them; every problem carries its own
statement and tests.

---

## 7. Everything else in the library

Use these when a phase calls for them or your target role needs them:

| Module | When to use it |
|---|---|
| [`GoogleBehavioral/`](GoogleBehavioral) | Phases 0, 1 (story list) and 4 (all eight guides) |
| [`SoftwareDesign/`](SoftwareDesign/README.md) | Low-level design rounds; code-quality depth |
| [`SQL/`](SQL/README.md) and [`NoSQL/`](NoSQL/README.md) | Hands-on PostgreSQL, MongoDB and Redis; pairs with CS 03 and building block 05 |
| [`API/`](API) | REST, GraphQL, gRPC, WebSockets, webhooks in depth; pairs with building blocks 03–04 |
| `PyEngineering/`, `GoEngineering/`, `PyStdLib/`, `GoStdLib/` | Production-style language skills for backend roles |
| `TestingAndQuality/`, `CICD/`, `DataEngineering/`, `MLOps/`, `Tool-Kit/` | Role-specific depth |
| `AI-road-map/`, `AI-Libraries-Guides/`, `Agentic-AI/` | ML and AI engineering roles |

Two older planning documents remain for reference: [Google Interview Master Study Plan (L5 / Senior SWE)](GOOGLE_INTERVIEW_PREP.md)
(a 12-week plan that maps Google's four scoring attributes to files) and
[MAANG/FAANG DSA Master Plan](master_dsa_plan.md) (the DSA schedule, pattern table and retention
system). Where they disagree with this page about order, follow this page.
