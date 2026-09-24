# Archive

Superseded material, kept for history rather than deleted outright. Nothing in
here is loaded by the webapp or referenced by the active curriculum.

- **`scripts/`** — one-off content-generation and webapp-patching scripts
  (`add_topic_*.py`, `patch_*.py`, `fix_*`, `inject_viz.py`, `rewrite_viz.py`).
  Each already ran; their output is the committed content/code they targeted.
  Kept in case a future similar migration wants a starting template.
- **`docs/google_prep_plan.md`** — the original Google L5 syllabus. Audited
  against the repo on 16 Sep 2026 (see `CONTEXT.md` §6); every gap it named
  was closed, and `GOOGLE_INTERVIEW_PREP.md` is the up-to-date, file-mapped
  successor. Archived rather than deleted because `GOOGLE_INTERVIEW_PREP.md`
  still names it as its source.
- **`docs/RAG.md`** — standalone RAG notes, superseded by the structured
  `Agentic-AI/` module and not referenced from anywhere else in the repo.

Not archived, despite looking similar at a glance:
- **`SYSTEM_DESIGN_GUIDE.md`** (repo root) — still actively served by
  `webapp/server.py` as the System Design module's "Complete guide" doc.
- **`master_dsa_plan.md`** (repo root) — still cited as the source of the
  hint ladder and 13-week schedule in `webapp/static/app.js`,
  `webapp/README.md`, and `CSFundamentals/07_complexity_analysis_deep_dive.md`.
