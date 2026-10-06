# Running and Deploying the Guide

The web app runs in two modes from the same front end (`webapp/static/`):

| | Local app (`make app`) | Static site (`make build`) |
|---|---|---|
| What it is | `webapp/server.py`, Python standard library, on `127.0.0.1` | A plain folder, `dist/`, of HTML, JS, CSS and pre-rendered JSON |
| Reading every module, visualizers, labs, diagrams | Yes | Yes |
| **Run** / **gofmt**: DSA problems, standard-library levels | Yes (Python and Go on your machine) | Yes: Python in the browser (Pyodide, WebAssembly), Go on the [Go Playground](https://go.dev/play) |
| **Run**: Go/Py Engineering, Software Design LLD, API labs | Yes | No (they need the repo's files and packages); the editor says to run it locally |
| Progress (status, drafts, notes, timers, reviews) | `webapp/data/progress.json` | The visitor's browser (`localStorage`), per device |
| Where it can run | Your machine only (it executes code you type) | Any static host or container platform |

The static build is safe to publish: it contains no server, executes nothing on the host,
and never includes your `progress.json`.

### Running code on the static site

`webapp/static/browser-run.js` stands in for the server's `/api/run`, `/api/stdlib-run` and
`/api/format` when the app is a static build:

- **Python** runs in the visitor's browser: [Pyodide](https://pyodide.org) (CPython compiled
  to WebAssembly) in a Web Worker, `webapp/static/py-worker.js`. The runtime (about 10 MB)
  downloads from the jsDelivr CDN on the first **Run** and is cached after that. A run
  that exceeds the time limit has its worker terminated, so an infinite loop never
  freezes the page. Output matches `python main.py`, with two browser limits: timers are
  coarsened to ~0.1 ms (benchmark timings are rougher), and recursion that passes through
  C code (`@functools.cache`, `__repr__`, `map`) stops at a few hundred levels with a
  `RecursionError`. Plain recursion is not limited.
- **Go** is sent to the Go Playground (`play.golang.org/compile`, `/fmt`), which accepts
  requests from any site. The code runs on Google's servers; the Playground's clock is
  simulated, so `time.Since()` measures nothing there.

---

## Build the static site

Needs Python 3.10 or newer. No packages, no Node, no internet.

```bash
make build                                   # → dist/
make preview                                 # build, then serve on http://127.0.0.1:8000
python3 webapp/build_static.py --out site    # any other output folder
```

`dist/` is self-contained: every URL in it is relative and routing is hash-based
(`#/dsa`, `#/p/…`), so it works at a domain root (`https://guide.example.com/`) and
under a sub-path (`https://<user>.github.io/engineering-guide/`) alike, with no
rewrite rules.

How it works: `build_static.py` copies `webapp/static/`, then asks `server.py`'s own
`api_get()` for every `GET /api/*` answer the client can request and writes each one to
`dist/data/`. `dist/config.js` switches the client to read those files. Because the
answers come from the same function the local server uses, the two modes always show the
same content. Adding a page, a problem or a module needs no change to the build, as long
as it is served through an existing endpoint; a new endpoint is added to
`client_requests()` in `build_static.py`.

---

## GitHub Pages (set up)

`.github/workflows/deploy.yaml` builds and deploys on every push to `main`, and can be run
by hand (Actions → Deploy to GitHub Pages → Run workflow). Pull requests run the build
only, so a change that breaks it is caught before merge.

One-time setup: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
The site is then at `https://<user>.github.io/<repo>/`.

---

## Other static hosts

Every static host needs the same two settings:

| Setting | Value |
|---|---|
| Build command | `python3 webapp/build_static.py` |
| Output / publish directory | `dist` |

That covers Netlify, Cloudflare Pages, Vercel (framework preset "Other"), Render (static
site), Azure Static Web Apps, Firebase Hosting and similar. If a host's build image has no
Python 3.10+, build in CI or locally (`make build`) and upload `dist/` instead, for example:

```bash
make build
aws s3 sync dist/ s3://<bucket>/ --delete     # S3 (+ CloudFront in front of it)
firebase deploy --only hosting                # with "public": "dist" in firebase.json
```

No redirects or SPA fallback rules are needed.

---

## Containers (any cloud)

`deploy/Dockerfile` builds the site and serves it with nginx on port 8080: the default
port for Google Cloud Run, and easy to map on AWS App Runner / ECS, Azure Container Apps,
Fly.io, Render, Kubernetes and the rest.

```bash
make docker-build            # docker build -f deploy/Dockerfile -t engineering-guide .
make docker-run              # http://127.0.0.1:8080
```

`deploy/nginx.conf` gzips text, caches the versioned libraries under `vendor/` for a
year and makes browsers revalidate everything else, so a redeploy shows up at once.

---

## Repository layout

```text
content/            all learning material, the app's single source of truth (read as is, never written)
  interview-core/     PyDSA/  GoDSA/  SystemDesign/  SoftwareDesign/  CSFundamentals/  Maths/  GoogleBehavioral/
  languages/          GoEngineering/  PyEngineering/  GoStdLib/  PyStdLib/
  data-and-apis/      SQL/  NoSQL/  API/        (SQL/lab/, NoSQL/lab/: Query Lab questions and datasets)
  ai-engineering/     AI-road-map/  AI-Libraries-Guides/  Agentic-AI/  MLOps/
  ship-and-run/       Tool-Kit/  TestingAndQuality/  CICD/  DataEngineering/
  study-plans/        master_dsa_plan.md  REVIEW_LEDGER.md  GOOGLE_INTERVIEW_PREP.md  CURRICULUM.md (generated)
webapp/
  server.py         local app: serves the front end, answers /api/*, runs code (paths: CONTENT and friends at the top)
  build_static.py   static build: dist/ from the front end + every /api answer
  static/           the front end (index.html, app.js, …, vendor/ libraries)
  scripts/          developer checks for the front end (npm ci first; see below)
  data/             progress.json, your local progress
tools/              curriculum tooling: problems.tsv (DSA index), generators, checkers; ollama/Modelfile
deploy/             Dockerfile + nginx.conf for container platforms
docs/               this guide; CONTEXT.md (session handoff notes)
.github/workflows/  GitHub Pages deployment
docker-compose.databases.yml   Postgres, MongoDB and Redis for the SQL / NoSQL lessons
Makefile            make help lists every command
```

The groups mirror the sections of the app's home page. Module folders keep their names
(`PyDSA`, `SystemDesign`, …) because they are part of the app's contract: page ids, the
reader's cross-references between guides (`SystemDesign/building_blocks/06_x.md` written in a
lesson is resolved to its page) and the problem tracker all use them. Moving a module to
another group is a `git mv` plus one line in `server.py` and in `CONTENT_GROUP` (reader.js).

