# Google Interview Master Study Plan (L5 / Senior SWE)

This repository (`DSA-Practice`) is organized around the four attributes Google interviewers write feedback on:
1. **General cognitive ability** — how you break down unfamiliar problems (every round)
2. **Role-related knowledge** — coding, data structures & algorithms, system design
3. **Leadership** — ownership, influence without authority, mentoring, driving ambiguity
4. **Googleyness** — collaboration, humility, user focus, comfort with ambiguity

Start with `GoogleBehavioral/01_how_google_scores_and_googleyness.md` to understand how you're scored and why candidates get downleveled. The plan below is the **12-week plan** from `_archive/docs/google_prep_plan.md` (the original syllabus this file was mapped from — archived once every gap it named was closed, see `CONTEXT.md`), mapped to the exact files in this repo. (`master_dsa_plan.md` holds the 13-week DSA-only schedule, pattern table, and retention system; use it for the coding track's details.)

> Assumes about 2-3 hours on weekdays and 5-6 hours on weekend days. If you have less time, stretch to 16-20 weeks rather than skipping topics.

---

## Where everything lives

| Area | Files |
|---|---|
| **Foundations** | `CSFundamentals/08_python_for_coding_interviews_deep_dive.md` (stdlib cold, write without an IDE) · `CSFundamentals/07_complexity_analysis_deep_dive.md` (Big-O, recursion trees, master theorem, amortized, constraints → algorithm) |
| **Coding round execution** | `CSFundamentals/09_coding_round_execution_deep_dive.md` (45-min timeline, clarifying list, edge cases, hints, verification) · `CSFundamentals/10_google_follow_ups_deep_dive.md` (stream / out of memory / many queries / threads / changed constraints) |
| **DSA problems** | `CURRICULUM.md` (344 problems, 28 topics) · `PyDSA/<topic>/_TOPIC_GUIDE.md` + question/solution files · `./studio` web app · `REVIEW_LEDGER.md` (spaced repetition) |
| **CS fundamentals** | `CSFundamentals/01`–`06`: OS, networking (incl. "type google.com"), databases (isolation, indexes, replication, Spanner), software engineering (DDD, sagas, <abbr title="Application Programming Interface">API</abbr> evolution), concurrency, data structure internals |
| **System design** | `SystemDesign/00_google_l5_playbook.md` (start here) · `SystemDesign/building_blocks/` (01–25) · `SystemDesign/problems/` + `solutions/` (001–030) · `SYSTEM_DESIGN_GUIDE.md` · `SystemDesign/building_blocks/24_google_papers.md` |
| **Code quality & design** | `SoftwareDesign/01_philosophy_of_software_design.md` · `SoftwareDesign/13_design_docs_and_technical_leadership.md` · `SystemDesign/best_practices/` |
| **Language engineering depth** | `PyEngineering/` and `GoEngineering/` topics 1–35 |
| **Behavioral** | `GoogleBehavioral/01` scoring & Googleyness · `02` STAR blueprints · `03` L5 leadership · `04` story bank worksheet (13 story types) · `05` hypotheticals · `06` projects, resume, why Google |

---

## The 12-week plan

| Week | Coding (PyDSA topics + foundations) | System design and behavioral |
|---|---|---|
| **1** | Python stdlib (`CSFundamentals/08`), complexity (`07`), **01** Arrays & Hashing, **02** Two Pointers, **03** Sliding Window, **04** Prefix Sum | Read `GoogleBehavioral/01`. Start a mistakes log. Brainstorm candidate stories (`04` step 1). |
| **2** | **08** Linked List, **06** Stack & Monotonic Stack, **07** Queue & Deque, **05** Binary Search, **22** Sorting, **27** Classic Algorithms (quickselect, randomized) | Estimation and networking: `building_blocks/18`, `02`, `CSFundamentals/02` |
| **3** | **10** Binary Trees, **11** BST, **12** Heap, **13** Trie | APIs, load balancing, databases: `building_blocks/03`, `04`, `13`, `05`, `CSFundamentals/03` |
| **4** | **14** Graphs (traversal, bipartite, implicit graphs), **15** Advanced Graphs 001–002, 009, 013 (union-find, topo sort) | Storage engines, replication, partitioning: `building_blocks/06`, `19`, `25` |
| **5** | **15** Advanced Graphs rest (Dijkstra, 0-1 BFS, Bellman-Ford, MST, Tarjan), **09** Recursion & Backtracking, **28** Recursion Mastery (as needed) | Caching and messaging: `building_blocks/07`, `09`. **Write your first 5 stories** (`04` template). |
| **6** | **16** DP 1D, **17** DP 2D 001–015. **First coding mock.** | Consistency, consensus, resilience: `building_blocks/10`, `11`, `12`, `19`. `CSFundamentals/05` concurrency |
| **7** | **17** DP 2D 016–018 (bitmask BFS, digit DP), **18** Greedy, **19** Intervals | Stream processing, search & geo indexes, SRE: `building_blocks/20`, `21`, `15`. **Finish all stories** (coverage matrix). |
| **8** | **20** Bit Manipulation, **21** Math & Geometry, **26** Segment Tree & Fenwick, **25** Design, **23** String Algorithms, **24** Matrix | Design problems: 001 URL shortener, 002 rate limiter, 022 unique ID, 023 KV store, 009 autocomplete |
| **9** | Mixed Google-tagged sets; follow-ups drill (`CSFundamentals/10`). **Second coding mock.** | Design: 007 news feed, 006 chat, 004 notifications, 024 Google Docs, 015 Drive. **First design mock.** |
| **10** | Timed sessions: 2 problems in 45 minutes (`CSFundamentals/09`) | Design: 016 YouTube, 025 web search, 026 Maps/nearby, 012 job scheduler, 027 ad click aggregation, 028 top-K, 029 leaderboard, 030 <abbr title="Large Language Model">LLM</abbr> assistant. **Behavioral mock** (`05` hypotheticals). |
| **11** | Full mock loops (4 rounds in one day), then fix the weakest area | Read the Google papers (`building_blocks/24`). Rehearse project deep dives and resume (`GoogleBehavioral/06`). |
| **12** | Redo failed problems from your log. Light practice only. | Rest, logistics, review notes. Don't cram. |

