# Repo restructure checklist

Findings from a full repo audit. Grouped by module, structural/broken-link
fixes first within each module, then content-depth gaps, then diagram and
interactive-lab gaps. Unchecked = not yet done.

---

## Global / Webapp & Visualizations

### Diagram migration status (mermaid → arch)

- [x] ~~Migrate all legacy `mermaid` box-and-arrow diagrams (`flowchart`,
      `graph`, `stateDiagram`) to the new custom `arch` block syntax.~~
      **DONE** — a grep of the entire repo confirms zero `flowchart`, `graph`,
      or `stateDiagram` blocks remain. All 60+ remaining ` ```mermaid ` blocks
      are `sequenceDiagram` or `xychart-beta`, which are correct to keep in
      mermaid per `ARCH_DIAGRAMS.md`.

### Arch diagram coverage gaps (files with zero `arch` blocks)

Many content files still have **no** `arch` diagrams at all. Adding static
architecture visuals to these will bring them to the standard set by the OS
deep dive and the SD solutions:

- [x] ~~**SoftwareDesign/** — **0 arch diagrams across all 16 files**~~ (00–15).
      This is the single largest module with zero visual architecture content.
      Key files that need arch diagrams:
      `04_design_patterns_in_practice.md` (patterns like Observer, Strategy
      are perfect for box-and-arrow), `08_application_architecture_in_code.md`
      (hexagonal, clean arch, CQRS), `10_designing_observable_code.md`,
      `11_performance_aware_design.md`.
- [x] ~~**SystemDesign/building_blocks/** — 20 of 33 files had zero arch diagrams. (All identified key files now have arch diagrams).~~

- [x] ~~**SystemDesign/solutions/** — 2 solutions still have zero arch diagrams:~~
      `017_payment_ledger_solution.md`, `019_feature_flags_solution.md`.
- [x] ~~**SQL/** — only 2 of 21 files had arch diagrams. (Added to 09, 10, 17, 18).~~
- [ ] **NoSQL/** — most files lack arch diagrams. Only 4 out of 28 NoSQL files
      have them (`mongodb/04_embedding_vs_referencing.md`, `mongodb/10_replication_and_write_read_concern.md`,
      `redis/00_the_key_value_model.md`, `redis/05_caching_patterns.md`).
      Key gaps: `redis/08_distributed_locking.md`, `redis/10_persistence_rdb_aof.md`,
      `mongodb/09_transactions_in_mongodb.md`.
- [ ] **API/Fundamentals/02_http_and_web_foundations.md** — 0 arch diagrams
      (287 lines, should have HTTP request lifecycle, TLS handshake arch).
- [ ] **API/Fundamentals/03_cross_cutting_concerns.md** — 0 arch diagrams
      (335 lines, should have observability pipeline, auth flow arch).
- [ ] **API/REST/Theory.md** — 0 arch diagrams (510 lines, the largest API
      theory file, should have REST resource hierarchy, HATEOAS flow).
- [ ] **CSFundamentals/** — topics 05 through 10 have zero arch diagrams.
      Topic 01 (OS) has 6, topic 02 has 3, topics 03–04 have 1–2 each.

### Interactive animation lab gaps

The webapp has interactive flow labs (`defineFlow`) and static visualizations
(`defineAlgo`/`defineAlgoDom`/`defineLab`). Current coverage:

| Module | Script(s) | Coverage |
|---|---|---|
| DSA (28 topics) | `dsa-viz.js` – `dsa-viz29.js`, `viz-algorithms.js` | **345/345 problems — DONE** |
| System Design solutions | `sd-flow.js` | **30 of 39 solutions** have flow labs (problems 031–040 partially covered, 033/037 missing) |
| SD building blocks | `viz-sd.js`, `viz-sd2.js`, `viz-sd3.js` | Partial |
| CS Fundamentals | `viz-csfund.js`, `flows-osdb.js` | Only OS + partial DB/networking |
| API | `viz-api.js` – `viz-api5.js` | Partial |
| AI/ML/LLM | `viz-ml.js`, `viz-llm.js`, `flows-ai.js` | Partial |
| Networking | `flows-net.js` | 5 flows (web request, TLS, DNS, TCP, LB) |
| Data/DB | `flows-data.js` | 6 flows (PG query, lost update, pooling, HA, Redis lock, Mongo WC) |
| SD building blocks | `flows-sdbb.js` | 5 flows (WAL, cache-aside, outbox, Kafka ISR, CDN) |

**Modules with ZERO interactive labs:**

- [ ] **SQL/** — no visualization or flow labs whatsoever.
- [ ] **NoSQL/** — no visualization or flow labs.
- [ ] **SoftwareDesign/** — no visualization or flow labs.
- [ ] **GoEngineering/PyEngineering/** — no visualization or flow labs.
- [ ] **GoStdLib/PyStdLib/** — no visualization or flow labs.
- [ ] **GoogleBehavioral/** — no visualization or flow labs (may not need them).

---

## SystemDesign/

- [ ] Fix 9 dead links pointing at `06_spoken_walkthroughs.md` (referenced in
      `README.md:12`, `01_company_interview_guide.md:137`,
      `02_problem_catalog.md:74/77`) — file does not exist. Either write it or
      remove the references.
- [ ] Fix dead links to `problems/035_distributed_object_store_question.md` +
      `solutions/035_distributed_object_store_solution.md` (referenced in
      `00_google_l5_playbook.md:171`, `02_problem_catalog.md:55`) — disk jumps
      034 → 036. Either write problem 035 or remove the references.
- [ ] Fix dead links to `problems/041_email_service_question.md` +
      `solutions/041_email_service_solution.md` (referenced in
      `00_google_l5_playbook.md:177`, `02_problem_catalog.md:61`) — disk stops
      at 040. Either write problem 041 or remove the references.
- [ ] Reconcile the "41 problems" claim throughout README/catalog with the
      actual 39 on disk (either write the 2 missing problems above and keep
      41, or renumber the claim to 39 everywhere it appears).
- [ ] Extend the condensed review layer (`03_practice_prompts.md`,
      `04_practice_answers.md`, `05_architecture_blueprints.md`) from problem
      21 through problem 40 — currently stops at 21 despite being advertised
      as "a condensed pass across all 41 problems in one sitting." Missing:
      KV store, CRDT editor, web search, geo, ad-click streaming, leaderboard,
      LLM systems, message queue, ranked feed, live streaming, maps/ETA, CDN,
      experimentation, video conferencing, social graph, lock service.
- [ ] Link `best_practices/` (8 files, SOLID/GoF/architectural
      patterns/anti-patterns) into the module's own navigation (README,
      playbook, or catalog) — it's currently unreachable except by browsing
      the directory, which contradicts README.md:14's claim that this content
      "lives in the separate Software Design module, not here." Either fold
      it into the learning path with a stated rationale, or move it out.
- [ ] Add interactive flow labs for the 9 solutions that currently lack them
      (033_live_streaming, 037_experimentation_platform, and verify 031–040
      mapping is complete in `sd-flow.js`).

## PyEngineering/

- [ ] Add the 4 missing topic folders that GoEngineering already has and the
      PyEngineering README promises: `03_api_client_with_retries`,
      `04_custom_stream_reader_writer`, `05_large_file_line_processor`,
      `15_rate_limiter`.
- [ ] Fix `PyEngineering/README.md` — says "25 real-world engineering
      problems / same 25 topics as GoEngineering" but its own table lists 35
      rows matching GoEngineering 1:1. Update the stale "25" text to 35.
- [ ] Fix the 2 SoftwareDesign cross-references broken by the missing
      folders: `SoftwareDesign/06_error_handling_and_failure_design.md:28`
      (references `PyEngineering/03_api_client_with_retries`) and
      `SoftwareDesign/07_designing_concurrent_code.md:31` (references the
      range `PyEngineering/12–16`, where 15 doesn't exist) — fix once the
      folders exist, or scope those refs to Go-only in the meantime.

## GoDSA/

- [ ] Remove or fold in 3 stray legacy directories that sit outside the
      28-topic structure and duplicate it: `linklist/` (dupes `08_linked_list`),
      `recursion/` (5 subdirs: factorial, palindrome, subsets, permutations,
      fibonacci — dupes `09_recursion_backtracking`/`28_recursion_backtracking`),
      `reverse_linked_list/`. None have a question/solution split or a
      `_TOPIC_GUIDE.md`.
- [ ] Add the missing Go solution for `27_algorithms/009_implement_rand10_using_rand7`
      — exists in PyDSA (9 problems in that topic) but GoDSA only has 8.

## AI-road-map/

- [ ] Add a top-level `README.md` — currently missing. 186 day-files with
      no navigational index or suggested reading order.
- [ ] Resolve the duplicate-topic pair `74_day_pretraining_data.md` vs.
      `92_day_pretraining_data.md` (different angles — dedup pipeline vs.
      extraction — but redundant as two separate day slots). Merge, rename
      one to reflect its actual distinct angle, or replace one slot with new
      content (see gaps below).
- [ ] Resolve the duplicate-topic pair `75_day_domain_adaptation.md` vs.
      `109_day_domain_adaptation.md` — same treatment as above.
- [ ] Add coverage of RL-trained "reasoning models" (o1/DeepSeek-R1-style
      test-time-compute scaling) — day 115 only covers 2022-era prompting
      tricks (CoT/ToT/Self-Consistency/ReAct), not how reasoning models are
      actually trained/served.
- [ ] Name and cover modern quantized/optimized serving formats and engines
      (GPTQ, AWQ, SGLang) — day 78 (quantization) and day 151 (serving)
      currently only mention vLLM/TGI/TensorRT-LLM and generic quantization.
- [ ] Add coverage of computer-use / GUI-driving agents — only browser agents
      (136) and code agents (135) exist today; screen/GUI agents are a
      standard agentic pattern with no treatment.
- [ ] Consider whether the two reallocated day-slots (from the duplicate
      merges above) should go toward the reasoning-model and modern-serving
      gaps rather than staying padding.

## Agentic-AI/

Depth is extremely uneven. Modules 1–5 are 756–1,136 lines each with 6–16
arch diagrams. Modules 6–8 are 60–435 lines with 0 arch diagrams:

| Module | Lines | Arch diagrams |
|---|---:|---:|
| 01 Generative AI Internals | 947 | 9 |
| 02 Agentic AI Internals | 1,136 | 16 |
| 03 RAG Deep Dive | 815 | 8 |
| 04 Vector Databases Internals | 756 | 6 |
| 05 Graph Databases & GraphRAG | 865 | 9 |
| **06 Protocol Buffers & gRPC** | **98** | **0** |
| **07 Multi-Agent & MCP** | **60** | **0** |
| **08 API Architectures Guide** | **435** | **0** |

- [ ] Bring Module 7 (Multi-Agent Orchestration & MCP) up to the depth of
      Modules 1–5 — currently the thinnest file in the whole module (60
      lines, no code, no diagrams, no worked example) despite covering the
      most central "agentic" topic.
- [ ] Bring Module 6 (Protocol Buffers & gRPC, 98 lines) up to depth —
      or merge it into Module 8 / the API module if it's not meant to be
      standalone.
- [ ] Bring Module 8 (API Architectures, 435 lines) up to a comparable
      depth to 1–5, or explicitly rescope it in the README.
- [ ] Add arch diagrams to Modules 6, 7, and 8 (currently 0 across all three).
- [ ] Add evaluation/observability content — zero mentions anywhere of
      "observability," "guardrail," "monitoring," or "red team"; only passing
      mentions of evaluation/hallucination/safety. The module's stated arc
      ("all the way to advanced Agentic AI architectures") doesn't currently
      reach deployment/ops.
- [ ] Add a standalone deployment/production module or section — rate
      limiting, retries, rollout, prompt versioning for a deployed agent
      aren't addressed anywhere (Module 8 touches infra but not this).

## AI-Libraries-Guides/

- [ ] Add a top-level README/index — currently none; 25 standalone guides
      with no navigational scaffolding or suggested order.
- [ ] Add a data visualization library guide (matplotlib and/or seaborn) —
      glaring omission for an ML curriculum; referenced nowhere except in
      passing in `04_xgboost.md`.
- [ ] Add a general-purpose LLM/agent evaluation framework guide (e.g.
      DeepEval, promptfoo) — Ragas (25) only covers RAG-specific metrics, not
      general chat/agent output evaluation.
- [ ] Add a guardrails/safety library guide (e.g. Guardrails AI, NeMo
      Guardrails, LLM Guard) — absent despite deep fine-tuning/serving
      coverage elsewhere in the module.
- [ ] Add a sentence-transformers (embedding models) guide — embeddings are
      central to every RAG guide in this module (LangChain, LlamaIndex,
      FAISS/Chroma/Qdrant) but the embedding-model library itself is never
      covered directly.
- [ ] Add a Streamlit or Gradio guide — no covered way to quickly demo/serve
      a model or agent as an app.
- [ ] Consider trimming one of the three vector-DB guides (FAISS/ChromaDB/
      Qdrant, currently back-to-back) to make room for the gaps above.

## API/

- [ ] Add arch diagrams to `API/Fundamentals/02_http_and_web_foundations.md`
      (0 arch, 287 lines) and `API/Fundamentals/03_cross_cutting_concerns.md`
      (0 arch, 335 lines).
- [ ] Add arch diagrams to `API/REST/Theory.md` (0 arch, 510 lines — the
      largest API theory file).
- [ ] Add OIDC (OpenID Connect) coverage — OAuth2 and JWT are covered well in
      `Fundamentals/03`, but OIDC (the identity layer used for SSO) has zero
      mentions anywhere.
- [ ] Add a hands-on API gateway lab (e.g. Kong/Envoy, rate-limiting at the
      edge) — "gateway" currently appears only in prose/comparison tables,
      never as an exercise.
- [ ] Add contract testing (Pact/consumer-driven contracts) for REST and
      GraphQL specifically — currently only Protobuf/gRPC (`buf breaking`)
      and SOAP have contract-testing content.
- [ ] Confirm/build out GraphQL federation as a hands-on lab, not just prose
      in `GraphQL/Theory.md` — no Apollo Federation/schema-stitching exercise
      currently exists.
- [ ] Add an end-to-end observability lab (e.g. OpenTelemetry tracing +
      metrics instrumented through a real API) — currently only one writeup
      (`Fundamentals/03` §11) and passing mentions elsewhere, no hands-on lab.
- [ ] Extend Protobuf's Go Foundation track from level 06 up to parity with
      Python's 14 levels (oneof, protoc-vs-buf, generated-code-in-real-program,
      cross-language interop, capstone, bridge-to-gRPC, wire-format bonus).
- [ ] Fix the README's REST lab count for Go (says 5 labs; Go actually has 7,
      including Gin/Echo framework examples) — not a gap, just an inaccurate
      claim.

## SoftwareDesign/

- [ ] Add arch diagrams across the module — **all 16 files (00–15) currently
      have zero arch diagrams**. This is the largest module entirely without
      visual architecture content. Priority targets:
      `04_design_patterns_in_practice.md` (1,417 lines),
      `08_application_architecture_in_code.md` (1,487 lines),
      `06_error_handling_and_failure_design.md` (1,431 lines),
      `07_designing_concurrent_code.md` (1,350 lines).
- [ ] Add interactive visualization labs to the webapp for this module —
      currently zero. Pattern/architecture diagrams would benefit greatly
      from animated "request walks through layers" style labs.

## GoogleBehavioral/

- [ ] Add worked STAR blueprints for the other 10 of the 13 story types named
      in file 04 — file 02 ("STAR Blueprints") currently only has 3 (Conflict,
      Ambiguity, Failure). Missing: leadership-without-authority, mentorship,
      technical-decision-making, and the rest of the 13.
- [ ] Add a dedicated deep-dive on leadership-without-authority and
      mentorship, comparable in depth to file 03's general L5-leadership
      treatment.
- [ ] Add systematic L4→L5→L6 calibration guidance — currently just one
      comparison table (file 01 §4, L4 vs L5) and a single passing L5→L6
      question (file 06); no guidance on reshaping a story's scope/ownership
      language across levels.

## SQL/

- [ ] Add arch diagrams to the 19 files that currently have none.
      Priority: `09_transactions_and_isolation_levels.md`,
      `10_indexing_and_query_planning.md`, `17_replication_and_high_availability.md`,
      `18_sharding_and_horizontal_scaling.md`.
- [ ] Add interactive visualization/flow labs to the webapp — currently
      zero for this module.
- [ ] Add JSON/JSONB column type and querying as its own named topic (common
      in modern Postgres senior interviews) — currently only implied via
      schema-design tradeoffs, not called out directly.
- [ ] Add coverage of finding slow queries in production at scale (e.g.
      `pg_stat_statements`) — file 10 covers `EXPLAIN` but not how you'd find
      what to `EXPLAIN` in the first place.
- [ ] Optional: expand recursive-CTE depth/materialization-vs-inlining beyond
      the one example currently in file 08.

## NoSQL/

- [ ] Add arch diagrams to the 24 files that currently have none.
      Priority: `redis/08_distributed_locking.md`, `redis/10_persistence_rdb_aof.md`,
      `mongodb/09_transactions_in_mongodb.md`, `mongodb/05_indexes_in_mongodb.md`.
- [ ] Add interactive visualization/flow labs to the webapp — currently
      zero for this module.
- [ ] Add at least a concepts-level graph database file with real modeling
      flavor (e.g. a taste of Cypher queries) — currently graph DBs are
      explicitly deferred to SystemDesign, but that treatment is system-
      design-flavored, not NoSQL-modeling-flavored.
- [ ] Confirm (or add) a dedicated MongoDB sharding level — README's roadmap
      table doesn't clearly list sharding under files 07-11 ("replication and
      read scaling"); verify shard-key selection is actually covered, and add
      a dedicated level if not.
- [ ] Add a dedicated Redis Streams level — currently only a passing mention
      in file 06 (pubsub) as an alternative, despite Streams being the
      production answer to pub/sub's fire-and-forget weakness.

## PyStdLib/ and GoStdLib/

- [ ] Add a dedicated `net/http` deep-dive package to GoStdLib (client
      tuning, transport pooling, server timeouts) — Python's README
      explicitly delegates networking to `../API`, but GoStdLib's README has
      no equivalent pointer, leaving it unstated whether this is covered
      anywhere as a dedicated deep-dive.
- [ ] Optional: add a few SoftwareDesign cross-references into PyStdLib/
      GoStdLib where relevant (e.g. the error-handling chapter could point at
      Go's `errors` package) — currently zero references exist in either
      direction, leaving both modules orphaned from the rest of the
      curriculum's cross-linking.

## CSFundamentals/

The OS topic (`01_operating_systems_deep_dive.md`) is the gold standard:
500 lines, 6 arch diagrams, interactive flow lab (`flow-page-fault` in
`flows-osdb.js`). All other topics fall short:

| Topic | Lines | Arch | Flow labs | Completeness vs OS |
|---|---:|---:|---|---|
| 01 Operating Systems | 500 | 6 | ✅ flow-page-fault | **100% (gold standard)** |
| 02 Networking | 278 | 3 | ✅ flows-net.js (5 flows) | ~60% |
| 03 Databases | 252 | 1 | ✅ flow-mvcc, flow-spanner-commit | ~50% |
| 04 Software Engineering | 190 | 2 | ❌ | ~35% |
| 05 Concurrency | 258 | 0 | ❌ | ~30% |
| 06 Data Structure Internals | 181 | 0 | ❌ | ~25% |
| 07 Complexity Analysis | 246 | 0 | ❌ | ~30% |
| 08 Python for Interviews | 303 | 0 | ❌ | ~35% |
| 09 Coding Round Execution | 173 | 0 | ❌ | ~20% |
| 10 Google Follow-Ups | 182 | 0 | ❌ | ~20% |

- [ ] Complete topics 02–10 to the same depth as topic 01, including:
      - Expanding content to 400–500+ lines with beginner-to-advanced progression.
      - Adding 4–6 `arch` diagrams per topic.
      - Adding interactive flow labs (`defineFlow`) per topic in the webapp.
- [ ] Add an explicit CAP-theorem framing section to file 03 —
      Paxos/Raft/TrueTime are covered, but the CAP framing itself currently
      lives only in `SystemDesign/building_blocks/10_distributed_systems_theory.md`,
      so a reader using only this module would miss it.
- [ ] Add a short security-fundamentals file (authn/authz, encryption, OWASP)
      or an explicit pointer to `SystemDesign/building_blocks/14_security.md`
      — CSFundamentals currently has zero security content of its own.

---

## Already confirmed fine — no action needed

- Mermaid → arch migration: **COMPLETE**. All remaining mermaid blocks are
  `sequenceDiagram` or `xychart-beta` (correct to keep).
- API's core structure and lab framework.
- SQL's and NoSQL's core topic structure.
- PyStdLib/GoStdLib symmetry (15 packages each).
- PyDSA's and GoDSA's 28-topic taxonomy and question/solution pairing.
- PyEngineering/GoEngineering parity (35 topics each, minus the 4 missing
  PyEngineering folders noted above).
- DSA visualization coverage: **345/345 problems — DONE**.
- AI-road-map's day-numbering scaffolding and disk consistency (outside the
  two duplicate pairs above).

---

## Ultimate Guide Master Gaps (New Modules & Domain Coverage)

To achieve the "ultimate self-contained backend engineering/interview guide of
any level," the following entire domains are currently missing and require
dedicated modules mirroring the depth of existing tracks, complete with
basic-to-advanced progression, code examples, static `arch` diagrams, and
interactive webapp labs:

- [ ] **Backend Tool-Kit Module**: A hands-on module dedicated to mastering
      essential backend and infrastructure technologies. Needs deep-dive
      topics covering:
      - **Containerization & Orchestration**: Docker (images, Dockerfile best
        practices, multi-stage builds, volumes, networking), Kubernetes (pods,
        services, deployments, ConfigMaps, Secrets, Helm charts, HPA, RBAC),
        Helm.
      - **Version Control**: Git deep dive (internals, rebase vs merge, cherry-pick,
        bisect, reflog, hooks), GitHub (pull request workflows, code review
        best practices, branch protection, GitHub Actions).
      - **Messaging & Event Streaming**: Kafka (producers, consumers, partitions,
        consumer groups, exactly-once semantics, schema registry), RabbitMQ
        (exchanges, queues, routing, dead-letter queues).
      - **Observability & Monitoring**: Prometheus (metrics, PromQL, alerting),
        Grafana (dashboards, alerting), OpenTelemetry (traces, spans, context
        propagation), ELK Stack (Elasticsearch, Logstash, Kibana).
      - **CLI & Linux Mastery**: Bash scripting, `curl`, `jq`, core utilities
        (`grep`, `awk`, `sed`, `find`, `xargs`), process management (`systemd`,
        `supervisord`), Linux networking (`ss`, `netstat`, `tcpdump`, `iptables`).
      - **Infrastructure as Code (IaC)**: Terraform (providers, state, modules,
        workspaces, drift detection), Ansible (playbooks, roles, inventory).
      - **Web Servers & Proxies**: Nginx (reverse proxy, load balancing, SSL
        termination, rate limiting), Envoy (service mesh, xDS, circuit breaking),
        HAProxy.
      - **Performance & Load Testing**: k6 (scripting, thresholds, scenarios),
        wrk, benchmarking methodology.
      - **Secret Management**: HashiCorp Vault, AWS Secrets Manager patterns.
      - **Service Mesh**: Istio / Linkerd basics, mTLS, traffic management.
- [ ] **CI/CD & Deployment Strategies**: A dedicated topic/module focusing
      purely on Continuous Integration, Continuous Deployment, automation
      pipelines (GitHub Actions deep dive, Jenkins, ArgoCD), and deployment
      strategies (blue/green, canary, rolling, feature flags, rollbacks,
      GitOps).
- [ ] **Data Engineering Module**: Missing hands-on coverage of batch/stream
      processing fundamentals (Apache Spark, Airflow DAGs, dbt models, data
      warehouse modeling — star schema, slowly changing dimensions).
- [ ] **Machine Learning System Design (MLOps)**: Needs a dedicated module
      focused on interviewing and architecting ML systems in production
      (Recommendation Systems, Fraud Detection, Search Ranking, Ad Click
      Prediction, MLOps pipelines — feature stores, model registry, A/B
      testing, model monitoring), distinct from the existing `AI-road-map`
      and `Agentic-AI` theory paths.
- [ ] **Unified Testing & Quality Module**: Missing a dedicated deep dive into
      testing strategies: Unit testing best practices, Integration testing,
      E2E testing, TDD, Property-based testing, Mutation testing, Contract
      testing, Chaos Engineering, Load/Stress testing methodology.