### Developer checks

The app itself needs no npm packages. The checks in `webapp/scripts/` do:

```bash
cd webapp && npm ci                                   # jsdom + mermaid, dev only
node webapp/scripts/validate_api_labs.mjs             # every API/System Design lab mounts
node webapp/scripts/validate_mermaid.mjs              # mermaid blocks in the API guides parse
node webapp/scripts/arch_tool.mjs check               # every ```arch diagram lays out
node webapp/scripts/validate_viz_player.js            # every visualizer plays (app running)
node webapp/scripts/validate_query_labs.mjs           # every Query Lab solution runs (no npm needed)
```

### The Query Lab

The SQL and NoSQL modules' Query Lab (`#/query-lab/sql|mongodb|redis`, `webapp/static/qlab*.js`)
runs its databases in the browser, so it works the same locally and on a static host: PostgreSQL
via PGlite (`static/vendor/pglite/`), MongoDB's query language via mingo (`static/vendor/mingo/`)
and a Redis emulator (`static/qlab-redis.js`, checked command by command against Redis 7).

- **Questions** live in Markdown that also reads well on GitHub: `content/data-and-apis/SQL/lab/questions.md`,
  `content/data-and-apis/NoSQL/lab/mongodb-questions.md`, `content/data-and-apis/NoSQL/lab/redis-questions.md`. To add one, copy an existing
  question (heading, metadata comment, prompt, hints, `<details>` with the solution) and run
  `validate_query_labs.mjs`. No code changes, and the static build picks it up.
- **Datasets** (`content/data-and-apis/SQL/lab/datasets/`, `content/data-and-apis/NoSQL/lab/datasets/`) are generated, deterministically, by
  `python3 tools/gen_query_lab_data.py`. Re-run the validator after regenerating: answers depend on
  the data.
