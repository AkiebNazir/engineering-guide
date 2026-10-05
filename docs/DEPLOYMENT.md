# Running and Deploying the Guide

The web app runs in two modes from the same front end (`webapp/static/`):

| | Local app (`make app`) | Static site (`make build`) |
|---|---|---|
| What it is | `webapp/server.py`, Python standard library, on `127.0.0.1` | A plain folder, `dist/`, of HTML, JS, CSS and pre-rendered JSON |
| Reading every module, visualizers, labs, diagrams | Yes | Yes |
| **Run** / **gofmt** in the editor | Yes (Python and Go on your machine) | No; the editor shows how to run it locally |
| Progress (status, drafts, notes, timers, reviews) | `webapp/data/progress.json` | The visitor's browser (`localStorage`), per device |
| Where it can run | Your machine only (it executes code you type) | Any static host or container platform |

The static build is safe to publish: it contains no server, executes nothing, and never
includes your `progress.json`.

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
<module folders>/   the curriculum (PyDSA/, GoDSA/, SystemDesign/, CSFundamentals/, …):
                    the single source of truth; the app reads them as they are
tools/              curriculum tooling: problems.tsv (DSA index), generators, checkers
webapp/
  server.py         local app: serves the front end, answers /api/*, runs code
  build_static.py   static build: dist/ from the front end + every /api answer
  static/           the front end (index.html, app.js, …, vendor/ libraries)
  scripts/          developer checks for the front end (npm ci first; see below)
  data/             progress.json, your local progress
deploy/             Dockerfile + nginx.conf for container platforms
docs/               this guide
.github/workflows/  GitHub Pages deployment
Makefile            make help lists every command
```

The curriculum folders keep their names on purpose: the app's routes, the links between
guides and the run instructions inside the lessons (`go run GoStdLib/…`) all use them.

### Developer checks

The app itself needs no npm packages. The checks in `webapp/scripts/` do:

```bash
cd webapp && npm ci                                   # jsdom + mermaid, dev only
node webapp/scripts/validate_api_labs.mjs             # every API/System Design lab mounts
node webapp/scripts/validate_mermaid.mjs              # mermaid blocks in the API guides parse
node webapp/scripts/arch_tool.mjs check               # every ```arch diagram lays out
node webapp/scripts/validate_viz_player.js            # every visualizer plays (app running)
```
