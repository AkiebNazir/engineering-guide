# Repo restructure checklist

Findings from a full repo audit (8 parallel module reviews). Grouped by module,
structural/broken-link fixes first within each module, then content-depth gaps.
Unchecked = not yet done.

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
      <abbr title="Large Language Model">LLM</abbr> systems, message queue, ranked feed, live streaming, maps/ETA, CDN,
      experimentation, video conferencing, social graph, lock service.
- [ ] Link `best_practices/` (8 files, SOLID/GoF/architectural
      patterns/anti-patterns) into the module's own navigation (README,
      playbook, or catalog) — it's currently unreachable except by browsing
      the directory, which contradicts README.md:14's claim that this content
      "lives in the separate Software Design module, not here." Either fold
      it into the learning path with a stated rationale, or move it out.

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

## <abbr title="Artificial Intelligence">AI</abbr>-road-map/

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
      currently only mention vLLM/TGI/TensorRT-<abbr title="Large Language Model">LLM</abbr> and generic quantization.
- [ ] Add coverage of computer-use / GUI-driving agents — only browser agents
      (136) and code agents (135) exist today; screen/GUI agents are a
      standard agentic pattern with no treatment.
- [ ] Consider whether the two reallocated day-slots (from the duplicate
      merges above) should go toward the reasoning-model and modern-serving
      gaps rather than staying padding.

## Agentic-<abbr title="Artificial Intelligence">AI</abbr>/

- [ ] Bring Module 7 (Multi-Agent Orchestration & <abbr title="Model Context Protocol">MCP</abbr>) up to the depth of
      Modules 1–5 — currently the thinnest file in the whole module (582
      words, no code, no diagrams, no worked example) despite covering the
      most central "agentic" topic; Module 2 (single-agent internals) is
      6,197 words by comparison.
- [ ] Bring Module 6 and Module 8 up to a comparable depth to 1–5, or
      explicitly rescope them in the README as lighter supporting-infra
      modules rather than presenting all 8 as equal "core modules."
- [ ] Add evaluation/observability content — zero mentions anywhere of
      "observability," "guardrail," "monitoring," or "red team"; only passing
      mentions of evaluation/hallucination/safety. The module's stated arc
      ("all the way to advanced Agentic <abbr title="Artificial Intelligence">AI</abbr> architectures") doesn't currently
      reach deployment/ops.
- [ ] Add a standalone deployment/production module or section — rate
      limiting, retries, rollout, prompt versioning for a deployed agent
      aren't addressed anywhere (Module 8 touches infra but not this).

## <abbr title="Artificial Intelligence">AI</abbr>-Libraries-Guides/

- [ ] Add a top-level README/index — currently none; 25 standalone guides
      with no navigational scaffolding or suggested order.
- [ ] Add a data visualization library guide (matplotlib and/or seaborn) —
      glaring omission for an <abbr title="Machine Learning">ML</abbr> curriculum; referenced nowhere except in
      passing in `04_xgboost.md`.
- [ ] Add a general-purpose <abbr title="Large Language Model">LLM</abbr>/agent evaluation framework guide (e.g.
      DeepEval, promptfoo) — Ragas (25) only covers <abbr title="Retrieval-Augmented Generation">RAG</abbr>-specific metrics, not
      general chat/agent output evaluation.
- [ ] Add a guardrails/safety library guide (e.g. Guardrails <abbr title="Artificial Intelligence">AI</abbr>, NeMo
      Guardrails, <abbr title="Large Language Model">LLM</abbr> Guard) — absent despite deep fine-tuning/serving
      coverage elsewhere in the module.
- [ ] Add a sentence-transformers (embedding models) guide — embeddings are
      central to every <abbr title="Retrieval-Augmented Generation">RAG</abbr> guide in this module (LangChain, LlamaIndex,
      FAISS/Chroma/Qdrant) but the embedding-model library itself is never
      covered directly.
- [ ] Add a Streamlit or Gradio guide — no covered way to quickly demo/serve
      a model or agent as an app.
- [ ] Consider trimming one of the three vector-DB guides (FAISS/ChromaDB/
      Qdrant, currently back-to-back) to make room for the gaps above.

## <abbr title="Application Programming Interface">API</abbr>/

- [ ] Add OIDC (OpenID Connect) coverage — OAuth2 and JWT are covered well in
      `Fundamentals/03`, but OIDC (the identity layer used for SSO) has zero
      mentions anywhere.
- [ ] Add a hands-on <abbr title="Application Programming Interface">API</abbr> gateway lab (e.g. Kong/Envoy, rate-limiting at the
      edge) — "gateway" currently appears only in prose/comparison tables,
      never as an exercise.
- [ ] Add contract testing (Pact/consumer-driven contracts) for REST and
      GraphQL specifically — currently only Protobuf/gRPC (`buf breaking`)
      and SOAP have contract-testing content.
- [ ] Confirm/build out GraphQL federation as a hands-on lab, not just prose
      in `GraphQL/Theory.md` — no Apollo Federation/schema-stitching exercise
      currently exists.
- [ ] Add an end-to-end observability lab (e.g. OpenTelemetry tracing +
      metrics instrumented through a real <abbr title="Application Programming Interface">API</abbr>) — currently only one writeup
      (`Fundamentals/03` §11) and passing mentions elsewhere, no hands-on lab.
- [ ] Extend Protobuf's Go Foundation track from level 06 up to parity with
      Python's 14 levels (oneof, protoc-vs-buf, generated-code-in-real-program,
      cross-language interop, capstone, bridge-to-gRPC, wire-format bonus).
- [ ] Fix the README's REST lab count for Go (says 5 labs; Go actually has 7,
      including Gin/Echo framework examples) — not a gap, just an inaccurate
      claim.

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

- [ ] Add JSON/JSONB column type and querying as its own named topic (common
      in modern Postgres senior interviews) — currently only implied via
      schema-design tradeoffs, not called out directly.
- [ ] Add coverage of finding slow queries in production at scale (e.g.
      `pg_stat_statements`) — file 10 covers `EXPLAIN` but not how you'd find
      what to `EXPLAIN` in the first place.
- [ ] Optional: expand recursive-CTE depth/materialization-vs-inlining beyond
      the one example currently in file 08.

## NoSQL/

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

- [ ] Optional: add an explicit CAP-theorem framing section to file 03 —
      Paxos/Raft/TrueTime are covered, but the CAP framing itself currently
      lives only in `SystemDesign/building_blocks/10_distributed_systems_theory.md`,
      so a reader using only this module would miss it.
- [ ] Optional: add a short security-fundamentals file (authn/authz,
      encryption, OWASP) or an explicit pointer to
      `SystemDesign/building_blocks/14_security.md` — CSFundamentals
      currently has zero security content of its own.

---

## Already confirmed fine — no action needed

<abbr title="Application Programming Interface">API</abbr>'s core structure, SQL's and NoSQL's core structure, CSFundamentals'
core scope, PyStdLib/GoStdLib symmetry, PyDSA's 28-topic taxonomy and its
question/solution pairing, <abbr title="Artificial Intelligence">AI</abbr>-road-map's day-numbering scaffolding and
README-to-disk consistency (outside the two duplicate pairs above).
