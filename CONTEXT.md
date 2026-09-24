# CONTEXT.md — Session Handoff

**Read this first.** Everything a fresh session needs to continue with zero prior context.
Last updated: 16 Sep 2026.

---

## 1 · The goal

MAANG/FAANG interview prep. Building a **complete 288-problem DSA curriculum in Python
and Go**, plus a local web app to work through it.

| | |
|---|---|
| Target date | **Mon 7 Dec 2026** (13 weeks from 7 Sep) |
| Commitment | 25+ hrs/week, ~325 hours total |
| Scope | DSA + system design + behavioral (full loop) |
| Languages | Both Python and Go. Python is the interview language. |
| User level | Solid on recursion/backtracking. Gaps: binary search, graphs, DP, heaps, intervals. |
| User's code | Clean and idiomatic. Already handles the copy-on-append trap correctly. |

---

## 2 · Repo map

```
CONTEXT.md            ← this file
master_dsa_plan.md    13-week schedule, pattern-recognition table, interview script,
                      system design + behavioral tracks, retention system  (609 lines)
REVIEW_LEDGER.md      D+1/D+3/D+10/D+30 spaced-repetition tracker           (123 lines)
CURRICULUM.md         GENERATED index of all 288 problems. Do not hand-edit. (550 lines)
Makefile              `make app` starts the webapp (DSA_PORT, default 8420); the old ./studio script is gone
_archive/             superseded one-off scripts + docs, kept for history (see _archive/README.md)

tools/
  problems.tsv        ← SINGLE SOURCE OF TRUTH: 288 problems (289 lines w/ header)
  gen_curriculum.py   reads the TSV → writes CURRICULUM.md, auto-detects progress

PyDSA/<topic>/        28 topic folders, e.g. 01_arrays_hashing
  _TOPIC_GUIDE.md     deep language-internals guide for that topic
  NNN_slug_question.py
  NNN_slug_solution.py

GoDSA/<topic>/        same 28 topics; every one has a `_TOPIC_GUIDE.md` (24 Sep 2026). Topic 27's problem 009 has no Go folder yet.
  _TOPIC_GUIDE.md
  NNN_slug/
    question.go
    solution.go

webapp/               local web app (see §8)
  server.py  static/{index.html,styles.css,app.js}  data/progress.json

API/<Type>/            REST/GraphQL/Protobuf/gRPC/WebSockets/Webhooks/SOAP — Theory.md,
                      Foundation/ 00-13 ladder (py+go), labs/ (5 py + 5 go), see API/README.md
SQL/                  PostgreSQL module — README.md + 00-15 numbered level ladder (read-only
                      markdown, code blocks actually run against docker-compose.databases.yml)
NoSQL/                MongoDB + Redis module — README.md + mongodb/00-11 + redis/00-11
                      (same read-only ladder shape as SQL/, one shared docker-compose file)
```

**Legacy (pre-curriculum, leave in place, do not migrate):**
`PyDSA/{link_list,double_link_list,reverse_linked_list}.py`, `PyDSA/recursion/*`,
`GoDSA/{linklist,reverse_linked_list,recursion}/*`