**Daily habits**
- Give each problem 25–30 minutes before looking at a solution. If you look, re-solve it from scratch the next day.
- Log every problem you couldn't solve with the missing insight in one sentence; redo after 3, 7, and 21 days (`REVIEW_LEDGER.md`).
- After each problem, sketch answers to the five follow-ups (`CSFundamentals/10`).
- Depth over count: 250–350 well-understood problems beat 800 memorized ones.
- Before each session, name which attribute you're producing evidence for.

---

## How to use the repository during the loop

1. **Coding rounds:** run the timeline in `CSFundamentals/09`: clarify → example → brute force → optimize and state complexity → agree → code with helpers → trace and test → follow-ups. Write production-quality Python, not competitive-programming code.
2. **System design rounds:** drive the 45 minutes as in `SystemDesign/00_google_l5_playbook.md`: requirements → estimates and <abbr title="Application Programming Interface">API</abbr> → data model → high-level design → two real deep dives → failures and evolution. Quantify, state trade-offs, and commit to decisions.
3. **Fundamentals questions** ("how does a hash map work?", "what happens when you type google.com?"): `CSFundamentals/06` and `CSFundamentals/02` §0.
4. **Googleyness & Leadership:** STAR + lesson, 2–3 minutes, "I" for your actions, numbers in the result, stories drawn from your coverage matrix (`GoogleBehavioral/04`); frameworks for hypotheticals in `05`.

---

## You're ready when you can tick all of these

**Coding**
- [ ] I solve unseen medium problems in 25 minutes or less, 8 times out of 10, bug-free after my own testing.
- [ ] I solve unseen hard problems in about 40 minutes at least half the time, and reach a solid approach on the rest.
- [ ] I can write Dijkstra, union-find, topological sort, a trie, binary search, quickselect, an LRU cache, and a Fenwick tree from memory.
- [ ] My last 3 coding mocks, with strangers, came back as hire or strong hire.

**System design**
- [ ] I can design at least 15 of the listed systems in 45 minutes, with 2 real deep dives each.
- [ ] I've done at least 3 design mocks with experienced engineers, and the latest feedback was at the senior level.
- [ ] I can explain every trade-off I make and name at least one alternative.

**Behavioral and experience**
- [ ] I have 10 or more stories written out and rehearsed aloud, each under 3 minutes.
- [ ] I can map any common behavioral question to a story within 10 seconds.
- [ ] I can defend every project on my resume with numbers and trade-offs.

---

## External resources (use a few deeply)

- **Coding practice:** LeetCode (Google-tagged problems with premium); NeetCode roadmap for pattern-organized lists.
- **Algorithm references:** cp-algorithms.com.
- **Fundamentals book:** *Cracking the Coding Interview* (Gayle Laakmann McDowell).
- **System design books:** *Designing Data-Intensive Applications* (Martin Kleppmann) — the most important one; *System Design Interview* vols 1–2 (Alex Xu).
- **Reliability:** Google's SRE books, free online.
- **Mock interviews:** interviewing.io, peers who are also preparing.
- **Google papers:** GFS, MapReduce, Bigtable, Chubby, Spanner, Dremel, Borg, Zanzibar (plus Amazon's Dynamo and the Dataflow model) — summaries in `SystemDesign/building_blocks/24_google_papers.md`.