**3 unsolved user stubs still open** (user's own homework, do NOT solve unprompted):
`PyDSA/recursion/combination_sum.py` · `GoDSA/recursion/permutations/permutations.go` ·
`GoDSA/reverse_linked_list/reverse_linked_list.go`

---

## 3 · Workflow agreement

1. **I create the problem file** (question + solution), with the problem statement,
   constraints, and visuals as comments at the top.
2. **User attempts it.**
3. **I review**: complexity feedback, optimal approach, step-by-step comments in their file.

Hint ladder baked into the material: **25 min** → one hint · **40 min** → full solution
+ auto-queued cold re-solve.

Status marks used across all docs: `[ ]` todo · `[/]` in progress · `[x]` solved ·
`[★]` mastered (cold, ≤20 min, narrated). **Only `[★]` counts as interview-ready.**

---

## 4 · File conventions — EXACT

### Python
```
PyDSA/<topic>/NNN_<snake_slug>_question.py
PyDSA/<topic>/NNN_<snake_slug>_solution.py
```
- `NNN` = zero-padded seq from the TSV. `<snake_slug>` = TSV slug with `-` → `_`.
- Module **docstring** holds all prose; code follows. The web app splits on this.
- `class Solution:` with the LeetCode method name.
- Question file: body is `# YOUR CODE HERE` + `pass`.
- Every file ends with `run_tests()` + `if __name__ == "__main__":`.
- **Solution files MUST print `ALL PASSED`** — verification greps for it.

### Go
```
GoDSA/<topic>/NNN_<snake_slug>/question.go
GoDSA/<topic>/NNN_<snake_slug>/solution.go
```
- **Exactly two files.** Both `package main`. This compiles because:
  - `question.go` has NO `main()`; it declares `func YourXxx(...)` — an unused function,
    which Go permits.
  - `solution.go` has the real solution funcs + the single `func main()`.
  - A third file breaks the convention (already made and reverted this mistake once).
- Prose lives in one `/* ... */` block; the app extracts it.
- Each dir is its own package, so a `status(ok bool) string` helper is **duplicated per
  problem on purpose** — that is correct, not redundancy to clean up.
- Digit-leading directory names work fine: `go run ./01_arrays_hashing/004_two_sum`.
- **Solution files MUST print `ALL PASSED`.**

---

## 5 · The quality bar (this is what makes the material good)

Every solution file contains, in order:

1. **THE CORE IDEA** — the one insight, stated plainly
2. **Multiple approaches**, brute force first (state it, price it, don't code it), then
   the real answer, then the space/time variants
3. **STEP BY STEP trace** with actual values, ASCII-drawn
4. **Complexity summary table** with a "mutates input?" column
5. **Edge cases** with the reason each one exists
6. **Common mistakes** — numbered, specific
7. **Follow-ups the interviewer may ask**
8. **Related problems** — the pattern family

**The distinguishing feature: the tests PROVE the lesson at runtime.** Not assertions in
prose — executable demonstrations. Established examples:

| File | What it demonstrates live |
|---|---|
| 001 Go | `append(nums, nums...)` aliasing actually corrupting the caller's slice |
| 002 both | O(n) vs O(n²) benchmark: 388x → 1668x slower as n doubles |
| 003 Go | `[26]int` vs `map[rune]int`: **146ms vs 3044ms** over 200k runs; real IndexError on `"école"` |
| 004 both | Insert-before-check returning `[0,0]`; Go's `!= 0` instead of comma-ok missing the answer |
| 005 both | Boyer–Moore trace table; garbage output when no majority exists |
| 006 both | Array mutating into its own hash table; Go **panicking** `index out of range [-3]` |

Keep this bar. It is the reason the user said "format is nice."

---

## 6 · Progress

**24 Sep 2026 — Topic guides: a Go guide for every topic, and both languages' guides audited and filled.**
User asked for (a) a Go guide beside each Python one, (b) "Read the topic guide" turned into a label plus two buttons
**Python** / **Golang**, each opening a well-laid-out reader page, and (c) no important detail missing from any guide.
- **Webapp.** `server.py`: `DSA_GUIDE_ROOTS`, `load_dsa_guides(lang)` / `read_dsa_guide(id, lang)`, `?lang=py|go` on
  `/api/dsa-guides` and `/api/dsa-guide-doc` (**restart the server**). `reader.js`: `MODULES.dsaguidego`
  (`#/dsa-guide-go/<topic>`), a Python|Golang switch in the guide hero, `repoRoute` sends `…/_TOPIC_GUIDE.md` links to the
  right language's page. `dsa-topic.js` `guideChooser()` renders the label + two buttons on the pattern page (disabled
  if that language's guide is missing); CSS in `dsa-topic.css` / `reader.css`. All 56 guides render with every mermaid
  figure drawn and zero console errors (every guide has at least 2 figures per language now).
- **Content.** Every guide (28 Python, 28 Go) got a gap-filling Part or two, a **"Every Problem in This Topic, by
  Pattern"** table (each problem linked, with the trap documented in its solution file) and extra checklist lines.
  `GoDSA/27_algorithms/_TOPIC_GUIDE.md` and `GoDSA/28_recursion_backtracking/_TOPIC_GUIDE.md` are new. Because the Go
  solution files are still stubs, the Go guides for topics 22–28 carry a complete, tested Go plan for every problem in
  the topic (earlier Go guides carry code for the patterns and the trickier problems). Standing rule kept: every snippet was run (Go compiled with `go vet`, checked against a
  brute-force reference or a chi-square test) and every number in the text was measured on this machine.
- **Factual errors found and fixed in the existing guides** (so they do not come back): Go's goroutine stack starts at 2 KB
  not 8 KB (topics 06/08/09/10/11/14); Go 01's map internals (Swiss tables); Go 02's elimination proof; Go 11's fictional
  `golang.org/x/exp/btree`; Go 13's array-vs-map memory claim; `cmp.Or` is Go 1.22 not 1.21; Go 22's pdqsort thresholds
  (insertion sort up to 12, a `bits.Len(n)` bad-pivot budget, not "depth > 2·log₂ n"), the `sort.Slice`-uses-reflection
  claim, and the small-input stability example (insertion sort is stable, so `sort.Slice` only breaks ties from 13
  elements); Go 23's claim that `strings.Builder` copies are caught by `go vet` (it is a runtime panic); Go 24's claim that flat
  beats `[][]int` (measured: it ties — loop order is the 12× effect) and its wrong counter-clockwise recipe; Go 25's
  mixed-receiver claim; Go 26's `4n` explanation (`2n` fails at `n = 6`); Py 21's "false split" claim about float slopes;
  and several Python/Go table rows. Stray `[cite: N]` artifacts remain in `PyDSA/09_recursion_backtracking/012–014`
  question/solution files (out of scope, not touched).
- **Not done, by the user's call:** the unfinished Go problem solutions (`GoDSA/**/solution.go` placeholders).

**23 Sep 2026 — final-check pass: hygiene, SOAP Go, and a webapp modernization sweep.** An audit of every
module found the Python DSA curriculum (345/345) and all learning modules complete and wired. What it turned up, and
what was done:
- **GoDSA is mostly stubs — NOT fixed, by the user's call.** 299 of 344 `GoDSA/**/solution.go` are placeholders
  (`"not implemented yet"`); real Go exists only for topic 01 (9/14), 08 (all), 10 (all), 11 (1). File counts look like
  parity but are not. §11's "Go second pass" is therefore still entirely open outside those topics.
- **Repo hygiene.** 37 one-off `add_topic_*`/`patch_*`/`fix_*`/`inject_*`/`rewrite_*` scripts moved to
  `_archive/scripts/`; `RAG.md` and `google_prep_plan.md` moved to `_archive/docs/` (`GOOGLE_INTERVIEW_PREP.md` still
  names the latter, path updated). `SYSTEM_DESIGN_GUIDE.md` (served by `server.py` as the SD "Complete guide") and
  `master_dsa_plan.md` (cited by webapp code/README) deliberately stay at the root. `injected.txt`, `pico.save` deleted.
- **SOAP Foundation Go levels 11-13 written** (`complete_soap_service`, `being_a_client`, `bonus_raw_envelope_over_tcp`);
  all 14 Go levels now match Python. gofmt/vet clean, each prints `OK`; `server.py` needed no change (it globs).
- **Webapp.** Mobile: the sidebar was open by default under 860px and covered ~75% of the screen — `setSidebarOpen()`
  (app.js) is now the single owner of open/closed state (hamburger, backdrop tap, Esc, picking a link, search); the
  problem workspace stacks statement over editor on phones instead of squeezing both into one screen; the topbar
  search box hides at <=560px (the quick-jump button replaces it). **⌘K / Ctrl+K quick jump** (`paletteRows`/
  `renderPalette` in app.js, `#palette` in index.html) searches DSA + every module, ranks prefix > word-start >
  substring, ignores the DSA chips, and multi-word queries match in any order (`matchesAll`, also used by the sidebar
  search). Routes: `#/p/<topic>/1/…` now finds `001`; `#/sd`, `#/sql` etc. work as aliases for the published hash.
  Every navigation gets one settle-in (`.view` `view-in` keyframe). SQL, NoSQL, CS Fundamentals, Google Behavioral and
  both StdLib modules had no motif of their own and fell through to the "pytest -v" worker-pool drawing; each now has a
  purpose-built one in `motif()` (reader.js). Module cards' summaries now use the whole first paragraph
  (`doc_meta` in server.py) instead of one hard-wrapped line that ended mid-sentence. Solving a problem now says where
  it leaves you ("3 of 14 in Arrays & Hashing · 4-day streak") and the status button pops. Verified with headless
  Chrome at 1440x900 and 390x844, dark and light: zero console errors. **Restart the server to pick up `server.py`.**

**23 Sep 2026 — SQL/NoSQL modules given full Go parity (all 47 levels), on top of the
Python content.** User asked for Go examples alongside Python in both modules, "full
parity," using both `database/sql` and native pgx for Postgres, plus `mongo-driver/v2`
and `go-redis/v9`. Done via 6 parallel forks (SQL split into four 5-level chunks,
MongoDB and Redis+concepts each one fork), each running real Go code against the live
lab databases and capturing real output — no fabricated numbers, per this repo's
standing rule. Every level in `SQL/00`-`19` and every hands-on level in
`NoSQL/mongodb/`, `NoSQL/redis/`, plus `NoSQL/concepts/00` and `02`, now has a Go
section immediately after its Python one (`NoSQL/concepts/01` stayed prose-only —
no code to parallel). `SQL/01` and `NoSQL/README.md`/`SQL/README.md` document the two
Postgres driver styles (`pgx/v5/stdlib` for `database/sql`, `lib/pq` mentioned as the
legacy alternative, native `pgxpool`) and the Go setup (`go get`, Go 1.25+ requirement
for pgx v5.11+, `GOTOOLCHAIN=auto` handles the toolchain). As with Python, no `.go`
files are committed — snippets are copy-paste-and-run, verified via a scratch Go
module in the session scratchpad (not part of the repo).

Real bugs and surprises the forks caught (all left in the docs honestly, per the
"note on the runtime demos" rule):
- **A genuine pre-existing bug**, caught by the mongo fork and fixed by the
  coordinating session: `NoSQL/mongodb/02_crud_basics.md`'s Python section stated a
  final document count of `0` that was never reachable from its own demonstrated
  `deleteOne`/`deleteMany` sequence — the real, traced, and now-verified value is `1`
  (one `done: true` document always survives `deleteOne`). Fixed at the root (the
  Python output), not papered over in the Go section.
- pgx's binary protocol panics scanning a Postgres `DATE` into a Go `string`
  (`SQL/07`) — psycopg has no such restriction; documented as a first-class gotcha.
- Connection-pooling's speedup was far larger in Go (37.1x, `SQL/13`) than Python's
  7.8x, because an unpooled loop pays `sql.Open`'s per-call driver setup on top of the
  TCP handshake.
- `go-redis`'s `MaxRetries` compounds with the connection pool's own internal dial
  retry (`NoSQL/redis/11`) — 2108ms measured instead of the ~800ms a naive estimate
  predicts; written up with the real log evidence.
- The Go v2 Mongo driver has no `socketTimeoutMS` at all — replaced by a unified
  `SetTimeout` (CSOT spec) — a real driver-design difference from the Python side,
  documented in `NoSQL/mongodb/11`.
- Two independent single-node MongoDB transaction-overhead measurements (Python 0.96x,
  Go 0.56x) both show a transaction running *faster* than the non-transactional
  baseline — reported as-is both times, with the same "this is a single-node artifact,
  not a real production signal" caveat already in the file.

Verified end to end: all code fences balanced across all 47 files (fence-count parity
checked file by file), `/api/sql` (21 items) and `/api/nosql` (28 items) unchanged in
count from before this work (no new files, no `server.py` changes needed), a real
headless-Chrome pass renders four spot-checked pages with zero console/page errors,
and the live lab Postgres/MongoDB/Redis were confirmed clean of scratch objects left
over from any fork's demos (compared table/database/key lists before and after).

**23 Sep 2026 — SQL/NoSQL gap-fill: normalization, replication, sharding, wide-column,
and interview playbooks, 7 new files, fully wired.** The SQL/NoSQL module below was
already built and webapp-wired earlier the same day, but audited against what a
working engineer is actually asked in interviews and found genuinely missing:
normalization/denormalization, replication/HA, and sharding had no coverage anywhere
in `SQL/`, and `NoSQL/` had no wide-column (Cassandra/DynamoDB) design content or any
cross-cutting SQL-vs-NoSQL / CAP-applied decision material beyond a one-line mention.
Closed with real, measured content (this repo's standing rule — nothing here is a
fabricated number):
- **`SQL/16_normalization_and_denormalization.md`** — all three anomalies (update,
  delete, insert) reproduced live against a real denormalized table, then fixed by
  splitting on functional dependency; denormalization framed as a deliberate, measured
  reversal, not a default.
- **`SQL/17_replication_and_high_availability.md`** — real logical replication set up
  between two databases on the lab Postgres instance (`CREATE PUBLICATION`/
  `CREATE SUBSCRIPTION`), replication lag actually measured (**26ms**, polled from
  commit to visible-on-replica). Required flipping the lab Postgres to
  `wal_level = logical`, done both live (`ALTER SYSTEM` + restart) and durably in
  `docker-compose.databases.yml`'s `command:` so a fresh volume still has it. Hit and
  solved a real same-instance logical-replication self-deadlock (`CREATE SUBSCRIPTION`
  with default `create_slot=true` waits on "transactions older than this one," which
  includes its own still-open transaction) — fixed by creating the slot as a separate,
  already-committed statement first. Also covers physical vs. logical replication,
  sync vs. async tradeoffs, and what a real failover requires (detection/promotion/
  reconfiguration/split-brain), honestly separating "Postgres has replication" from
  "Postgres has automatic failover" (the latter needs Patroni/repmgr/a managed layer).
- **`SQL/18_sharding_and_horizontal_scaling.md`** — real 2,000,000-row measurement:
  flat indexed table vs. Postgres native `PARTITION BY RANGE`, same range query,
  **26.294ms → 8.357ms**, with the real `EXPLAIN` plan proving partition pruning (only
  `events_part_2026_02` touched, the other 3 partitions never considered). Explicitly
  distinguishes partitioning (one instance) from sharding (multiple instances, no free
  joins/FKs/transactions across shards), plus shard-key strategies and the hot-shard/
  resharding failure modes.
- **`SQL/19_interview_playbook.md`** — worked, real-output query patterns (Nth-highest-
  per-group via `DENSE_RANK`, duplicate detection, running totals) plus precise answers
  to the conceptual questions this ladder gets asked as.
- **`NoSQL/concepts/`** (new group, 3 files, required a small `webapp/server.py`
  change: `NOSQL_GROUPS`/`NOSQL_ID_RE` extended to include `concepts`) —
  `00_wide_column_and_dynamodb_style_databases.md` (partition/sort key model, a worked
  single-table DynamoDB schema, Cassandra's `R + W > N`, explicitly labeled as design-
  level since no Cassandra/DynamoDB container exists in this repo's lab stack);
  `01_choosing_a_database_and_cap_theorem.md` (a 4-step decision framework across
  SQL/Mongo/Redis/wide-column, and a table naming the concrete consistency knob real
  systems expose — Postgres's `synchronous_commit`, Mongo's write concern, Cassandra's
  consistency level, DynamoDB's eventual/strong toggle — deliberately consistent with
  `SystemDesign/building_blocks/10_distributed_systems_theory.md`'s point that CAP is
  per-operation, not a static per-product label); `02_interview_playbook.md` (worked
  NoSQL data-modeling questions: blog comments, a leaderboard, rate limiting, a
  distributed lock).
- Both READMEs' roadmap tables and level counts updated (`SQL/` 16→20 levels,
  `NoSQL/` gains the `concepts/` group). Verified end to end with a real headless-
  Chrome pass: `/api/sql` and `/api/nosql` list all new items, both new doc endpoints
  serve real markdown, and `#/sql/19_interview_playbook` /
  `#/nosql/concepts/02_interview_playbook` render actual content client-side with zero
  console/page errors.

**24 Sep 2026 — No source paths in the webapp.** The problem header no longer shows the file path. In markdown, repo
paths (inline code, link targets/labels, `file:///` links, cross-module `../` refs) are rewritten by `reader.js`
`repoRoute()`/`rewriteLinks()` into links to the app page, labelled with its title; refs with no page become plain words.
Adding a new module/doc type means adding a rule to `repoRoute()`.

**23 Sep 2026 — Rebrand + workspace polish.** App is now "Ultimate Engineering Guide" (logo `webapp/static/logo.svg`,
also the favicon). Sidebar DSA filter chips removed. Problem header is one compact row. Code panel toggle
(`#toggleCode`, ⌘\\) hides the editor; Topic-guide tab removed from the workspace (guide = `#/dsa-guide/<topic>`).

**23 Sep 2026 — PyDSA topic guides are now their own reading page, with diagrams.**
`PyDSA/<topic>/_TOPIC_GUIDE.md` used to render as a bare "Topic guide" tab inside the code workspace. It is
now a full reader page at `#/dsa-guide/<topic>` (TOC rail, section checks, highlights, focus mode, prev/next
guide) built as a reader.js module (`MODULES.dsaguide`, not a sidebar section — it keeps the DSA row and
accent; `back` sends you to the pattern page). Server: `/api/dsa-guides` + `/api/dsa-guide-doc` (restart
the server after pulling). Entry points: "Read the topic guide" on the pattern page, and the workspace
Topic-guide tab / old `#/p/<topic>/<seq>/guide` bookmarks redirect there (Python only — Go guides still
render inline in the tab). 84 mermaid diagrams (2–4 per guide, all 28 guides) were added inside the guide
markdown as ```` ```mermaid ```` blocks with a `%% caption:` line; every one parses (mermaid.parse) and
renders in dark + light. Guide diagrams are drawn at natural size (`.reader[data-mod="dsaguide"]` CSS +
`--nat` set in `renderMermaidBlocks`).

**23 Sep 2026 — New module: SQL (PostgreSQL) + NoSQL (MongoDB + Redis), 42 files, fully wired.**
An earlier session had stubbed the webapp backend for this (`webapp/server.py` `SQL_DIR`/`NOSQL_DIR`,
`load_sql`/`load_nosql`/`read_sql`/`read_nosql`, routes `/api/sql*`/`/api/nosql*`) but never written
the content or wired the frontend. Both finished this session:
- **`SQL/`** (README + 16 levels, `00`–`15`): relational model → connecting (psql + psycopg3) →
  DDL/types → CRUD → filtering/pagination (keyset vs offset, measured) → constraints → joins →
  aggregation/window functions → subqueries/CTEs → transactions & isolation levels (real lost-update
  race, fixed with `SELECT ... FOR UPDATE`; real `REPEATABLE READ` serialization failure) → indexing
  (`EXPLAIN ANALYZE`, measured ~244x seq-scan-vs-index-scan) → SQL injection (live exploit against a
  vulnerable query, then the parameterized fix) → schema migrations (measured ~1125x cost of a
  volatile vs constant column default) → connection pooling & ORM-vs-raw-SQL (measured N+1: 74x) →
  a being-a-client capstone (pool + retries + `statement_timeout`) → an optional bonus level on how
  Postgres executes a query. Cross-references `CSFundamentals/03_databases_deep_dive.md` (MVCC) and
  `SoftwareDesign/09_data_design_and_schema_evolution.md` (expand/contract) instead of duplicating.
- **`NoSQL/`** (README + `mongodb/00`–`11` + `redis/00`–`11`): MongoDB side covers the document
  model, CRUD, query operators, **embedding vs. referencing** (the core document schema-design call,
  with a real BSON-size measurement crossing the 16MB doc limit), indexes (measured ~50x), the
  aggregation pipeline (`$lookup` framed as the join-equivalent), updates, schema validation,
  multi-document transactions, and write/read concern — through a pooling capstone (measured 5.2x
  penalty for a fresh `MongoClient` per call vs. one shared client). Redis side covers the key-value
  model, strings/counters, hashes/lists/sets, sorted sets/leaderboards, caching patterns (cache-aside,
  stampede), pub/sub, transactions & pipelining (measured 34-39x speedup), distributed locking (with
  an honest Redlock critique), rate limiting backed by real shared Redis (contrasted against the
  in-memory limiter in `API/REST/labs/golang/04_rate_limit_middleware`), RDB/AOF persistence, and a
  client capstone. Both cross-reference `SystemDesign/building_blocks/06_database_internals.md` and
  `10_distributed_systems_theory.md` for replication/CAP theory instead of duplicating it.
- Every code sample (mostly Python: `psycopg3`, `pymongo`, `redis-py`; some `psql`/`mongosh`/
  `redis-cli`) was actually run against real, dockerized services during authoring — all measured
  numbers above are real captures, not fabricated, per this repo's "measured, not asserted" rule.
- **Lab environment:** `docker-compose.databases.yml` at repo root — Postgres 16 (`localhost:5544`,
  user/pass/db `dsa`), MongoDB 7 as a **single-node replica set** `rs0` (`localhost:27018` — a
  standalone `mongod` can't do multi-doc transactions or write/read concern at all, not just "hard to
  demo," so the compose file runs `--replSet rs0 --port 27018` and `rs.initiate()` must be run once
  after first `up`), Redis 7 (`localhost:6390`). Non-default ports so this never collides with
  services already running natively (e.g. the user's brew-installed MongoDB on 27017).
  `SQL/requirements.txt` (`psycopg[binary]`, `psycopg_pool`) and `NoSQL/requirements.txt` (`pymongo`,
  `redis`) let a reader re-run every snippet themselves.
- **Webapp wiring** (backend already existed): added `MODULES.sql`/`MODULES.nosql` to
  `webapp/static/reader.js`, `'sql'`/`'nosql'` to `SECTIONS` + `SECTION_ICON` in
  `webapp/static/app.js`, accent colors in `webapp/static/reader.css`. No `index.html` changes needed
  (generic module-reader pattern, unlike API's bespoke practice layer). Verified end to end with a
  real headless-Chrome pass (Playwright): `#/sql` and `#/nosql` render, sidebar shows `SQL 0/17` and
  `NoSQL 0/25`, NoSQL's Overview/MongoDB/Redis grouping tabs work, zero console/page errors.

**16 Sep 2026 — Google prep plan gap closure (read this first; supersedes counts below).**
`google_prep_plan.md` (the user's Google L5 syllabus) was audited against the repo and every gap closed:
- **TSV now 344 problems, 28 topics; CURRICULUM.md shows 344/344 Python.** Topic 03's TSV rows were
  renumbered to match the 13 files on disk (it used to show 2/10), plus 014 Minimum Window Substring and
  015 Sliding Window Maximum. Topic 02 finished (008–010) plus 011 Boats. 28 more problems added in
  topics 01, 06, 10 (020 also in Go), 12, 13, 14, 15, 16, 17 (incl. digit DP 017–018), 19, 25. All 161
  practice problems named in google_prep_plan.md now exist. Topic guides got an "Added problems" section.
- All 344 solution files verified `ALL PASSED`. Two pre-existing failures fixed in their TEST code only:
  10_trees/008 (random values 0–2 could never trigger the no-delimiter bug) and 25_design/009 (random ops
  generated inputs LeetCode rules out).
- New modules/files: `CSFundamentals/05–10_*_deep_dive.md` (concurrency, DS internals, complexity, Python
  stdlib, coding-round execution, Google follow-ups); 01–04 rewritten to fix factual errors (CAS bus lock,
  2 MB stacks, epoll O(1), QUIC 0-RTT, IW10/CUBIC β, TLS 1.3 order, LSM write amp, 2PC absolutism) while
  keeping the peer session's lab `<div>`s and mermaid blocks. `GoogleBehavioral/01, 04, 05, 06`.
  `SoftwareDesign/01–02`. `GOOGLE_INTERVIEW_PREP.md` rewritten as the 12-week plan mapped to files.
- SystemDesign split with a parallel session (dsa-practice-42): it owns new SD files (00 playbook,
  building_blocks 18–25, problems 022–030, READMEs, webapp). This session deepened solutions 004/005/006,
  added sections to 011/016 and building_blocks 05/14/15 (existing `##` headings must stay unchanged —
  webapp labs attach to them).
- Webapp lists `CSFundamentals/NN_*_deep_dive.md`, `GoogleBehavioral/NN_*.md`, and (since 17 Sep 2026)
  **Software Design** — see below.
- **17 Sep 2026 — SoftwareDesign complete and in the webapp.** Chapters were RENUMBERED into reading
  order (all cross-references, including `` `NN` §x `` short refs and lld solution RELATED blocks, updated):
  Part 1 `01` philosophy · `02` OOP & domain modeling · `03` modularity/coupling/API · `04` patterns;
  Part 2 `05` testability/refactoring · `06` error handling · `07` concurrency;
  Part 3 `08` application architecture · `09` data & schema evolution · `10` observability ·
  `11` performance · `12` security; Part 4 `13` design docs & leadership (rewritten, ~800 lines) ·
  `14` LLD interview playbook. `SoftwareDesign/README.md` is the start-here page.
  Chapters 06–12 were written this session: every embedded Python/Go program was run (`ALL PASSED`;
  Go with `-race`); each opens with an "Already covered elsewhere" table — keep new files from
  duplicating CSFundamentals/SystemDesign/PyEngineering.
  `lld/017_text_editor_undo_redo_question.py` created (was missing); 017 solution's demo 2 fixed (it
  failed its own memory check). All 17 lld solutions print `ALL PASSED`.
  Webapp: `server.py` `load_software_design()` orders README → parts (`SWD_CHAPTER_PARTS`) → LLD sets
  (`SWD_LLD_SETS`: warm-up 008/009/003, core 001/002/004/005/006, breadth 007/010/011/012, Tier 2
  013–017) with a running `step` number 0–31. LLD problems are eng lang `"lld"` (`ENG_ROOTS`), opened at
  `#/eng/lld/<id>` in the code workspace with Brief/Solution/Notes tabs; Run swaps the question file.
- **17 Sep 2026 — webapp navigation: the missing middle level.** A DSA topic's problems could only
  be reached by unrolling the sidebar accordion, which is why "topic → its questions" looked bad.
  Added **pattern pages** at `#/t/<topic>` — `static/dsa-topic.js` + `static/dsa-topic.css`, view
  `#viewDsaTopic`, registered in `VIEWS`/`route()`. The page has a hero (family tint, progress ring,
  difficulty mix, Continue CTA, Topic-guide link), a scannable problem list (seq, status glyph, title,
  LC, Go badge, review-due badge, difficulty, time on problem), status + difficulty filters, three
  sort orders (curriculum / unsolved first / easiest first) and prev/next pattern cards.
  Wiring: DSA-home cards, lattice cells and the "thinnest pattern" tile now open `#/t/<id>` instead of
  jumping into one problem; the sidebar topic row is now caret (expand in place) + name (open the
  pattern page) with `.topic.is-on` marking the current one; the workspace crumb is a link back up;
  `route()` accepts `#/p/<topic>/<seq>/<tab>` so a link can open a problem on a given tab.
  Learning modules: `renderModGrid()` now emits a sticky category chip rail (`wireModRail`,
  `.mod-rail` in `reader.css`) for any module with more than one group — counts per group, click to
  jump, scroll-spy marks where you are. Long pages (Software Design's four parts, 31 entries) were
  previously one unbroken scroll.
- **17 Sep 2026 — the sidebar was flattened to modules + filters.** It used to be a flat module list
  plus the contents of whichever module you were standing in (`#topics` for DSA / `#modnav` for a
  module, swapped by `syncModuleChrome`). A three-level tree over all ten branches was tried first and
  rejected as too busy — the user's call: "keep it simple, sidebar should have just modules and
  filters". Final shape (`#modules`, `renderSidebar()` in `app.js`): Dashboard/Review, the DSA
  difficulty + status chips, then one `.mod-item` row per module with icon, name, done/total and a 2px
  progress hairline; the active module's row is marked. Every module list is fetched once on boot
  (`loadSections`) so the counts are real and search can reach a module you have never opened.
  Search (2+ chars, `renderResults`) replaces the module list with one flat result list across DSA and
  all nine modules, each row labelled with its section, capped at 60; the chips narrow the DSA half.
  Hierarchy now lives on the pages instead: DSA home → pattern page → problem, module home → cards.
  `renderModNav()` is an alias for `renderSidebar()`; `modOpenGroups`, all `.modnav*`/`.mgroup*`/
  `.mitem`/`.prob`/`.topic*`/`.ring` sidebar CSS and the module `nav-item`s in `index.html` are gone
  (their SVGs live in `SECTION_ICON` in `app.js`). `showView()` records `curView`, which
  `activeSection()` uses to mark the live module row.
- **17 Sep 2026 — solutions are gated; animated SD request flows.** `static/solution-gate.js` owns the
  "Reveal solution" gate for BOTH System Design practice problems (reader.js calls `revealGateHTML`,
  `revealBannerHTML`, `revealIsOpen/revealOpen/revealClose`) and DSA solutions (`loadPane('solution')`
  in app.js hands off to `renderGatedSolution`). A reveal is scoped to the current route: switching
  tabs inside the problem keeps it open; any navigation away or reload hides it again (reveal counts
  still go to progress.json: `docs[..].reveals`, `problems[..].solutionViews`). Revealed DSA solutions
  start with a "Watch it run" dsa-viz player — exact animation for ~52 problems (title match or
  `SOLUTION_ALGO_FOR`), otherwise the topic's pattern animations, collapsed and labelled as such.
  To give a problem its own animation: add a `defineAlgo` whose title equals the problem title (or map
  it in `SOLUTION_ALGO_FOR`). `static/sd-flow.js` is a data-driven animated request-flow engine
  (`defineFlow(name, {zones, nodes, edges, scenarios})`, SVG + CSS vars, play/step/speed, narrated
  steps with latency); `sd-flow-shortener` (6 scenarios) sits in URL shortener's reference design via
  `SD_LABS` in sd.js. Styles: `static/sd-flow.css`. Other SD problems can get flows the same way.

**Python: 262 / 313** (see CURRICULUM.md, auto-generated, for the live count;
the curriculum grew from 288 to 313 problems with the addition of Topic 28,
Recursion Mastery — a dedicated 25-problem topic covering recursion patterns
not already exercised elsewhere, ranging from Easy single-call recursion
through Hard tree/DP/backtracking problems. It is NOT in the original TSV
count cited elsewhere in this file's older sections — treat any "288" figure
below as historical, and 313 as current).
Go: topic 01 (001–006), topic 08 (all 15), topic 10 (all 19) = 40 problems.
Python is the number that matters — see §11.

| Topic | Problems | Py | Guide |
|---|:--:|:--:|:--:|
| 01 · Arrays & Hashing | 12 | **12/12 ✅** | ✅ Py + Go |
| 02 · Two Pointers | 10 | **7/10** | ✅ Py |
| 03 · Sliding Window | 10 (+3 extra) | **13/13 ✅** | ✅ Py |
| 04 · Prefix Sum | 8 | **8/8 ✅** | ✅ Py |
| 05 · Binary Search | 12 | **12/12 ✅** | ✅ Py |
| 06 · Stack & Monotonic Stack | 10 | **10/10 ✅** | ✅ Py |
| 07 · Queue & Deque | 6 | **6/6 ✅** | ✅ Py |
| 08 · Linked List | 15 | **15/15 ✅** | ✅ Py + Go |
| 09 · Recursion & Backtracking | 14 | **14/14 ✅** | ✅ Py |
| 10 · Binary Trees | 19 | **19/19 ✅** | ✅ Py + Go |
| 11 · Binary Search Tree | 8 (+3 extra) | **11/11 ✅** | ✅ Py |
| 12 · Heap / Priority Queue | 10 | **10/10 ✅** | ✅ Py |
| 13 · Trie (Prefix Tree) | 6 | **6/6 ✅** | ✅ Py |
| 14 · Graphs | 16 | **16/16 ✅** | ✅ Py |
| 15 · Advanced Graphs | 12 | **12/12 ✅** | ✅ Py |
| 16–20, 22–26 | 101 | 0 | — |
| 21 · Math & Geometry | 10 | **10/10 ✅** | ✅ Py |
| 27 · Classic Algorithms | 8 | **8/8 ✅** | ✅ Py |
| 28 · Recursion Mastery | 25 | **25/25 ✅** | ✅ Py |

**Topic 21 (Math & Geometry) completed 10 Sep 2026, 10/10, Python.** All ten
problems: 001 Palindrome Number (half-reversal to avoid a full digit
reverse), 002 Plus One (manual carry propagation, array-grows-on-all-9s
edge case), 003 Happy Number (cycle detection via a seen-set or Floyd's
slow/fast pointer over the digit-square-sum function — explicitly
cross-referenced against topic 08's linked-list cycle detection as the
same technique in a different domain), 004 Pow(x, n) (binary/fast
exponentiation, recursive and iterative), 005 Multiply Strings
(grade-school digit-array multiplication, no bignum conversion allowed),
006 Integer to Roman (greedy table with the six subtractive pairs baked
in), 007 Factorial Trailing Zeroes (count factors of 5 via
floor(n/5)+floor(n/25)+..., never computing n! itself), 008 Count Primes
(Sieve of Eratosthenes), 009 Detect Squares (hash map of point counts,
iterating only same-x diagonal candidates), and 010 Max Points on a Line
(gcd-reduced (dx,dy) integer pairs as an exact slope key, never a float).
A genuine bug was caught while writing 003's test cases: a fabricated
expected value (`116 -> happy`) was actually wrong (116 is NOT happy —
its chain enters the same 8-number unhappy cycle as 2), caught only
because the test actually ran and failed. Real measured surprises,
reported honestly per the "measured, not asserted" rule rather than
adjusted to match intuition: in 003, the O(n)-space seen-set beat
O(1)-space Floyd's on wall-clock time (Floyd's calls the step function
~3x per outer iteration vs. the seen-set's 1x); in 006, a plain
digit-by-digit if/elif beat the "cleaner" flat lookup-table greedy loop;
in 001, Python's C-level `s[::-1]` string reversal beat the pure-integer
half-reversal arithmetic; in 005, native `int()` conversion beat the
required manual digit-array simulation by roughly 1000x (expected and
irrelevant to correctness, since the problem explicitly forbids it — the
measurement exists purely to be honest about this machine's numbers).
010's write-up also includes a verified (not hypothetical) IEEE-754 float
collision: two different, already-lowest-terms fractions built from
consecutive Fibonacci numbers (`F(40)/F(39)` and `F(41)/F(40)`) divide to
the exact same Python float, concretely demonstrating why a float-keyed
slope hash map is unsafe and a gcd-reduced integer key is required.

**Topic 27 (Classic Algorithms — Randomized, Divide & Conquer, Quickselect)
added 10 Sep 2026**, a brand-new topic covering interview-classic techniques
not present anywhere else in the curriculum (checked against every existing
topic in `tools/problems.tsv` first). Python-only per §11 (not a
pointer/memory topic). All 6 problems: 001 Shuffle an Array (Fisher-Yates,
with a live 100k-trial frequency demo showing a naive full-range shuffle is
measurably biased — 34% max deviation vs 1.2% for Fisher-Yates), 002 Random
Pick Index and 003 Linked List Random Node (reservoir sampling, size 1, with
the telescoping-product uniformity proof and empirical frequency demos), 004
Random Pick with Weight (prefix sum + binary search, measured 101x faster
than a linear scan at n=5000), 005 Wiggle Sort II (Quickselect + three-way
virtual-index partition — the runtime demo honestly reports that CPython's
C-level Timsort actually beats this pure-Python O(n) Quickselect in wall-
clock time at n=200,000, a measured constant-factor artifact kept as-is per
the "measured, not asserted" rule rather than adjusted to match the
asymptotic expectation), and 006 Different Ways to Add Parentheses (divide &
conquer memoized by expression SUBSTRING, contrasted explicitly against
topics 16/17's array-indexed DP state). All 6 solution files independently
verified `ALL PASSED`.

**Topic 27 extended to 007–008, 10 Sep 2026** — the topic's two real
remaining gaps: 007 Find the Kth Largest Integer in a String (LC 1985, the
CANONICAL Quickselect exercise for this topic, with a custom length-first-
then-lexicographic comparator — `"9" > "10"` lexicographically but `9 < 10`
numerically, a live demo shows plain string sort returning the wrong answer
while the length-aware comparator returns the correct one) and 008 Random
Pick with Blacklist (LC 710, Hard — the advanced randomized-remapping
technique: shrink the draw range to `whitelist_size = n - len(blacklist)`
and remap the handful of low-range blacklisted values to valid high-range
targets in O(B) preprocessing, one random() call per O(1) pick; measured
live against naive reject-and-resample, which needed ~10,673x more
random() calls per pick on a 99.99%-blacklisted range). Both LC 1985 and
LC 710 were confirmed absent from every other topic in `tools/problems.tsv`
before adding. Both solution files independently verified `ALL PASSED`.
Topic 27 is now 8/8, curriculum total 288.

**Topics 11–15 completed 10 Sep 2026** by five parallel subagents (Python-only —
GoDSA left untouched for this batch per user instruction), each reading this file
first and following §4/§5 exactly. All 55 solution files verified `ALL PASSED`
(independently re-confirmed by the coordinating session, not just self-reported).

- **Topic 11 (BST)** finished 006–008 and added 3 extras for pattern coverage —
  009 Recover Binary Search Tree (LC 99, Hard — in-order dip detection + Morris
  traversal), 010 Inorder Successor in BST (LC 285), 011 Minimum Absolute
  Difference in BST (LC 530 — adjacent-in-order-pairs-suffice proof). TSV rows
  appended for all three.
- **Topic 12 (Heap)** — all 10 problems (Kth Largest in a Stream through Minimum
  Interval to Include Each Query). Notable: Reorganize String's round-robin fill
  beat the heap-churn approach 4.4x — a case where the "simpler" non-heap
  approach wins, caught by actually measuring rather than assuming.
- **Topic 13 (Trie)** — all 6 problems. Caught and fixed two real bugs while
  writing tests: Map Sum Pairs' root-node sum wasn't updated on re-insert
  (`sum("")` returned 0), and Word Search II's first test board made one target
  word geometrically unreachable.
- **Topic 14 (Graphs)** — all 16 problems (flood fill through word ladder),
  written via 4 sub-subagents then independently re-verified. Demonstrates a
  live `RecursionError` on deep/degenerate grids for naive recursive DFS, and a
  false-positive cycle detection from reusing a single `visited` set on a
  directed graph (course schedule).
- **Topic 15 (Advanced Graphs)** — all 12 problems: Union-Find, Dijkstra,
  Bellman-Ford, Prim's MST, Floyd-Warshall, Kahn's topo sort, Hierholzer's
  Eulerian path, and Tarjan's bridge-finding. Extra correctness diligence per
  instructions: hand-traced 10 of the 12 against real state, and stress-tested
  Tarjan's bridges against a brute-force oracle over 300 random graphs with
  zero mismatches.

**Topics 05–10 completed 9 Sep 2026** by six parallel subagents, each reading this
file first and following §4/§5 exactly. All solution files verified `ALL PASSED`;
all Go files `gofmt`-clean and `go vet`-clean. Notable fixes made along the way:
topic 09's `010_letter_combinations` files were renamed to match the TSV slug
exactly (`010_letter_combinations_of_a_phone_number_*`) — `gen_curriculum.py`
matches on `{seq}_{snake(slug)}_solution.py` exactly, so a shortened filename
silently reads as "not written." Also fixed in 09: an empty `010` solution file,
an unreachable-word test board in `012_word_search`, and a fabricated expected
row in `014_sudoku_solver` — all left behind by a prior session, caught by
actually running the files (see the runtime-demos rule below).

**Topic 01 · COMPLETE in Python.** 001 Concatenation · 002 Contains Duplicate ·
003 Valid Anagram · 004 Two Sum · 005 Majority Element · 006 Find Disappeared ·
007 Group Anagrams · 008 Top K Frequent · 009 Encode/Decode Strings ·
010 Product Except Self · 011 Valid Sudoku · 012 Longest Consecutive.
(001–006 also have Go; 007–012 are Python-only per the §11 lane.)

**Topic 02 · 7/10.** 001 Valid Palindrome · 002 Valid Palindrome II ·
003 Remove Duplicates · 004 Remove Element · 005 Move Zeroes · 006 Two Sum II ·
007 3Sum. Remaining: 008 3Sum Closest (16) · 009 Container With Most Water (11) ·
010 Trapping Rain Water (42, Hard).

**Topic 03 · Sliding Window · 13/13 (10 planned + 3 extra).** 001 Best Time to Buy/Sell
Stock · 002 Maximum Average Subarray I · 003 Maximum Number of Vowels · 004 Contains
Duplicate II · 005 Longest Substring Without Repeating Characters · 006 Max Consecutive
Ones III · 007 Longest Repeating Character Replacement · 008 Minimum Size Subarray Sum ·
009 Fruit Into Baskets · 010 Permutation in String · 011 Find All Anagrams in a String ·
012 Binary Subarrays with Sum · 013 Subarrays with K Different Integers.

**Topic 04 · Prefix Sum · 8/8.** 001 Running Sum of 1d Array · 002 Range Sum Query -
Immutable · 003 Find Pivot Index · 004 Subarray Sum Equals K · 005 Contiguous Array ·
006 Range Sum Query 2D - Immutable · 007 Subarray Sums Divisible by K · 008 Continuous
Subarray Sum.

Every solution file verified: all 40 print `ALL PASSED`.

Topic guides: `01_arrays_hashing` (Py + Go), `02_two_pointers` (Py — four-pattern
taxonomy, Python slicing/immutability traps, 3Sum dedupe, pattern decision tree),
`03_sliding_window` (Py — monotone-validity mechanism, why the inner while is
amortized O(n), sliding window vs two pointers), `04_prefix_sum` (Py — prefix-sum-as-
hashmap-key pattern, sliding window vs prefix sum for arbitrary-sign data, 2D
inclusion-exclusion). Remaining: 22 Python guides.

**Curriculum shape:** 27 topics, 288 problems (73 Easy / 172 Medium / 43 Hard,
including the 3 topic-11 extras and topic 27's 8 problems).
Covers arrays, two pointers, sliding window, prefix sum, binary search, stack, queue,
linked list, recursion/backtracking, trees, BST, heap, trie, graphs, advanced graphs
(Dijkstra/Bellman-Ford/MST/Union-Find/Tarjan), DP 1D+2D, greedy, intervals, bits,
math, sorting algorithms, string algorithms (KMP/Rabin-Karp), matrix, design,
segment tree/Fenwick, and classic algorithms (randomized, divide & conquer,
Quickselect).

### ⚠️ Parallel sessions happen — check mtimes before writing

On 7 Sep 2026 two Claude sessions wrote `PyDSA/02_two_pointers` simultaneously and
one silently overwrote the other's `004_remove_element_solution.py`. Recovered by
negotiating a split over SendMessage; the surviving 004 is the other session's
version (718 lines, verified ALL PASSED) and it was deliberately KEPT rather than
reverted.

**Before writing a problem file: `ls -lT <topic-dir>` and check whether it already
exists.** If another session is active, agree an explicit range split first. Also
note only ONE session should run `tools/gen_curriculum.py` and edit this file.

### A note on the runtime demos (learned the hard way, 7 Sep 2026)

Several §5 "prove it at runtime" demos in 007–012 CONTRADICTED the prose written
alongside them, and the contradictions were only caught by actually running the
file. Real examples from this batch:

- **008** — bucket sort is O(n) and the *slowest* of the four in CPython, because
  allocating n+1 list objects costs more than a C-coded sort of 20k keys.
- **011** — bitmasks are *slower* than 27 sets in CPython (boxed ints, no
  registers), the reverse of the C/Go intuition.
- **012** — here the O(n) set *does* beat the sort, opposite to 007/008.
- **011** — the first `%`-vs-`//` demo board did not discriminate at all
  (distinct digits never collide); it needed the SAME digit at (0,0) and (3,3).
- **009** — the escaping codec silently failed `[]` vs `[""]`, and a
  `join`-vs-`+=` benchmark measured nothing because CPython optimises
  `a = a + b` in place when the refcount is 1.

**Rule: write the demo, RUN it, then write the prose to match the output.**
Never state a performance claim you have not measured on this machine.

**21 Sep 2026 — API module restructured** (`API/`, see `API/README.md`). Per type (REST, GraphQL, Protobuf, gRPC,
WebSockets, Webhooks, SOAP): one `Theory.md` + `labs/python/` (5) + `labs/golang/NN_name/main.go` (5). Labs 1-2 basic,
3-5 advanced; Python and Go sets are DIFFERENT on purpose. Every lab is self-contained (own server on port 0), asserts,
and ends with `OK`. One Go module `API/go.mod`, `API/requirements.txt`. Old guides/code moved to `API/_archive/`.
The webapp now strips YAML front matter in `read_markdown`. All 70 labs verified (parallel soak x2), 34 mermaid blocks
parse-checked. Fundamentals/01-04 written. Next for the API module: advanced system visualisations (viz-api.js).

**22 Sep 2026 — NEW MODULE: `PyStdLib/` + `GoStdLib/`, standard-library mastery, level 1-10.** Distinct from
`PyEngineering`/`GoEngineering` (which assume competence and teach whole production systems) — this pair of modules
teaches the standard library itself, one package per directory, starting from real beginner basics. 15 packages per
language (chosen to not duplicate what `PyEngineering`/`GoEngineering` 26-35 already deep-dive — no asyncio/GIL,
`context`/`sync`/`reflect`/`unsafe`): Python `os, sys, pathlib, io, json, csv, re, collections, itertools, functools,
datetime, subprocess, logging, argparse, contextlib`; Go `os, fmt, io, bufio, strings, strconv, bytes, path/filepath,
encoding/json, encoding/csv, time, sort, errors, regexp, slices` (the last is the Go 1.21+ generics package). Each
package dir has a `GUIDE.md` (concepts + gotchas table) plus 10 standalone, independently runnable level files
(Python: `level_NN_slug.py`; Go: `level_NN_slug/main.go`, one `package main` per level since Go can't share a
`main()`). Level shape: 1 basic call -> 2 core API -> 3 idiom -> 4 real error handling -> 5 intermediate pattern ->
6 MEASURED perf comparison (real numbers, reported honestly even when counter-intuitive) -> 7 lifecycle/resource
concern -> 8 interop with another stdlib package -> 9 production gotcha shown failing then fixed -> 10 capstone.
Built by 10 parallel subagents (5 Python groups, 5 Go groups, 3 libraries each); every one of the 300 level files
was independently re-run by the coordinating session after all agents finished (`.venv/bin/python`/`go run`,
150/150 + 150/150 pass, `gofmt`/`go vet` clean across all of `GoStdLib`). Real bugs were caught and fixed during
the build (not left for later): a Python 3.13 `re.error`/`PatternError` inheritance change, a `json`
`object_pairs_hook`-overrides-`object_hook` gotcha, a platform-verified `csv` `newline=''` corruption case, a
`bufio.Scanner.Bytes()` aliasing demo that had to be rebuilt with a forced-compaction reader to actually reproduce,
and several miscalculated "expected" values in test assertions caught only by running the file (same standing rule
as the "note on the runtime demos" above). Webapp wiring was deferred at first and has since been done (`STDLIB_ROOTS` + `/api/stdlib*`
in `server.py`, `pystdlib`/`gostdlib` in `reader.js`, `stdlib-practice.js`).

**23 Sep 2026 — API module's `Foundation/` ladder wired into the webapp, editable and runnable.** Until now
`API/<Type>/Foundation/` (the 00-13 level ladder per type, see api-foundation-teaching-order.md) and `labs/` were
invisible in the webapp — `load_api()` only globbed `API/*/*.md`, so only `Theory.md` + `Fundamentals/*.md` showed.
Added a third workspace mode alongside `dsa`/`eng` (`mode = 'api'` in `app.js`) sharing the same `#viewProblem`
editor/console: `webapp/server.py` gained `API_TYPES`, `api_ladder()`, `load_api_types()`, `load_api_type()`,
`read_api_file()`, `run_api_file()` and four endpoints (`/api/api-types`, `/api/api-type`, `/api/api-file`,
`/api/api-run`); new `webapp/static/api-practice.{js,css}` add `#/api-type/<Type>` (a type's full Foundation +
labs ladder, prev/next to the neighbouring style — same shape as `dsa-topic.js`'s pattern page) and
`#/api-item/<Type>/<section>/<id>` (the level itself: explanation via reader.js's `renderEngExplanation`, editable
code, Run, Python/Go toggle). The API module home (reader.js) now shows a "Practice" strip above the Theory/
Fundamentals doc grid, and each type's Theory page has a CTA into its practice ladder. **New:** `API/.venv`
(`pip install -r API/requirements.txt`) — Foundation levels need fastapi/strawberry-graphql/grpcio/websockets/
protobuf, which the root `.venv` does not have; `api_python_bin()` prefers it, falling back to the root venv.
Running the editor's buffer never touches the real file: Go gets a scratch package under `API/.runtmp/` (deleted
after, same trick as `run_stdlib`'s Go path) so it still compiles inside the `dsapractice/api` module and its real
deps (gin, echo, coder/websocket); Python copies the level's sibling `*.py` files (some gRPC/Protobuf levels import
generated `*_pb2`/`*_pb2_grpc` stubs by bare name) into a scratch dir alongside the edited code. Verified end to
end: all 7 types' `/api/api-type` responses, a Python run with sibling pb2 imports (gRPC level 00), a Go run with
an external module dependency (REST lab 06, Gin), and that no `.runtmp` directory or file mutation is left behind.

## 7 · Adding a problem — the loop

```bash
# 1. Look up the row (topic, seq, lc, slug, title, diff)
grep "^01_arrays_hashing" tools/problems.tsv

# 2. Write 4 files: Py question+solution, Go question+solution
#    (Go needs: mkdir -p GoDSA/<topic>/NNN_<snake_slug>)

# 3. Verify
.venv/bin/python PyDSA/<topic>/NNN_slug_solution.py     # must print ALL PASSED
cd GoDSA && gofmt -l ./<topic>/ && go vet ./<topic>/NNN_slug \
  && go run ./<topic>/NNN_slug                          # must print ALL PASSED

# 4. Regenerate the index (progress is auto-detected from file existence)
.venv/bin/python tools/gen_curriculum.py
```

To add/change problems in the curriculum, edit `tools/problems.tsv` then regenerate.
**Never hand-edit `CURRICULUM.md`.**

---

## 8 · The web app

```bash
make app                 # http://127.0.0.1:8420
DSA_PORT=9000 make app     # custom port (kills whatever holds the port first)
# or, without killing anything:  DSA_PORT=9000 .venv/bin/python webapp/server.py
```

Stdlib-only Python server. No pip/npm, no build step.

- **Runs code for real**: Python via `.venv` (~17ms), Go via `go run` (~800ms incl.
  compile). Timeouts 15s/40s.
- **Persists to `webapp/data/progress.json`** — atomic writes, survives close/reboot.
  Separate drafts per language per problem. Delete the file to reset.
- Timer wired to the 25/40-min hint ladder; spaced repetition D+1→D+3→D+10→D+30;
  notes tab = pattern journal; per-topic progress rings; streak.
- **Reads problem files off disk; never writes to them.** New problems appear on reload
  automatically — nothing to re-import.
- Detects "written" by testing existence of `PyDSA/<topic>/<seq>_<snake_slug>_solution.py`.
- CodeMirror + marked load from cdnjs; offline degrades to a plain textarea.
- Binds `127.0.0.1` only. Executes user-typed code — Jupyter-equivalent trust model.

Key endpoints: `/api/bootstrap` `/api/problem` `/api/guide` `/api/run` `/api/format`
`/api/state` `/api/patch`

**Learning modules (15 Sep 2026).** System Design, Go/Py Engineering, AI Roadmap,
AI Library Guides and Agentic AI share one reader in `static/reader.js` + `reader.css`
(the DSA workspace in `app.js` is unchanged). Each module re-points `--accent` via
`#app[data-module]`, swaps the sidebar's topic tree for its own page list, and has a
landing page + reader (section checks, highlights, page themes, zoomable mermaid).
System Design is served as a 53-page collection (`/api/sd`, `/api/sd-doc`) instead of
one concatenated book. Reading state is `state.docs` in `progress.json`, written via
`/api/patch` with `{doc, docPatch}`.

---

## 9 · Gotchas (all hit and solved already)

| Gotcha | Detail |
|---|---|
| **zsh ≠ bash** | Unquoted `$VAR` does **not** word-split in zsh. `for t in $TOPICS` fails. Use an explicit list or an array. |
| **Go two-file rule** | See §4. Two `main()`s in one package won't compile; the stub file must have none. |
| **Go question.go needs a main for the app** | Server auto-appends an empty `func main(){}` to Go question buffers so they compile immediately in the editor. |
| **Verification greps `ALL PASSED`** | Solution files must print it or tooling reports FAIL. |
| **gofmt after writing Go** | Heredoc-written Go is often unformatted. Always `gofmt -l`, then `gofmt -w` if needed. |
| **Pre-existing lint** | `GoDSA/recursion/factorial/factorial.go` is unformatted (user's file, untouched). `go vet` also flags redundant `\n` in old harness `Println`s. Not ours. |
| **go.mod typo** | Module is `AI/DSA-Practive/GoDSA` ("Practive"). Harmless, left alone deliberately. |
| **Live vs snapshot iteration** | In sign-marking demos, iterate the live slice/list (values may already be negated) so the demo matches the documented trace. |

---

## 10 · Decisions already made — do not relitigate

- **Local web app, not a published Artifact.** An Artifact's CSP blocks Pyodide's WASM
  fetches and it has no filesystem access, so it could never run code or read the repo.
  User confirmed localhost is fine.
- **Problem files are the source of truth**; the app only writes `progress.json`.
- **TSV drives everything**; `CURRICULUM.md` is generated.
- **Legacy files stay put** — no migration into topic folders.
- **Go mandatory** for pointer/memory-heavy topics (linked lists, trees, tries,
  union-find); optional where it only teaches syntax (most DP, sliding window).
- Binary search, intervals, greedy, bit manipulation were **missing from the user's
  original plan** and were deliberately added.

---

## 11 · Lane — DECIDED 7 Sep 2026, do not relitigate

User chose **Python-first, full depth** (option 3 of the old §11) and
**DSA before system design**.

- All 288 problems in **Python at the full §5 quality bar**. This is the
  priority; it makes the web app usable end-to-end as fast as possible.
- **Go is a second pass**, EXCEPT the pointer/memory topics where Go teaches
  something Python cannot — `08_linked_list`, `10_trees`, `11_binary_search_tree`,
  `13_trie`, `15_advanced_graphs`. Write Go alongside Python for those.
- Topic 01 keeps its existing Go for 001–006; 007–012 are Python-only until the
  second pass. Half-Go topics are expected and fine — do not "fix" them.
- **Topic 27 (Classic Algorithms) was declared Python-only** (not a pointer/memory
  topic). **Superseded 24 Sep 2026:** `GoDSA/27_algorithms` and `28_recursion_backtracking` now exist as
  problem folders (stubs), and the user asked for a Go *topic guide* for every DSA topic, so both have one
  (27's is written from scratch; 28's covers all 25 problems). Problem 009 (Rand10 from Rand7) still has no Go folder.
- **System design is Phase 2**, after 288/288 Python. It currently lives only as
  prose in `master_dsa_plan.md` §7 and has no web-app surface. Leave it there.

## 12 · Next action

**Everything in this section above dated 7–10 Sep 2026 is historical** — topics
05–15, 21, 27 are now complete (see §6's table, which is current as of
14 Sep 2026). The one genuinely open item right now is:

**~~1. Topic 02, three open problems~~ — DONE 16 Sep 2026** (008–010 written, plus 011).
**Current state (16 Sep 2026): Python curriculum is 344/344.** Next work is the user's own practice
per `GOOGLE_INTERVIEW_PREP.md`; Go second pass remains optional (§11).

**Topic 28 · Recursion Mastery is now 25/25 ✅ Python, completed 14 Sep 2026**
(added after the original 288-problem plan — see §6's note on why the total
is now 313, not 288). All 25 question+solution pairs verified `ALL PASSED`:
001–006 Easy, 007–020 Medium, 021–025 Hard — each file's "UNDERSTANDING THE
PROBLEM" section names the specific new recursive shape it introduces
relative to its neighbors (index-range two-pointer, linked-list pointer
rewiring, tree branching, "return a pair" combine patterns, BST-property
one-sided descent, range-split memoized DP). 006 (Pascal's Triangle II),
which had been left as a question-only stub from an earlier interrupted
session, now has its solution file too.

Confirm the full repo still passes before adding anything new:

```bash
for f in PyDSA/*/[0-9]*_solution.py; do
  printf '%-64s %s\n' "$(basename $f)" "$(.venv/bin/python $f 2>&1 | tail -1)"
done
```

While fixing 021–025, two pre-existing bugs were found and fixed in
`PyDSA/28_recursion_backtracking/001_..._solution.py` (left over from
whichever session first wrote it): the recursion-depth demo loop called the
naive O(num)-stack version on `num=1000` and `10000`, exceeding Python's
default 1000-frame recursion limit uncaught (fixed: loop now uses `987`); and
a fabricated expected value `(1000000, 25)` in `CASES` was wrong — the real
answer is 26, confirmed both by running the rule-following recursion and by
the independent bit-trick formula. Caught only by actually running the file,
per this repo's standing rule (§6, "A note on the runtime demos").
