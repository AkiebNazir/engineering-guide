#!/usr/bin/env python3
"""
Ultimate Engineering Guide — a local web app for the DSA, systems, data and AI curriculum.

Stdlib only. No pip install, no build step.

    python webapp/server.py          # then open http://127.0.0.1:8420

Two modes:

  local (default)  Binds to 127.0.0.1. It executes code you type, on your machine,
                   as you — the same trust model as a Jupyter notebook. Single user,
                   everything readable, progress in webapp/data/progress.json.
                   Do not expose it to a network.
  hosted (EG_AUTH=1, `make serve`, deploy/Dockerfile)
                   Sign-in with Google (google_signin.py) or an emailed
                   one-time code (auth.py), subscription tiers
                   (entitlements.py) enforced on every /api request, per-user progress
                   in SQLite, security headers, and code execution switched off.
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class StudioServer(ThreadingHTTPServer):
    # The page pulls ~60 scripts at once; the default backlog of 5 made the
    # browser see ERR_CONNECTION_RESET on some of them and load half a page.
    request_queue_size = 128
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import auth
import entitlements
import google_signin
import sandbox

ROOT = Path(__file__).resolve().parent.parent
WEBAPP = ROOT / "webapp"
STATIC = WEBAPP / "static"
DATA = WEBAPP / "data"
STATE_FILE = DATA / "progress.json"
TSV = ROOT / "tools" / "problems.tsv"
# The curriculum lives under content/, one folder per area (see docs/DEPLOYMENT.md).
CONTENT = ROOT / "content"
INTERVIEW_CORE = CONTENT / "interview-core"
LANGUAGES = CONTENT / "languages"
DATA_AND_APIS = CONTENT / "data-and-apis"
AI_ENGINEERING = CONTENT / "ai-engineering"
SHIP_AND_RUN = CONTENT / "ship-and-run"
PY_DSA = INTERVIEW_CORE / "PyDSA"
GO_DSA = INTERVIEW_CORE / "GoDSA"
SYSTEM_DESIGN = INTERVIEW_CORE / "SystemDesign"
SYSTEM_DESIGN_GUIDE = SYSTEM_DESIGN / "SYSTEM_DESIGN_GUIDE.md"
ENG_ROOTS = {"go": LANGUAGES / "GoEngineering", "py": LANGUAGES / "PyEngineering",
             "lld": INTERVIEW_CORE / "SoftwareDesign" / "lld"}
ENG_EXT = {"go": "go", "py": "py", "lld": "py"}
LLD_ID_RE = re.compile(r"^\d{3}_[a-z0-9_]+$")
ROADMAP_DIR = AI_ENGINEERING / "AI-road-map"
LIBRARY_GUIDES_DIR = AI_ENGINEERING / "AI-Libraries-Guides"
AGENTIC_AI_DIR = AI_ENGINEERING / "Agentic-AI"
CS_FUNDAMENTALS_DIR = INTERVIEW_CORE / "CSFundamentals"
GOOGLE_BEHAVIORAL_DIR = INTERVIEW_CORE / "GoogleBehavioral"
SOFTWARE_DESIGN_DIR = INTERVIEW_CORE / "SoftwareDesign"
API_DIR = DATA_AND_APIS / "API"
SQL_DIR = DATA_AND_APIS / "SQL"
NOSQL_DIR = DATA_AND_APIS / "NoSQL"
STDLIB_ROOTS = {"py": LANGUAGES / "PyStdLib", "go": LANGUAGES / "GoStdLib"}
# Flat `NN_slug.md` tracks with a README index, all served by one pair of endpoints:
# /api/track?m=<key> and /api/track-doc?m=<key>&id=<id>.
TRACK_DIRS = {"toolkit": SHIP_AND_RUN / "Tool-Kit", "testing": SHIP_AND_RUN / "TestingAndQuality", "cicd": SHIP_AND_RUN / "CICD",
              "dataeng": SHIP_AND_RUN / "DataEngineering", "mlops": AI_ENGINEERING / "MLOps", "maths": INTERVIEW_CORE / "Maths"}
# Tracks whose chapters are grouped into parts (a learning path), keyed like
# TRACK_DIRS. Chapter numbers already run in path order; the table only names
# the groups. A chapter missing from its track's table lands in "More".
TRACK_PARTS = {
    "maths": (
        ("Part 0 · Warm-up", ("00",)),
        ("Part 1 · The language of maths", ("01", "02", "03", "04")),
        ("Part 2 · Discrete maths", ("05", "06", "07", "08")),
        ("Part 3 · Continuous maths", ("09", "10", "11", "12")),
        ("Part 4 · Maths behind computing", ("13", "14", "15")),
    ),
}

PORT = int(os.environ.get("DSA_PORT", "8420"))

# Hosted mode: sign-in, tiers and no code execution (see the module docstring).
AUTH_ENABLED = os.environ.get("EG_AUTH", "") == "1"
HOST = os.environ.get("EG_HOST", "127.0.0.1")
LOOPBACK = HOST in ("127.0.0.1", "localhost", "::1")
# Secure cookies need HTTPS; on by default unless bound to loopback for development.
COOKIE_SECURE = os.environ.get("EG_COOKIE_SECURE", "0" if LOOPBACK else "1") == "1"
SESSION_COOKIE = "__Host-eg_session" if COOKIE_SECURE else "eg_session"
TRUST_PROXY = os.environ.get("EG_TRUST_PROXY", "") == "1"     # read X-Forwarded-For / -Proto
# The site's origin, e.g. https://guide.example.com. Several, comma-separated, are allowed
# (e.g. a public address and https://localhost); the first is the one Google returns to.
PUBLIC_ORIGINS = [o.rstrip("/") for o in re.split(r"[,\s]+", os.environ.get("EG_PUBLIC_ORIGIN", "")) if o]
PUBLIC_ORIGIN = PUBLIC_ORIGINS[0] if PUBLIC_ORIGINS else ""
UPGRADE_URL = os.environ.get("EG_UPGRADE_URL", "")           # where "Upgrade" buttons go (billing page)
AUTH_DB = Path(os.environ.get("EG_AUTH_DB", str(DATA / "auth.sqlite3")))
MAX_BODY = 4_000_000
AUTH = None            # auth.AuthStore, created by main() in hosted mode
GOOGLE = None          # google_signin.GoogleSignIn, when EG_GOOGLE_CLIENT_ID/SECRET are set
OAUTH_COOKIE = "__Host-eg_oauth" if COOKIE_SECURE else "eg_oauth"
SIGNIN_ERRORS = {"google_failed", "google_cancelled", "google_mismatch", "disabled", "google_off", "rate_limited"}
CODE_RUN_OFF = ("Running code is switched off on the hosted guide. Clone the repository and "
                "run `make app` to run code on your own machine.")
RUNNER_SOCKET = os.environ.get("EG_RUNNER_SOCKET", "")      # hosted: runner.py's socket (see deploy/)
RUNNER = None          # sandbox.LocalRunner / RemoteRunner, picked by code_runner() and main()
SCRATCH_PKG = "scratch_run"    # the package a Go level's buffer becomes, inside a copy of its module
RUN_TIMEOUT_PY = 15
RUN_TIMEOUT_GO = 40
RUN_TIMEOUT_ENG_PY = 30
RUN_TIMEOUT_ENG_GO = 45
RUN_TIMEOUT_STDLIB_PY = 20
RUN_TIMEOUT_STDLIB_GO = 45

TOPIC_TITLES = {
    "01_arrays_hashing": "Arrays & Hashing",
    "02_two_pointers": "Two Pointers",
    "03_sliding_window": "Sliding Window",
    "04_prefix_sum": "Prefix Sum",
    "05_binary_search": "Binary Search",
    "06_stack": "Stack & Monotonic Stack",
    "07_queue_deque": "Queue & Deque",
    "08_linked_list": "Linked List",
    "09_recursion_backtracking": "Recursion & Backtracking",
    "10_trees": "Binary Trees",
    "11_binary_search_tree": "Binary Search Tree",
    "12_heap_priority_queue": "Heap / Priority Queue",
    "13_trie": "Trie (Prefix Tree)",
    "14_graphs": "Graphs",
    "15_advanced_graphs": "Advanced Graphs",
    "16_dp_1d": "Dynamic Programming (1D)",
    "17_dp_2d": "Dynamic Programming (2D)",
    "18_greedy": "Greedy",
    "19_intervals": "Intervals",
    "20_bit_manipulation": "Bit Manipulation",
    "21_math_geometry": "Math & Geometry",
    "22_sorting_algorithms": "Sorting Algorithms",
    "23_string_algorithms": "String Algorithms",
    "24_matrix": "Matrix",
    "25_design": "Design",
    "26_segment_tree_fenwick": "Segment Tree & Fenwick Tree",
    "27_algorithms": "Classic Algorithms (Randomized, Divide & Conquer, Quickselect)",
    "28_recursion_backtracking": "Recursion Mastery (Progressive Ladder)",
}

_state_lock = threading.Lock()


# ----------------------------------------------------------------------------
# Interpreter discovery
# ----------------------------------------------------------------------------
def python_bin() -> str:
    venv = ROOT / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


def go_bin() -> str | None:
    found = shutil.which("go")
    if found:
        return found
    for candidate in ("/usr/local/go/bin/go", "/opt/homebrew/bin/go"):
        if Path(candidate).exists():
            return candidate
    return None


# ----------------------------------------------------------------------------
# Persistent state
# ----------------------------------------------------------------------------
def default_state() -> dict:
    return {
        "version": 1,
        "settings": {"theme": "dark", "lang": "py", "editorFont": 13},
        "problems": {},
        "sessions": {},
        "docs": {},
    }


def load_state() -> dict:
    if not STATE_FILE.exists():
        return default_state()
    try:
        state = json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        backup = STATE_FILE.with_suffix(".corrupt.json")
        try:
            shutil.copy(STATE_FILE, backup)
            print(f"[warn] progress.json unreadable; backed up to {backup.name}")
        except OSError:
            pass
        return default_state()
    base = default_state()
    base.update(state)
    return base


def apply_patch(state: dict, body: dict) -> dict:
    """Merge one POST /api/patch into a progress document (static/app.js staticPost twins this)."""
    pid = body.get("id")
    if pid and isinstance(body.get("patch", {}), dict):
        rec = state["problems"].setdefault(pid, {})
        rec.update(body.get("patch", {}))
    if isinstance(body.get("settings"), dict):
        state["settings"].update(body["settings"])
    if body.get("doc") and isinstance(body.get("docPatch", {}), dict):
        # Reading state for module pages: scroll depth, checked sections,
        # highlights, completion.
        docs = state.setdefault("docs", {})
        docs.setdefault(body["doc"], {}).update(body.get("docPatch", {}))
    if isinstance(body.get("session"), dict):
        day = str(body["session"].get("date", ""))[:10]
        secs = body["session"].get("seconds", 0)
        if day and isinstance(secs, (int, float)):
            state["sessions"][day] = state["sessions"].get(day, 0) + secs
    return state


def save_state(state: dict) -> None:
    """Atomic write so a crash mid-save cannot corrupt your progress."""
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    os.replace(tmp, STATE_FILE)


# ----------------------------------------------------------------------------
# Curriculum loading
# ----------------------------------------------------------------------------
def snake(slug: str) -> str:
    return slug.replace("-", "_")


def py_path(topic: str, seq: str, slug: str, kind: str) -> Path:
    return PY_DSA / topic / f"{seq}_{snake(slug)}_{kind}.py"


def go_path(topic: str, seq: str, slug: str, kind: str) -> Path:
    return GO_DSA / topic / f"{seq}_{snake(slug)}" / f"{kind}.go"


def load_curriculum() -> list[dict]:
    with TSV.open() as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    out = []
    for r in rows:
        topic, seq, slug = r["topic"], r["seq"], r["slug"]
        out.append({
            "id": f"{topic}/{seq}",
            "topic": topic,
            "topicTitle": TOPIC_TITLES.get(topic, topic),
            "seq": seq,
            "lc": r["lc"],
            "slug": slug,
            "title": r["title"],
            "diff": r["diff"],
            "url": f"https://leetcode.com/problems/{slug}/",
            "has": {
                "pyQuestion": py_path(topic, seq, slug, "question").exists(),
                "pySolution": py_path(topic, seq, slug, "solution").exists(),
                "goQuestion": go_path(topic, seq, slug, "question").exists(),
                "goSolution": go_path(topic, seq, slug, "solution").exists(),
            },
        })
    return out


def load_topics(problems: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for p in problems:
        t = seen.setdefault(p["topic"], {
            "id": p["topic"],
            "title": p["topicTitle"],
            "num": p["topic"].split("_")[0],
            "count": 0,
            "written": 0,
            "guides": {},
        })
        t["count"] += 1
        if p["has"]["pySolution"]:
            t["written"] += 1
    for tid, t in seen.items():
        t["guides"] = {
            "py": (PY_DSA / tid / "_TOPIC_GUIDE.md").exists(),
            "go": (GO_DSA / tid / "_TOPIC_GUIDE.md").exists(),
        }
    return list(seen.values())


# ----------------------------------------------------------------------------
# GoEngineering / PyEngineering — production-grade curriculum (not LeetCode)
# ----------------------------------------------------------------------------
ENG_ACRONYMS = {
    "api": "API", "rest": "REST", "io": "I/O", "json": "JSON", "db": "DB",
    "grpc": "gRPC", "ci": "CI", "sql": "SQL", "http": "HTTP", "ii": "II",
    # API module: Foundation-level and lab slugs pull acronyms/mixed-case terms
    # from this same table via eng_prettify, so a new level needs no server change.
    "jwt": "JWT", "hmac": "HMAC", "tcp": "TCP", "xml": "XML", "wsdl": "WSDL",
    "ssrf": "SSRF", "crud": "CRUD", "soap": "SOAP", "rpc": "RPC", "mtls": "mTLS",
    "etag": "ETag", "openapi": "OpenAPI", "fastapi": "FastAPI", "dlq": "DLQ",
    "dataloader": "DataLoader", "fieldmask": "FieldMask", "pubsub": "PubSub",
    "websocket": "WebSocket", "ws": "WS", "mustunderstand": "mustUnderstand",
}


def eng_prettify(slug: str) -> str:
    return " ".join(ENG_ACRONYMS.get(w, w.capitalize()) for w in slug.split("_"))


def eng_topic_dirs(lang: str) -> list[Path]:
    root = ENG_ROOTS[lang]
    if not root.exists():
        return []
    return sorted(
        (d for d in root.iterdir() if d.is_dir() and re.match(r"^\d{2}_", d.name)),
        key=lambda d: d.name,
    )


def eng_file(lang: str, topic_id: str, kind: str) -> Path:
    """kind is one of explanation/solution/test."""
    root = ENG_ROOTS[lang]
    ext = ENG_EXT[lang]
    if lang == "lld":
        # SoftwareDesign/lld is flat: NNN_slug_question.py is the brief + stub (with
        # its tests built in), NNN_slug_solution.py the reference. No separate test file.
        if not LLD_ID_RE.match(topic_id):
            return root / "__invalid__"
        suffix = "question" if kind == "explanation" else kind
        return root / f"{topic_id}_{suffix}.py"
    name = f"{topic_id}_{kind}.{ext}"
    if lang == "go":
        subdir = "explanation" if kind == "explanation" else "solution"
        return root / topic_id / subdir / name
    return root / topic_id / name


def load_eng_curriculum(lang: str) -> list[dict]:
    if lang == "lld":
        return [{k: it[k] for k in ("id", "num", "slug", "title", "has")}
                for it in load_lld_problems()]
    out = []
    for d in eng_topic_dirs(lang):
        num, _, slug = d.name.partition("_")
        out.append({
            "id": d.name,
            "num": num,
            "slug": slug,
            "title": eng_prettify(slug),
            "has": {
                "explanation": eng_file(lang, d.name, "explanation").exists(),
                "solution": eng_file(lang, d.name, "solution").exists(),
                "test": eng_file(lang, d.name, "test").exists(),
            },
        })
    return out


def read_eng_problem(lang: str, topic: str, kind: str) -> dict:
    path = eng_file(lang, topic, kind)
    if not path.exists():
        return {"exists": False, "doc": "", "code": "", "path": ""}
    text = path.read_text()
    if kind == "explanation" or (lang == "lld" and kind == "solution"):
        doc, code = (split_go if lang == "go" else split_python)(text)
        if lang == "lld":
            doc = lld_brief(doc)
    else:
        doc, code = "", text
    return {
        "exists": True, "doc": doc, "code": code,
        "path": str(path.relative_to(ROOT)),
    }


LLD_BANNER_RE = re.compile(r"\A\s*=+\n(.*?)\n=+\n", re.S)


def lld_brief(doc: str) -> str:
    """The LLD files open with a ===== banner (title, tier, time box). The app shows the
    title itself, so keep only the time box as an ordinary first paragraph."""
    m = LLD_BANNER_RE.match(doc)
    if not m:
        return doc
    box = re.search(r"^Time box:\s*(.+)$", m.group(1), re.M)
    rest = doc[m.end():].lstrip("\n")
    return (f"Time box: {box.group(1).strip()}\n\n" if box else "") + rest


def eng_python_bin() -> str:
    venv = ENG_ROOTS["py"] / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else python_bin()


def run_eng(lang: str, topic: str, code: str) -> dict:
    """Runs the learner's edited explanation code.

    When the topic has a test file, tests are the real check: Go/Python
    tests are hardcoded to load the *_solution.* file by name, so the run
    gets a scratch copy of the topic with the learner's code in place of the
    solution file (same package/module, same public surface) and runs the
    real test file against it. Many topics have no test file (by design —
    this curriculum doesn't require one), so when there isn't one the
    *explanation* file is swapped instead and just compiled/run directly:
    `go vet` (which type-checks a `package main` fine even with no
    `func main()`) for Go, or executing the file for Python. The curriculum
    on disk is only ever read."""
    if not code.strip():
        return {"ok": False, "stdout": "", "exitCode": -1, "ms": 0,
                "stderr": "Nothing to run — the editor is empty."}
    if lang not in ENG_ROOTS or not re.fullmatch(r"[\w\-]+", topic or ""):     # no dots, no slashes
        return {"ok": False, "stdout": "", "exitCode": -1, "ms": 0, "stderr": "Unknown topic."}

    expl = eng_file(lang, topic, "explanation")
    sol = eng_file(lang, topic, "solution")
    test = eng_file(lang, topic, "test")
    if not expl.exists():
        return {"ok": False, "stdout": "", "exitCode": -1, "ms": 0,
                "stderr": "This topic hasn't been authored yet — nothing to run."}

    has_test = sol.exists() and test.exists()
    target = sol if has_test else expl
    root = ENG_ROOTS[lang]
    rel = target.relative_to(root).as_posix()
    pkg = rel.rpartition("/")[0]

    if lang == "go":
        timeout = RUN_TIMEOUT_ENG_GO
        job = {"kind": "go-test" if has_test else "go-vet", "cwd": pkg, "timeout": timeout,
               "files": sandbox.stage_go_module(root, [pkg], {rel: code})}
    elif lang == "lld":
        # lld/ is flat (every question and solution side by side): the question alone
        timeout = RUN_TIMEOUT_ENG_PY
        job = {"kind": "python", "python": "eng", "args": [target.name], "timeout": timeout,
               "files": {target.name: code}}
    else:
        timeout = RUN_TIMEOUT_ENG_PY
        files = sandbox.dir_files(target.parent, f"{pkg}/")
        files[rel] = code
        args = ["-m", "pytest", test.name, "-v", "-p", "no:cacheprovider"] if has_test else [expl.name]
        job = {"kind": "python", "python": "eng", "cwd": pkg, "args": args, "timeout": timeout,
               "files": files}

    result = timed_out_message(code_runner().run(job), timeout,
                               "likely an infinite loop, a deadlock, or a server that never shuts down.")
    if lang == "go" and not has_test and result.get("ok") and not result.get("stdout", "").strip():
        result["stdout"] = "go vet: no issues found — code compiles cleanly.\n"
    return result


# ----------------------------------------------------------------------------
# AI-road-map / AI-Libraries-Guides — read-only markdown reference material
# ----------------------------------------------------------------------------
ROADMAP_DAY_RE = re.compile(r"^(\d+)_day_(.+)\.md$")
ROADMAP_CAPSTONE_RE = re.compile(r"^Capstone_(\d+)_(.+)\.md$")
LIBRARY_GUIDE_RE = re.compile(r"^(\d+)_(.+)\.md$")


MD_INLINE = [
    (re.compile(r"!\[[^\]]*\]\([^)]*\)"), ""),
    (re.compile(r"\[([^\]]+)\]\([^)]*\)"), r"\1"),
    (re.compile(r"\$+"), ""),
    (re.compile(r"[*`>#]+|(?<!\w)_+|_+(?!\w)"), ""),
    (re.compile(r"\s+"), " "),
]
WELCOME_RE = re.compile(r"^Welcome to Day \d+\.\s*", re.I)


def doc_meta(path: Path, fallback: str) -> dict:
    """Title (first heading), a one-line summary (first real paragraph) and a
    reading-time estimate — what a module's cards and side navigation show."""
    try:
        text = path.read_text()
    except OSError:
        return {"title": fallback, "summary": "", "minutes": 1}
    title, summary, in_fence = None, "", False
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line:
            continue
        if line.startswith("#"):
            title = title or line.lstrip("#").strip()
            continue
        if title is None or summary:
            continue
        if line[0] in "|<-!" or re.fullmatch(r"\*\*[^*]+\*\*:?", line):
            continue
        # Source paragraphs are hard-wrapped, so one physical line is a sentence
        # fragment ("...a table is a fixed set of"). Take the whole paragraph.
        para = [line]
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith(("#", "```", "|", "<", "- ", "* ", "> ")):
                break
            para.append(nxt)
            i += 1
        line = " ".join(para)
        for pattern, repl in MD_INLINE:
            line = pattern.sub(repl, line)
        line = WELCOME_RE.sub("", line.strip())
        if len(line) < 25:
            continue
        summary = line if len(line) <= 220 else line[:217].rsplit(" ", 1)[0] + "…"
        break
    words = len(text.split())
    return {"title": title or fallback, "summary": summary,
            "minutes": max(1, round(words / 220))}


def md_title(path: Path, fallback: str) -> str:
    return doc_meta(path, fallback)["title"]


def roadmap_phase(day: int) -> str:
    if day == 0:
        return "Prerequisites"
    if day <= 30:
        return "Phase 1 · Foundations & Classical ML"
    if day <= 60:
        return "Phase 2 · Deep Learning & Neural Architectures"
    if day <= 90:
        return "Phase 3 · Transformers & Modern NLP"
    if day <= 120:
        return "Phase 4 · LLMs: Training, Fine-Tuning & Alignment"
    if day <= 150:
        return "Phase 5 · Agentic AI, MCP & Tool-Use Systems"
    return "Phase 6 · Production LLMOps & System Design"


def load_roadmap() -> list[dict]:
    if not ROADMAP_DIR.exists():
        return []
    items = []
    for path in ROADMAP_DIR.glob("*.md"):
        if path.name == "roadmap.md":
            continue
        m = ROADMAP_DAY_RE.match(path.name)
        if m:
            day = int(m.group(1))
            items.append({
                "id": path.stem, "kind": "day", "day": day,
                "phase": roadmap_phase(day),
                **doc_meta(path, path.stem.replace("_", " ")),
            })
            continue
        m = ROADMAP_CAPSTONE_RE.match(path.name)
        if m:
            items.append({
                "id": path.stem, "kind": "capstone", "day": 1000 + int(m.group(1)),
                "phase": "Capstones",
                **doc_meta(path, path.stem.replace("_", " ")),
            })
    items.sort(key=lambda x: x["day"])
    return items


def load_numbered_md_collection(dir_path: Path) -> list[dict]:
    """A directory of `NN_slug.md` files, in file order — the shape shared by
    AI-Libraries-Guides and Agentic-AI. Each item's title is its own H1."""
    if not dir_path.exists():
        return []
    items = []
    for path in sorted(dir_path.glob("*.md")):
        m = LIBRARY_GUIDE_RE.match(path.name)
        if not m:
            continue
        items.append({
            "id": path.stem, "num": m.group(1),
            **doc_meta(path, m.group(2).replace("_", " ").title()),
        })
    return items


# ----------------------------------------------------------------------------
# SystemDesign — one navigable collection instead of a single concatenated book
# ----------------------------------------------------------------------------
SD_DRILLS = ("07_interview_question_bank", "03_practice_prompts", "04_practice_answers",
             "05_architecture_blueprints", "06_spoken_walkthroughs")


def load_system_design() -> list[dict]:
    items: list[dict] = []

    def add(path: Path, group: str, doc_id: str, num: str = "", kind: str = "doc") -> None:
        if path.exists():
            meta = doc_meta(path, path.stem.replace("_", " ").title())
            items.append({"id": doc_id, "group": group, "num": num, "kind": kind, **meta})

    add(SYSTEM_DESIGN / "README.md", "Start here", "readme")
    add(SYSTEM_DESIGN / "00_google_l5_playbook.md", "Start here", "00_google_l5_playbook")
    add(SYSTEM_DESIGN / "01_company_interview_guide.md", "Start here", "01_company_interview_guide")
    add(SYSTEM_DESIGN / "02_problem_catalog.md", "Start here", "02_problem_catalog")
    for sub, group in (("building_blocks", "Building blocks"), ("best_practices", "Best practices")):
        for path in sorted((SYSTEM_DESIGN / sub).glob("*.md")):
            add(path, group, f"{sub}/{path.stem}", num=path.stem.split("_")[0])
    for q in sorted((SYSTEM_DESIGN / "problems").glob("*_question.md")):
        stem = q.name[: -len("_question.md")]
        add(q, "Practice problems", f"problem/{stem}", num=stem.split("_")[0], kind="problem")
        items[-1]["hasSolution"] = (SYSTEM_DESIGN / "solutions" / f"{stem}_solution.md").exists()
    for name in SD_DRILLS:
        add(SYSTEM_DESIGN / f"{name}.md", "Drills & blueprints", name)
    add(SYSTEM_DESIGN_GUIDE, "Complete guide", "guide")
    return items


def read_system_design(doc_id: str) -> dict:
    """Maps a collection id back to its file(s). Ids are matched against fixed
    shapes with no dots or slashes in the free part, so they cannot escape
    the SystemDesign folder."""
    solution = None
    if doc_id == "readme":
        path = SYSTEM_DESIGN / "README.md"
    elif doc_id == "guide":
        path = SYSTEM_DESIGN_GUIDE
    elif m := re.fullmatch(r"(building_blocks|best_practices)/([\w-]+)", doc_id):
        path = SYSTEM_DESIGN / m.group(1) / f"{m.group(2)}.md"
    elif m := re.fullmatch(r"problem/([\w-]+)", doc_id):
        path = SYSTEM_DESIGN / "problems" / f"{m.group(1)}_question.md"
        solution = SYSTEM_DESIGN / "solutions" / f"{m.group(1)}_solution.md"
    elif re.fullmatch(r"\d{2}_[\w-]+", doc_id):
        path = SYSTEM_DESIGN / f"{doc_id}.md"
    else:
        return {"exists": False, "markdown": ""}
    out = read_markdown(path)
    if out["exists"] and solution and solution.exists():
        out["solution"] = solution.read_text()
    return out


def load_library_guides() -> list[dict]:
    return load_numbered_md_collection(LIBRARY_GUIDES_DIR)



def load_api() -> list[dict]:
    if not API_DIR.exists():
        return []
    items = []
    # Collect Masterclass Guides and General Guides
    for path in sorted(API_DIR.glob("*/*.md")):
        items.append({
            "id": path.parent.name + "/" + path.stem,
            **doc_meta(path, path.stem.replace("_", " ").title()),
            "path": str(path.relative_to(API_DIR))
        })
    return items


def load_agentic_ai() -> list[dict]:
    return load_numbered_md_collection(AGENTIC_AI_DIR)


def load_track(key: str) -> list[dict]:
    """A TRACK_DIRS module: README first ("Start here"), then its chapters in file order."""
    base = TRACK_DIRS.get(key)
    if not base or not base.exists():
        return []
    items: list[dict] = []
    readme = base / "README.md"
    if readme.exists():
        items.append({"id": "README", "num": "", "kind": "doc", **doc_meta(readme, "Start here")})
    parts = {n: part for part, nums in TRACK_PARTS.get(key, ()) for n in nums}
    for it in load_numbered_md_collection(base):
        items.append({**it, "kind": "chapter", **({"part": parts.get(it["num"], "More")} if parts else {})})
    if parts and items and items[0]["id"] == "README":
        items[0]["part"] = "Start here"
    return items


# The learning path through CSFundamentals (its README, Track A): cost first,
# then one machine, then many, then whole systems, then interview execution.
# Chapters keep their file numbers (other modules cite "CSFundamentals/03 §3"),
# so the path is an order and a grouping, not a renumbering. A chapter missing
# from this table still shows up, in a trailing "More" group.
CS_PARTS = (
    ("Part 1 · Measuring cost", ("07", "06")),
    ("Part 2 · One machine", ("13", "01", "14", "05")),
    ("Part 3 · Many machines", ("02", "03", "15")),
    ("Part 4 · Systems of services", ("04", "11")),
    ("Part 5 · Performing in the interview", ("08", "09", "10", "12")),
)


def load_cs_fundamentals() -> list[dict]:
    """Load CSFundamentals: the README ("Start here"), then the deep dives in
    learning-path order, each tagged with its part."""
    if not CS_FUNDAMENTALS_DIR.exists():
        return []
    chapters = {}
    for path in sorted(CS_FUNDAMENTALS_DIR.glob("*_deep_dive.md")):
        m = re.match(r"^(\d+)_(.+?)_deep_dive\.md$", path.name)
        if not m:
            continue
        chapters[m.group(1)] = {
            "id": path.stem, "num": m.group(1), "kind": "chapter",
            **doc_meta(path, m.group(2).replace("_", " ").title()),
        }
    items = []
    readme = CS_FUNDAMENTALS_DIR / "README.md"
    if readme.exists():
        items.append({"id": "README", "num": "", "kind": "doc", "part": "Start here",
                      **doc_meta(readme, "Start here")})
    for part, nums in CS_PARTS:
        items.extend({**chapters.pop(n), "part": part} for n in nums if n in chapters)
    items.extend({**it, "part": "More"} for it in chapters.values())
    return items


def load_google_behavioral() -> list[dict]:
    """Load GoogleBehavioral markdown files."""
    if not GOOGLE_BEHAVIORAL_DIR.exists():
        return []
    items = []
    for path in sorted(GOOGLE_BEHAVIORAL_DIR.glob("*.md")):
        m = re.match(r"^(\d+)_(.+)\.md$", path.name)
        if not m:
            continue
        items.append({
            "id": path.stem, "num": m.group(1),
            **doc_meta(path, m.group(2).replace("_", " ").title()),
        })
    return items


# ----------------------------------------------------------------------------
# SQL / NoSQL — read-only markdown ladders
#
# SQL is a flat NN_slug.md collection (one "Levels" group). NoSQL splits into
# mongodb/ and redis/ subfolders, so its ids are path-style (`mongodb/03_x`)
# and the group comes from the folder — the same shape as the API module.
# Both tolerate the folder not existing yet: the module then lists nothing
# rather than breaking the sidebar.
# ----------------------------------------------------------------------------
LEVEL_MD_RE = re.compile(r"^(\d{2})_([a-z0-9_]+)\.md$")
SQL_ID_RE = re.compile(r"^(?:README|\d{2}_[a-z0-9_]+)$")
NOSQL_ID_RE = re.compile(r"^(?:README|(?:mongodb|redis|concepts)/\d{2}_[a-z0-9_]+)$")
NOSQL_GROUPS = (("mongodb", "MongoDB"), ("redis", "Redis"), ("concepts", "Concepts & Interview Prep"))


def load_sql() -> list[dict]:
    if not SQL_DIR.exists():
        return []
    items: list[dict] = []
    readme = SQL_DIR / "README.md"
    if readme.exists():
        items.append({"id": "README", "num": "", "kind": "doc", "group": "Levels",
                      **doc_meta(readme, "Start here")})
    for path in sorted(SQL_DIR.glob("*.md")):
        m = LEVEL_MD_RE.match(path.name)
        if not m:
            continue
        items.append({
            "id": path.stem, "num": m.group(1), "kind": "level", "group": "Levels",
            **doc_meta(path, m.group(2).replace("_", " ").title()),
        })
    return items


def load_nosql() -> list[dict]:
    if not NOSQL_DIR.exists():
        return []
    items: list[dict] = []
    readme = NOSQL_DIR / "README.md"
    if readme.exists():
        items.append({"id": "README", "num": "", "kind": "doc", "group": "Overview",
                      **doc_meta(readme, "Start here")})
    for sub, group in NOSQL_GROUPS:
        for path in sorted((NOSQL_DIR / sub).glob("*.md")):
            m = LEVEL_MD_RE.match(path.name)
            if not m:
                continue
            items.append({
                "id": f"{sub}/{path.stem}", "num": m.group(1), "kind": "level",
                "group": group, "store": sub,
                **doc_meta(path, m.group(2).replace("_", " ").title()),
            })
    return items


DSA_GUIDE_ID_RE = re.compile(r"^\d{2}_[a-z0-9_]+$")
DSA_GUIDE_ROOTS = {"py": PY_DSA, "go": GO_DSA}


def load_dsa_guides(lang: str = "py") -> list[dict]:
    """One reader page per topic that has a _TOPIC_GUIDE.md in the given language's
    tree (PyDSA or GoDSA), in topic order."""
    root = DSA_GUIDE_ROOTS.get(lang, PY_DSA)
    items: list[dict] = []
    for path in sorted(root.glob("*/_TOPIC_GUIDE.md")):
        tid = path.parent.name
        if not DSA_GUIDE_ID_RE.fullmatch(tid):
            continue
        items.append({"id": tid, "num": tid.split("_")[0], "kind": "guide", "lang": lang,
                      "group": "Topic guides", **doc_meta(path, tid)})
    return items


def read_dsa_guide(doc_id: str, lang: str = "py") -> dict:
    """Whole-id match against a fixed shape, so it cannot escape PyDSA/ or GoDSA/."""
    if not DSA_GUIDE_ID_RE.fullmatch(doc_id or ""):
        return {"exists": False, "markdown": ""}
    return read_markdown(DSA_GUIDE_ROOTS.get(lang, PY_DSA) / doc_id / "_TOPIC_GUIDE.md")


def read_sql(doc_id: str) -> dict:
    """Ids are matched whole against a fixed shape with no dots or slashes, so
    they cannot escape SQL/."""
    if not SQL_ID_RE.fullmatch(doc_id or ""):
        return {"exists": False, "markdown": ""}
    return read_markdown(SQL_DIR / f"{doc_id}.md")


def read_nosql(doc_id: str) -> dict:
    """Same, but the one allowed slash is a literal `mongodb/` or `redis/`."""
    if not NOSQL_ID_RE.fullmatch(doc_id or ""):
        return {"exists": False, "markdown": ""}
    return read_markdown(NOSQL_DIR / f"{doc_id}.md")


# ----------------------------------------------------------------------------
# Query Lab — run SQL / MongoDB / Redis in the browser against real datasets
#
#   SQL/lab/questions.md                 question bank (markdown, readable on GitHub)
#   SQL/lab/datasets/<name>.sql          one Postgres schema per dataset
#   NoSQL/lab/mongodb-questions.md       + NoSQL/lab/datasets/mongodb/<collection>.json
#   NoSQL/lab/redis-questions.md         + NoSQL/lab/datasets/redis/seed.redis
#
# The engines themselves run in the browser (PGlite, mingo, qlab-redis.js), so
# the server only hands out files: the lab works the same on a static host.
# Datasets are generated by tools/gen_query_lab_data.py.
# ----------------------------------------------------------------------------
QUERY_LABS = {
    "sql": {"questions": SQL_DIR / "lab" / "questions.md", "datasets": SQL_DIR / "lab" / "datasets", "glob": "*.sql"},
    "mongodb": {"questions": NOSQL_DIR / "lab" / "mongodb-questions.md", "datasets": NOSQL_DIR / "lab" / "datasets" / "mongodb", "glob": "*.json"},
    "redis": {"questions": NOSQL_DIR / "lab" / "redis-questions.md", "datasets": NOSQL_DIR / "lab" / "datasets" / "redis", "glob": "*.redis"},
}
QLAB_META_RE = re.compile(r"<!--\s*(id:.*?)-->", re.S)
QLAB_FENCE_RE = re.compile(r"^```([\w-]*)[ \t]*(verify)?[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
QLAB_DATASET_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


def _qlab_question(title: str, section: str, body: str) -> dict | None:
    meta_m = QLAB_META_RE.search(body)
    if not meta_m:
        return None
    meta = {}
    for part in meta_m.group(1).split("|"):
        key, _, val = part.partition(":")
        meta[key.strip()] = val.strip()
    body = body[:meta_m.start()] + body[meta_m.end():]
    before, _, rest = body.partition("<details>")
    details = rest.split("</details>")[0]
    details = re.sub(r"<summary>.*?</summary>", "", details, flags=re.S)

    prompt_lines, hints = [], []
    for line in before.strip().split("\n"):
        if line.startswith(">"):
            text = line[1:].strip()
            m = re.match(r"\*\*Hint:\*\*\s*(.*)", text)
            if m:
                hints.append(m.group(1))
            elif hints:
                hints[-1] += " " + text
        else:
            prompt_lines.append(line)

    solution = verify = None
    explanation = details
    for m in QLAB_FENCE_RE.finditer(details):
        if m.group(2) == "verify" and verify is None:
            verify = m.group(3).strip()
            explanation = explanation.replace(m.group(0), "")
        elif solution is None and m.group(2) is None:
            solution = m.group(3).strip()
            explanation = explanation.replace(m.group(0), "")
    tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    return {
        "id": meta.get("id", ""), "title": title.strip(), "section": section,
        "dataset": meta.get("dataset", ""), "level": meta.get("level", "Medium"),
        "tags": tags, "order": meta.get("order", "any"),
        "prompt": "\n".join(prompt_lines).strip(), "hints": hints,
        "solution": solution or "", "verify": verify, "explanation": explanation.strip(),
    }


def load_query_lab(engine: str) -> dict:
    """A lab's question bank and dataset list, parsed from its markdown file."""
    lab = QUERY_LABS.get(engine)
    if not lab:
        return {"exists": False}
    text = lab["questions"].read_text() if lab["questions"].exists() else ""
    title = next((ln[2:].strip() for ln in text.split("\n") if ln.startswith("# ")), "Query Lab")
    chunks = re.split(r"^(##|###) (.+)$", text, flags=re.M)
    intro = re.sub(r"^# .*$", "", chunks[0], count=1, flags=re.M)
    intro = re.sub(r"<!--.*?-->", "", intro, flags=re.S).strip()
    questions, section = [], ""
    for i in range(1, len(chunks) - 2, 3):
        level, heading, body = chunks[i], chunks[i + 1], chunks[i + 2]
        if level == "##":
            section = heading.strip()
        else:
            q = _qlab_question(heading, section, body)
            if q:
                questions.append(q)
    datasets = []
    for path in sorted(lab["datasets"].glob(lab["glob"])) if lab["datasets"].exists() else []:
        if engine == "sql":
            first = path.read_text().split("\n", 3)
            desc = first[2].lstrip("- ").strip() if len(first) > 2 else ""
            datasets.append({"id": path.stem, "description": desc})
    if engine == "mongodb" and lab["datasets"].exists():
        datasets = [{"id": "shop", "description": "The shop dataset as documents: orders embed their items.",
                     "collections": [p.stem for p in sorted(lab["datasets"].glob("*.json"))]}]
    if engine == "redis" and lab["datasets"].exists():
        datasets = [{"id": "seed", "description": "Caches, leaderboards, sessions, counters, bitmaps, geo and streams."}]
    return {"exists": True, "engine": engine, "title": title, "intro": intro,
            "datasets": datasets, "questions": questions}


def read_query_lab_data(engine: str, dataset: str) -> dict:
    """The raw dataset files for one lab dataset (the browser engine loads them)."""
    lab = QUERY_LABS.get(engine)
    if not lab or not QLAB_DATASET_RE.fullmatch(dataset or "") or not lab["datasets"].exists():
        return {"exists": False, "files": {}}
    if engine == "sql":
        path = lab["datasets"] / f"{dataset}.sql"
        files = {path.name: path.read_text()} if path.is_file() else {}
    elif dataset in ("shop", "seed"):
        files = {p.name: p.read_text() for p in sorted(lab["datasets"].glob(lab["glob"]))}
    else:
        files = {}
    return {"exists": bool(files), "files": files}


# ----------------------------------------------------------------------------
# PyStdLib / GoStdLib — a package per folder, ten levels inside each
#
#   PyStdLib/08_collections/GUIDE.md
#   PyStdLib/08_collections/level_01_counter_basics.py … level_10_*.py
#   PyStdLib/08_collections/dsa_interview.py             (optional, shown last)
#
#   GoStdLib/12_sort/GUIDE.md
#   GoStdLib/12_sort/level_01_ints_strings_float64s/main.go
#   GoStdLib/12_sort/dsa_interview/main.go               (optional, shown last)
#
# Nothing is hardcoded: packages and levels are globbed every request, so a
# content agent adding package 16+ or a dsa_interview file needs no server
# change — only a page reload.
# ----------------------------------------------------------------------------
STDLIB_PKG_RE = re.compile(r"^(\d{2,})_([a-z0-9_]+)$")
STDLIB_LEVEL_RE = re.compile(r"^level_(\d{2})_([a-z0-9_]+)$")
STDLIB_DSA = "dsa_interview"
STDLIB_DSA_TITLE = "DSA interview examples"
# Stdlib packages whose real import name is a path. Matching on the first
# segment keeps this a rule, not a list of packages: `encoding_json` →
# `encoding/json`, `os_exec` → `os/exec`, and an unknown prefix is left alone.
STDLIB_PATH_PREFIXES = {
    "archive", "compress", "container", "crypto", "database", "debug", "encoding",
    "go", "hash", "image", "index", "io", "log", "math", "mime", "net", "os",
    "path", "regexp", "runtime", "sync", "testing", "text", "unicode",
}


def stdlib_lang(raw: str) -> str:
    return "go" if raw == "go" else "py"


def stdlib_pkg_title(slug: str) -> str:
    """The name you would actually type in an import — `collections`,
    `itertools`, `encoding/json`, `path/filepath`."""
    head, sep, _ = slug.partition("_")
    return slug.replace("_", "/") if sep and head in STDLIB_PATH_PREFIXES else slug


def stdlib_pkg_dirs(lang: str) -> list[Path]:
    root = STDLIB_ROOTS[lang]
    if not root.exists():
        return []
    return sorted(
        (d for d in root.iterdir() if d.is_dir() and STDLIB_PKG_RE.match(d.name)),
        key=lambda d: (int(STDLIB_PKG_RE.match(d.name).group(1)), d.name),
    )


def stdlib_level_names(lang: str, pkg_dir: Path) -> list[str]:
    """Every level id in a package directory, unsorted. A Go level is a
    directory holding main.go; a Python level is a single .py file."""
    if not pkg_dir.is_dir():
        return []
    if lang == "go":
        return [d.name for d in pkg_dir.iterdir() if d.is_dir() and (d / "main.go").exists()]
    return [f.stem for f in pkg_dir.glob("*.py") if f.is_file()]


STDLIB_HEAD_RE = re.compile(r"LEVEL\s+\d+\s*\(([^)]*)\)\s*[-\u2013\u2014]+\s*(.+)")


def stdlib_level_head(path: Path) -> tuple[str, str]:
    """(tag, blurb) from the lesson's own first line — `LEVEL 04 (core) -
    Real exceptions: namedtuple immutability` — so the ladder can say what a
    level is about instead of only echoing its file name. Empty when a file
    (a dsa_interview one, say) does not open that way."""
    try:
        with path.open() as f:
            head = f.read(600)
    except OSError:
        return "", ""
    m = STDLIB_HEAD_RE.search(head)
    return (m.group(1).strip(), m.group(2).strip()) if m else ("", "")


def stdlib_levels(lang: str, pkg_dir: Path) -> list[dict]:
    levels, dsa = [], None
    for name in stdlib_level_names(lang, pkg_dir):
        m = STDLIB_LEVEL_RE.match(name)
        if m:
            path = pkg_dir / name / "main.go" if lang == "go" else pkg_dir / f"{name}.py"
            tag, blurb = stdlib_level_head(path)
            levels.append({"id": name, "num": int(m.group(1)),
                           "title": eng_prettify(m.group(2)), "kind": "level",
                           "tag": tag, "blurb": blurb})
        elif name == STDLIB_DSA:
            dsa = {"id": name, "title": STDLIB_DSA_TITLE, "kind": "dsa",
                   "tag": "interview", "blurb": ""}
    levels.sort(key=lambda x: (x["num"], x["id"]))
    if dsa:
        # numbered one past the last level so "sorted by number, DSA last"
        # holds however many levels a package actually has
        dsa["num"] = (levels[-1]["num"] if levels else 0) + 1
        levels.append(dsa)
    return levels


def stdlib_summary(guide: Path) -> str:
    """The GUIDE's opening paragraph (under "What it's for"), whole and cut at
    a sentence — doc_meta only keeps the first physical line, which stops
    mid-clause on these hard-wrapped files."""
    try:
        text = guide.read_text()
    except OSError:
        return ""
    para, in_fence, seen_h2 = [], False, False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("#"):
            if para:
                break
            seen_h2 = seen_h2 or line.startswith("##")
            continue
        if not line:
            if para:
                break
            continue
        if seen_h2 or not line.startswith(("|", "<", "-", "!")):
            para.append(line)
    out = " ".join(para)
    for pattern, repl in MD_INLINE:
        out = pattern.sub(repl, out)
    out = out.strip()
    if len(out) > 190:
        cut = out[:190]
        stop = max(cut.rfind(". "), cut.rfind("; "))
        out = cut[:stop + 1] if stop > 80 else cut.rsplit(" ", 1)[0] + "\u2026"
    return out


def load_stdlib(lang: str) -> list[dict]:
    items = []
    for d in stdlib_pkg_dirs(lang):
        m = STDLIB_PKG_RE.match(d.name)
        num, slug = m.group(1), m.group(2)
        guide = d / "GUIDE.md"
        meta = doc_meta(guide, stdlib_pkg_title(slug)) if guide.exists() \
            else {"title": stdlib_pkg_title(slug), "summary": "", "minutes": 1}
        levels = stdlib_levels(lang, d)
        meta["summary"] = stdlib_summary(guide) or meta["summary"]
        # ~8 minutes a level to read, run and poke at, on top of the guide
        meta["minutes"] += 8 * len(levels)
        items.append({
            "id": d.name, "num": num, "slug": slug,
            # the card shows the import name; the GUIDE's own H1 is kept
            # separately so the package page can print it as written
            "title": stdlib_pkg_title(slug),
            "guideTitle": meta["title"],
            "summary": meta["summary"], "minutes": meta["minutes"],
            "hasGuide": guide.exists(),
            "levels": levels,
        })
    return items


def stdlib_guide(lang: str, pkg: str) -> dict:
    if not STDLIB_PKG_RE.fullmatch(pkg or ""):
        return {"exists": False, "markdown": ""}
    return read_markdown(STDLIB_ROOTS[lang] / pkg / "GUIDE.md")


def stdlib_level_path(lang: str, pkg: str, level: str) -> Path | None:
    """Both parts are matched whole against fixed shapes — no dots, no
    slashes — so a request cannot walk out of the curriculum folder."""
    if not STDLIB_PKG_RE.fullmatch(pkg or ""):
        return None
    if not (STDLIB_LEVEL_RE.fullmatch(level or "") or level == STDLIB_DSA):
        return None
    base = STDLIB_ROOTS[lang] / pkg
    return base / level / "main.go" if lang == "go" else base / f"{level}.py"


def read_stdlib_file(lang: str, pkg: str, level: str) -> dict:
    """Every level file opens with a module docstring (Python) or a leading
    /* */ block (Go) that carries the lesson prose — split off the same way
    an Engineering topic's explanation is (read_eng_problem), so the Lesson
    tab can render it as prose above the full runnable source."""
    path = stdlib_level_path(lang, pkg, level)
    if not path or not path.exists():
        return {"exists": False, "doc": "", "code": "", "path": ""}
    text = path.read_text()
    doc, _ = (split_go if lang == "go" else split_python)(text)
    return {"exists": True, "doc": doc, "code": text,
            "path": str(path.relative_to(ROOT))}


def run_stdlib(lang: str, pkg: str, level: str, code: str) -> dict:
    """Runs the buffer the learner is looking at — never the file on disk.

    Python runs alone in a scratch directory. A Go level imports nothing but the
    stdlib yet still compiles inside the GoStdLib module, so it gets a scratch
    package inside a copy of that module."""
    timeout = RUN_TIMEOUT_STDLIB_GO if lang == "go" else RUN_TIMEOUT_STDLIB_PY
    if not code.strip():
        return {"ok": False, "stdout": "", "stderr": "Nothing to run — the editor is empty.",
                "exitCode": -1, "ms": 0}
    if stdlib_level_path(lang, pkg, level) is None:
        return {"ok": False, "stdout": "", "stderr": "Unknown package or level.",
                "exitCode": -1, "ms": 0}
    if lang == "py":
        job = {"kind": "python", "args": ["main.py"], "timeout": timeout, "files": {"main.py": code}}
    else:
        job = {"kind": "go-run", "pkg": SCRATCH_PKG, "timeout": timeout,
               "files": sandbox.stage_go_module(STDLIB_ROOTS["go"], [], {f"{SCRATCH_PKG}/main.go": code})}
    return timed_out_message(code_runner().run(job), timeout,
                             "likely an infinite loop, a benchmark that is too big, "
                             "or something waiting on input.")


# ----------------------------------------------------------------------------
# API — Foundation ladders + labs, runnable in-browser
#
#   API/REST/Theory.md                                            the type's theory doc
#   API/REST/Foundation/python/00_single_endpoint_and_how_it_works.py
#   API/REST/Foundation/golang/00_single_endpoint_and_how_it_works/main.go
#   API/REST/labs/python/01_crud_stdlib.py
#   API/REST/labs/golang/01_servemux_basics/main.go
#
# Same globbing principle as PyStdLib/GoStdLib above: nothing is hardcoded, a
# new level or lab needs no server change, only a page reload. Foundation
# files are fully worked, self-checking examples (see api-foundation-teaching-
# order.md) — not fill-in-the-blank stubs like PyDSA — so the editor lets you
# rewrite and rerun them, never a question/solution split.
# ----------------------------------------------------------------------------
API_TYPES = ["REST", "GraphQL", "Protobuf", "gRPC", "WebSockets", "Webhooks", "SOAP", "Gateway", "Observability"]
API_LEVEL_RE = re.compile(r"^(\d{2})_([a-z0-9_]+)$")
RUN_TIMEOUT_API_PY = 30
RUN_TIMEOUT_API_GO = 45


def api_python_bin() -> str:
    venv = API_DIR / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else python_bin()


def api_ladder(type_name: str, section: str) -> list[dict]:
    """section is 'Foundation' or 'labs'. A Python level is one NN_slug.py file;
    a Go level is NN_slug/main.go. Paired into one row per slug when both exist
    (most do; a few levels are one language only, e.g. Protobuf's buf/protoc
    steps, and that is expected, not a gap)."""
    base = API_DIR / type_name / section
    rows: dict[str, dict] = {}
    py_dir = base / "python"
    if py_dir.exists():
        for f in sorted(py_dir.glob("[0-9][0-9]_*.py")):
            m = API_LEVEL_RE.match(f.stem)
            if not m:
                continue
            rows.setdefault(f.stem, {"id": f.stem, "num": m.group(1), "slug": m.group(2)})["py"] = True
    go_dir = base / "golang"
    if go_dir.exists():
        for d in sorted(go_dir.iterdir()):
            if not d.is_dir() or not (d / "main.go").exists():
                continue
            m = API_LEVEL_RE.match(d.name)
            if not m:
                continue
            rows.setdefault(d.name, {"id": d.name, "num": m.group(1), "slug": m.group(2)})["go"] = True
    out = []
    for key in sorted(rows):
        r = rows[key]
        out.append({
            "id": r["id"], "num": r["num"], "slug": r["slug"],
            "title": eng_prettify(r["slug"]),
            "has": {"py": r.get("py", False), "go": r.get("go", False)},
        })
    return out


def load_api_types() -> list[dict]:
    """One row per API style, for the module's main page."""
    out = []
    for t in API_TYPES:
        theory = API_DIR / t / "Theory.md"
        meta = doc_meta(theory, t) if theory.exists() else {"title": t, "summary": "", "minutes": 1}
        out.append({
            "id": t, "title": t, "summary": meta["summary"],
            "hasTheory": theory.exists(),
            "foundationCount": len(api_ladder(t, "Foundation")),
            "labsCount": len(api_ladder(t, "labs")),
        })
    return out


def load_api_type(type_name: str) -> dict:
    """Everything one API style's own page needs: its theory link and both
    runnable ladders, so a learner can pick any other level without leaving
    the page (the "main page of each topic" navigation)."""
    if type_name not in API_TYPES:
        return {"exists": False}
    theory = API_DIR / type_name / "Theory.md"
    meta = doc_meta(theory, type_name) if theory.exists() else None
    i = API_TYPES.index(type_name)
    return {
        "exists": True, "id": type_name,
        "hasTheory": theory.exists(),
        "theorySummary": meta["summary"] if meta else "",
        "foundation": api_ladder(type_name, "Foundation"),
        "labs": api_ladder(type_name, "labs"),
        "prevType": API_TYPES[i - 1] if i > 0 else None,
        "nextType": API_TYPES[i + 1] if i < len(API_TYPES) - 1 else None,
    }


def api_resolve(type_name: str, section: str, level_id: str, lang: str) -> Path | None:
    """Every part matched whole against a fixed shape — no dots, no slashes —
    so a request cannot walk out of the API/ folder."""
    if type_name not in API_TYPES or section not in ("Foundation", "labs"):
        return None
    if not API_LEVEL_RE.fullmatch(level_id or ""):
        return None
    base = API_DIR / type_name / section
    if lang == "go":
        return base / "golang" / level_id / "main.go"
    if lang == "py":
        return base / "python" / f"{level_id}.py"
    return None


def read_api_file(type_name: str, section: str, level_id: str, lang: str) -> dict:
    path = api_resolve(type_name, section, level_id, lang)
    if not path or not path.exists():
        return {"exists": False, "doc": "", "code": "", "path": ""}
    text = path.read_text()
    doc, code = (split_go if lang == "go" else split_python)(text)
    return {"exists": True, "doc": doc, "code": code, "path": str(path.relative_to(ROOT))}


def run_api_file(type_name: str, section: str, level_id: str, lang: str, code: str) -> dict:
    """Runs the buffer the learner is looking at — never the file on disk (same
    principle as run_stdlib above). Python: the level's sibling files (some
    Protobuf/gRPC levels import generated *_pb2 / *_pb2_grpc stubs by bare
    name) go into the scratch directory alongside the edited code, so those
    imports still resolve, using the content/data-and-apis/API/.venv interpreter that has fastapi,
    strawberry, grpcio, websockets etc. installed. Go: a scratch package
    inside a copy of the dsapractice/api module (with the generated packages
    it imports), so it picks up its real dependencies (gin, echo, coder/websocket...)."""
    timeout = RUN_TIMEOUT_API_GO if lang == "go" else RUN_TIMEOUT_API_PY
    if not code.strip():
        return {"ok": False, "stdout": "", "stderr": "Nothing to run — the editor is empty.",
                "exitCode": -1, "ms": 0}
    target = api_resolve(type_name, section, level_id, lang)
    if not target or not target.exists():
        return {"ok": False, "stdout": "", "stderr": "Unknown type, section, level or language.",
                "exitCode": -1, "ms": 0}
    if lang == "go":
        job = {"kind": "go-run", "pkg": SCRATCH_PKG, "timeout": timeout,
               "files": sandbox.stage_go_module(API_DIR, [], {f"{SCRATCH_PKG}/main.go": code})}
    else:
        files = {k: v for k, v in sandbox.dir_files(target.parent).items() if k.endswith(".py")}
        files[target.name] = code
        job = {"kind": "python", "python": "api", "args": [target.name], "timeout": timeout,
               "files": files}
    return timed_out_message(code_runner().run(job), timeout,
                             "likely an infinite loop, a deadlock, or a server that never shuts down.")


# ----------------------------------------------------------------------------
# SoftwareDesign — one ordered path: README, 14 chapters, then LLD practice
# ----------------------------------------------------------------------------
SWD_CHAPTER_PARTS = [
    ("Part 0 · Before you start", ("00",)),
    ("Part 1 · Foundations", ("01", "02", "03", "04")),
    ("Part 2 · Code that survives change", ("05", "06", "07")),
    ("Part 3 · Services in production", ("08", "09", "10", "11", "12")),
    ("Part 4 · Leading design & the LLD interview", ("13", "14")),
    ("Part 5 · Extended toolkit & field reference", ("15",)),
]
SWD_LLD_SETS = [
    ("LLD practice 1 · Warm-up", ("008", "009", "003")),
    ("LLD practice 2 · Core set", ("001", "002", "004", "005", "006")),
    ("LLD practice 3 · Breadth", ("007", "010", "011", "012")),
    ("LLD practice 4 · Tier 2", ("013", "014", "015", "016", "017")),
    ("LLD practice 5 · Tier 2 extended", ("018", "019", "020")),
]
LLD_TITLE_RE = re.compile(r"^LLD\s+(\d{3})\s*·\s*(.+?)\s*(?:\[(Tier\s*\d)\])?\s*$", re.M)


def load_lld_problems() -> list[dict]:
    """LLD problems in recommended practice order (see the LLD playbook §14)."""
    root = ENG_ROOTS["lld"]
    if not root.exists():
        return []
    found = {}
    for q in root.glob("*_question.py"):
        stem = q.name[: -len("_question.py")]
        if not LLD_ID_RE.match(stem):
            continue
        num, _, slug = stem.partition("_")
        doc, _ = split_python(q.read_text())
        m = LLD_TITLE_RE.search(doc)
        summary = ""
        prob = re.search(r"^PROBLEM\s*\n-+\n(.+?)\n\s*\n", doc, re.M | re.S)
        if prob:
            summary = " ".join(prob.group(1).split())
            if len(summary) > 220:
                summary = summary[:217].rsplit(" ", 1)[0] + "…"
        found[num] = {
            "id": stem, "num": num, "slug": slug, "kind": "lld",
            "title": m.group(2) if m else eng_prettify(slug),
            "tier": m.group(3) if m and m.group(3) else "",
            "summary": summary, "minutes": 45,
            "has": {"explanation": True,
                    "solution": (root / f"{stem}_solution.py").exists(),
                    "test": False},
        }
    items = []
    for group, nums in SWD_LLD_SETS:
        items += [{**found.pop(n), "group": group} for n in nums if n in found]
    items += [{**found[n], "group": "LLD practice · More"} for n in sorted(found)]
    return items


def load_software_design() -> list[dict]:
    if not SOFTWARE_DESIGN_DIR.exists():
        return []
    items: list[dict] = []
    readme = SOFTWARE_DESIGN_DIR / "README.md"
    if readme.exists():
        items.append({"id": "README", "num": "", "kind": "doc", "group": "Start here",
                      **doc_meta(readme, "Start here")})
    chapters = {}
    for path in SOFTWARE_DESIGN_DIR.glob("*.md"):
        m = re.match(r"^(\d{2})_(.+)\.md$", path.name)
        if m:
            chapters[m.group(1)] = {"id": path.stem, "num": m.group(1), "kind": "doc",
                                    **doc_meta(path, m.group(2).replace("_", " ").title())}
    for group, nums in SWD_CHAPTER_PARTS:
        items += [{**chapters.pop(n), "group": group} for n in nums if n in chapters]
    items += [{**chapters[n], "group": "More chapters"} for n in sorted(chapters)]
    items += load_lld_problems()
    step = 0
    for it in items:                      # one running step number: the order to work in
        it["step"] = step
        step += 1
    return items


def safe_md(base_dir: Path, doc_id: str) -> Path | None:
    """Resolves doc_id to a .md file inside base_dir, refusing path traversal."""
    if not doc_id or "/" in doc_id or "\\" in doc_id:
        return None
    path = (base_dir / f"{doc_id}.md").resolve()
    if not str(path).startswith(str(base_dir.resolve()) + os.sep):
        return None
    return path


FRONT_MATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.S)


def read_markdown(path: Path | None) -> dict:
    if not path or not path.exists():
        return {"exists": False, "markdown": ""}
    # A leading YAML front-matter block (title/description) is metadata, not content:
    # left in, the reader would render it as a giant paragraph above the title.
    return {"exists": True, "markdown": FRONT_MATTER_RE.sub("", path.read_text(), count=1)}


# ----------------------------------------------------------------------------
# Splitting a source file into prose + code
# ----------------------------------------------------------------------------
PY_DOC = re.compile(r'^\s*[rRuU]?(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', re.S)
GO_DOC = re.compile(r"/\*(.*?)\*/", re.S)


def split_python(text: str) -> tuple[str, str]:
    m = PY_DOC.match(text)
    if not m:
        return "", text
    return m.group(1).strip("\n"), text[m.end():].lstrip("\n")


def split_go(text: str) -> tuple[str, str]:
    m = GO_DOC.search(text)
    if not m:
        return "", text
    doc = m.group(1).strip("\n")
    code = (text[:m.start()] + text[m.end():]).replace("\n\n\n", "\n\n").strip("\n")
    return doc, code + "\n"


GO_MAIN_STUB = """

func main() {
\t// TODO: call your function with the examples from the problem statement
\t// and print the results. An empty main compiles, so you can run right away.
}
"""


def read_problem(topic: str, seq: str, kind: str, lang: str) -> dict | None:
    for p in load_curriculum():
        if p["topic"] == topic and p["seq"] == seq:
            break
    else:
        return None

    path = (py_path if lang == "py" else go_path)(topic, seq, p["slug"], kind)
    if not path.exists():
        return {"exists": False, "doc": "", "code": "", "path": ""}

    text = path.read_text()
    doc, code = (split_python if lang == "py" else split_go)(text)

    # A Go `question.go` has no main(), so it cannot run standalone. Append an
    # empty one so the buffer compiles the moment it is opened.
    if lang == "go" and kind == "question" and "func main(" not in code:
        code = code.rstrip("\n") + "\n" + GO_MAIN_STUB

    return {
        "exists": True,
        "doc": doc,
        "code": code,
        "path": str(path.relative_to(ROOT)),
    }


# ----------------------------------------------------------------------------
# DSA pattern map — the per-problem "move / idea / trap" rows that every
# PyDSA/<topic>/_TOPIC_GUIDE.md keeps between <!-- problem-map:start/end -->,
# plus a short statement per problem for the recognition drill. The webapp
# builds its hint ladder, "same move" families and drill cards from this.
# ----------------------------------------------------------------------------
MAP_ROW = re.compile(r"^\|\s*\[(\d{3})\s*·[^\]]*\]\([^)]*\)[^|]*\|\s*(.*?)\s*\|\s*(.*)\s*\|\s*$")
MAP_MD_BOLD = re.compile(r"\*\*|__")


def _md_plain(s: str) -> str:
    """Guide cells are markdown; the app renders them as plain text + `code`."""
    s = MAP_MD_BOLD.sub("", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?!\w)", r"\1", s)   # *emphasis*
    return s.replace("<br>", " ").strip()


def _question_statement(path: Path) -> dict:
    """First paragraphs of the problem, one example and the constraints —
    what a candidate sees in the first minute, minus the curriculum's own
    commentary (which usually names the technique)."""
    if not path.exists():
        return {}
    doc, _ = split_python(path.read_text())
    lines = doc.split("\n")
    # skip the ==== banner ==== (it carries the title, which often names the pattern)
    rules = [k for k, l in enumerate(lines[:10]) if re.match(r"^={6,}$", l.strip())]
    start = rules[1] + 1 if len(rules) >= 2 else 0
    body = lines[start:]
    # an explicit PROBLEM section, when there is one
    for k, l in enumerate(body):
        if l.strip() == "PROBLEM" and k + 1 < len(body) and re.match(r"^-{3,}$", body[k + 1].strip()):
            body = body[k + 2:]
            break
    text, example, constraints = [], [], []
    mode = "text"
    for k, l in enumerate(body):
        s = l.strip()
        if re.match(r"^={6,}$", s):
            break
        nxt = body[k + 1].strip() if k + 1 < len(body) else ""
        if mode == "text" and s and re.match(r"^-{3,}$", nxt) and not re.match(r"^EXAMPLES?$", s):
            break                          # a curriculum section (WHAT MAKES A GRAPH A TREE, …)
        if re.match(r"^(EXAMPLES?|Example\s*1\s*:?)", s):
            mode = "example"
            if s.lower().startswith("example 1") and ":" in s and s.split(":", 1)[1].strip():
                example.append(s.split(":", 1)[1].strip())
            continue
        if re.match(r"^(Example\s*[2-9]|EXAMPLE\s*[2-9])", s):
            mode = "skip"
            continue
        if re.match(r"^(CONSTRAINTS|Constraints\s*:)", s):
            mode = "constraints"
            continue
        if re.match(r"^-{3,}$", s):
            continue
        if mode != "text" and re.match(r"^[A-Z][A-Z0-9 /&()'.,:-]{3,}$", s) and not l.startswith(" "):
            if mode == "constraints":
                break
            mode = "skip"
            continue
        if mode == "text":
            text.append(l)
        elif mode == "example" and s and len(example) < 3 and re.match(r"^(Input|Output)", s):
            example.append(s)
        elif mode == "constraints" and s and len(constraints) < 4 and not s.startswith("<-"):
            constraints.append(re.sub(r"\s+<-.*$", "", s))
    paras, buf = [], []
    for l in text + [""]:
        if l.strip():
            # list items and aligned interface tables keep their own line (rendered pre-line)
            if buf and (re.match(r"^\s*(?:[-*•]|\d+[.)])\s", l) or re.search(r"\S\s{3,}\S", l.strip())):
                buf.append("\n" + l.strip())
            else:
                buf.append(l.strip())
        elif buf:
            paras.append(" ".join(buf).replace(" \n", "\n"))
            buf = []
    # parenthetical asides are the curriculum talking, and they tend to name the pattern
    paras = [p for p in paras if not p.startswith("(") and not re.match(r"^[A-Z][A-Z ]{3,}$", p)]
    out, n = [], 0
    for p in paras:
        if n > 650 and out:
            break
        out.append(p)
        n += len(p)
    return {"text": out, "example": example[:2], "constraints": constraints}


_dsa_map_cache: dict = {"key": None, "value": None}


def load_dsa_map() -> dict:
    guides = sorted(PY_DSA.glob("*/_TOPIC_GUIDE.md"))
    questions = sorted(PY_DSA.glob("*/*_question.py"))
    key = (TSV.stat().st_mtime, max((p.stat().st_mtime for p in guides + questions), default=0))
    if _dsa_map_cache["key"] == key:
        return _dsa_map_cache["value"]

    problems = {}
    for g in guides:
        topic = g.parent.name
        text = g.read_text()
        a, b = text.find("<!-- problem-map:start -->"), text.find("<!-- problem-map:end -->")
        if a < 0 or b < 0:
            continue
        for line in text[a:b].split("\n"):
            m = MAP_ROW.match(line)
            if not m:
                continue
            seq, move, rest = m.groups()
            idea, _, trap = rest.partition("**Trap:**")
            problems[f"{topic}/{seq}"] = {
                "move": _md_plain(move),
                "idea": _md_plain(idea).rstrip(" ."),
                "trap": _md_plain(trap),
            }
    for p in load_curriculum():
        st = _question_statement(py_path(p["topic"], p["seq"], p["slug"], "question"))
        if st:
            problems.setdefault(p["id"], {})["statement"] = st
    value = {"problems": problems}
    _dsa_map_cache.update(key=key, value=value)
    return value


def read_guide(topic: str, lang: str) -> dict:
    path = (PY_DSA if lang == "py" else GO_DSA) / topic / "_TOPIC_GUIDE.md"
    if not path.exists():
        return {"exists": False, "markdown": ""}
    return {
        "exists": True,
        "markdown": path.read_text(),
        "path": str(path.relative_to(ROOT)),
    }


# ----------------------------------------------------------------------------
# Code execution
# ----------------------------------------------------------------------------
def code_runner():
    """Where code runs: set by main() (the runner container in hosted mode),
    otherwise this machine's toolchains."""
    global RUNNER
    if RUNNER is None:
        if AUTH_ENABLED:      # the hosted guide never runs code with this machine's toolchains
            RUNNER = sandbox.RemoteRunner(RUNNER_SOCKET) if RUNNER_SOCKET else sandbox.DisabledRunner(CODE_RUN_OFF)
        else:
            RUNNER = sandbox.LocalRunner(
                {"default": python_bin(), "eng": eng_python_bin(), "api": api_python_bin()}, go_bin())
    return RUNNER


def timed_out_message(result: dict, timeout: int, why: str) -> dict:
    if result.get("timeout"):
        return {**result, "stderr": f"Timed out after {timeout}s — {why}", "ms": timeout * 1000}
    return result


def run_python(code: str) -> dict:
    return timed_out_message(
        code_runner().run({"kind": "python", "args": ["main.py"], "timeout": RUN_TIMEOUT_PY,
                           "files": {"main.py": code}}),
        RUN_TIMEOUT_PY, "likely an infinite loop or runaway recursion.")


def run_go(code: str) -> dict:
    return timed_out_message(
        code_runner().run({"kind": "go-run", "timeout": RUN_TIMEOUT_GO,
                           "files": {"main.go": code, "go.mod": "module dsascratch\n\ngo 1.21\n"}}),
        RUN_TIMEOUT_GO, "likely an infinite loop, or a very slow first build.")


def format_go(code: str) -> dict:
    r = code_runner().run({"kind": "gofmt", "stdin": code, "timeout": 10, "files": {}})
    if r.get("ok"):
        return {"ok": True, "code": r["stdout"]}
    error = "gofmt timed out." if r.get("timeout") else (r.get("stderr") or "gofmt failed.")
    return {"ok": False, "code": code, "error": error}


# ----------------------------------------------------------------------------
# GET routes
# ----------------------------------------------------------------------------
def _reply(obj, code: int = 200) -> tuple[object, int]:
    return obj, code


def api_get(p: str, q: dict[str, list[str]]) -> tuple[object, int] | None:
    """Answer GET /api/*: (JSON payload, HTTP status), or None if `p` is not an API route.

    The HTTP handler below and the static-site builder (build_static.py) both call
    this, so a deployed static build serves exactly what the local server does.
    """
    if p == "/api/bootstrap":
        problems = load_curriculum()
        with _state_lock:
            state = load_state()
        return _reply({
            "problems": problems,
            "topics": load_topics(problems),
            "engTopics": {
                "go": load_eng_curriculum("go"),
                "py": load_eng_curriculum("py"),
                "lld": load_eng_curriculum("lld"),
            },
            "state": state,
            "runtimes": code_runner().available,
            "root": str(ROOT),
        })
    elif p == "/api/eng-problem":
        r = read_eng_problem(q.get("lang", ["go"])[0], q.get("topic", [""])[0],
                              q.get("kind", ["explanation"])[0])
        return _reply(r, 200 if r["exists"] else 404)
    elif p == "/api/problem":
        r = read_problem(q.get("topic", [""])[0], q.get("seq", [""])[0],
                         q.get("kind", ["question"])[0],
                         q.get("lang", ["py"])[0])
        return _reply(r if r else {"error": "unknown problem"},
                      200 if r else 404)
    elif p == "/api/guide":
        return _reply(read_guide(q.get("topic", [""])[0],
                                 q.get("lang", ["py"])[0]))
    elif p == "/api/dsa-map":
        return _reply(load_dsa_map())
    elif p == "/api/dsa-guides":
        return _reply({"items": load_dsa_guides(q.get("lang", ["py"])[0])})
    elif p == "/api/dsa-guide-doc":
        return _reply(read_dsa_guide(q.get("id", [""])[0], q.get("lang", ["py"])[0]))
    elif p == "/api/system-design-guide":
        if SYSTEM_DESIGN_GUIDE.exists():
            # The in-app reader starts with the active curriculum, then
            # continues into the full reference and its first paired drill.
            # Files remain separate on disk so a learner can solve a prompt
            # before opening its solution.
            parts = []
            building_blocks_dir = SYSTEM_DESIGN / "building_blocks"
            for path in (
                SYSTEM_DESIGN / "README.md",
                *sorted(building_blocks_dir.glob("*.md")),
                SYSTEM_DESIGN / "02_problem_catalog.md",
                SYSTEM_DESIGN / "problems" / "001_url_shortener_question.md",
                SYSTEM_DESIGN / "solutions" / "001_url_shortener_solution.md",
                SYSTEM_DESIGN / "03_practice_prompts.md",
                SYSTEM_DESIGN / "04_practice_answers.md",
                SYSTEM_DESIGN / "05_architecture_blueprints.md",
                SYSTEM_DESIGN / "solutions" / "009_search_and_autocomplete_solution.md",
                SYSTEM_DESIGN / "solutions" / "002_rate_limiter_solution.md",
                SYSTEM_DESIGN / "solutions" / "003_pastebin_solution.md",
                SYSTEM_DESIGN / "solutions" / "004_notification_platform_solution.md",
                SYSTEM_DESIGN / "solutions" / "005_photo_pipeline_solution.md",
                SYSTEM_DESIGN / "solutions" / "006_chat_solution.md",
                SYSTEM_DESIGN_GUIDE,
            ):
                if path.exists():
                    parts.append(path.read_text())
            return _reply({"exists": True, "markdown": "\n\n---\n\n".join(parts)})
        else:
            return _reply({"exists": False, "markdown": ""}, 404)
    elif p == "/api/sd":
        return _reply({"items": load_system_design()})
    elif p == "/api/sd-doc":
        return _reply(read_system_design(q.get("id", [""])[0]))
    elif p == "/api/roadmap":
        return _reply({"items": load_roadmap()})
    elif p == "/api/roadmap-doc":
        return _reply(read_markdown(safe_md(ROADMAP_DIR, q.get("id", [""])[0])))
    elif p == "/api/library-guides":
        return _reply({"items": load_library_guides()})
    elif p == "/api/library-guide-doc":
        return _reply(read_markdown(safe_md(LIBRARY_GUIDES_DIR, q.get("id", [""])[0])))
    elif p == "/api/apis":
        return _reply({"items": load_api()})
    elif p == "/api/apis-doc":
        # The ID is now something like "REST/REST_API_Guide"
        req_id = q.get("id", [""])[0]
        if req_id:
            return _reply(read_markdown(API_DIR / f"{req_id}.md"))
        else:
            return _reply({"content": "Not found", "title": "Not Found"})
    elif p == "/api/api-types":
        return _reply({"items": load_api_types()})
    elif p == "/api/api-type":
        r = load_api_type(q.get("type", [""])[0])
        return _reply(r, 200 if r["exists"] else 404)
    elif p == "/api/api-file":
        r = read_api_file(q.get("type", [""])[0], q.get("section", ["Foundation"])[0],
                           q.get("level", [""])[0], q.get("lang", ["py"])[0])
        return _reply(r, 200 if r["exists"] else 404)
    elif p == "/api/agentic-ai":
        return _reply({"items": load_agentic_ai()})
    elif p == "/api/agentic-ai-doc":
        return _reply(read_markdown(safe_md(AGENTIC_AI_DIR, q.get("id", [""])[0])))
    elif p == "/api/track":
        return _reply({"items": load_track(q.get("m", [""])[0])})
    elif p == "/api/track-doc":
        base = TRACK_DIRS.get(q.get("m", [""])[0])
        path = safe_md(base, q.get("id", [""])[0]) if base else None
        return _reply(read_markdown(path) if path else {"exists": False, "markdown": ""})
    elif p == "/api/cs-fundamentals":
        return _reply({"items": load_cs_fundamentals()})
    elif p == "/api/cs-fundamentals-doc":
        return _reply(read_markdown(safe_md(CS_FUNDAMENTALS_DIR, q.get("id", [""])[0])))
    elif p == "/api/google-behavioral":
        return _reply({"items": load_google_behavioral()})
    elif p == "/api/google-behavioral-doc":
        return _reply(read_markdown(safe_md(GOOGLE_BEHAVIORAL_DIR, q.get("id", [""])[0])))
    elif p == "/api/sql":
        return _reply({"items": load_sql()})
    elif p == "/api/sql-doc":
        return _reply(read_sql(q.get("id", [""])[0]))
    elif p == "/api/nosql":
        return _reply({"items": load_nosql()})
    elif p == "/api/nosql-doc":
        return _reply(read_nosql(q.get("id", [""])[0]))
    elif p == "/api/query-lab":
        r = load_query_lab(q.get("engine", [""])[0])
        return _reply(r, 200 if r["exists"] else 404)
    elif p == "/api/query-lab-data":
        r = read_query_lab_data(q.get("engine", [""])[0], q.get("dataset", [""])[0])
        return _reply(r, 200 if r["exists"] else 404)
    elif p == "/api/stdlib":
        return _reply({"items": load_stdlib(stdlib_lang(q.get("lang", ["py"])[0]))})
    elif p == "/api/stdlib-doc":
        return _reply(stdlib_guide(stdlib_lang(q.get("lang", ["py"])[0]),
                                   q.get("id", [""])[0]))
    elif p == "/api/stdlib-file":
        return _reply(read_stdlib_file(stdlib_lang(q.get("lang", ["py"])[0]),
                                       q.get("pkg", [""])[0], q.get("level", [""])[0]))
    elif p == "/api/software-design":
        return _reply({"items": load_software_design()})
    elif p == "/api/software-design-doc":
        return _reply(read_markdown(safe_md(SOFTWARE_DESIGN_DIR, q.get("id", [""])[0])))
    elif p == "/api/state":
        with _state_lock:
            return _reply(load_state())

    return None


# Files the sign-in page needs before anyone is signed in (hosted mode).
PUBLIC_STATIC = frozenset({"login.html", "login.js", "auth.css", "logo.svg", "theme-init.js"})
PUBLIC_PREFIXES = ("vendor/fonts/",)

# Content-Security-Policy for the hosted app: scripts only from this origin (the
# Mongo shell in the Query Lab and PGlite need eval / WebAssembly), no framing.
CSP = ("default-src 'self'; script-src 'self' 'unsafe-eval' 'wasm-unsafe-eval'; "
       "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; font-src 'self' data:; "
       "connect-src 'self' blob: data:; worker-src 'self' blob:; frame-ancestors 'none'; "
       "base-uri 'self'; form-action 'self'; object-src 'none'")

STATIC_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".json": "application/json",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".ttf": "font/ttf",
    ".png": "image/png",
    ".wasm": "application/wasm",
    ".mjs": "application/javascript; charset=utf-8",
}

GOOGLE_START_RATE = auth.RateLimiter(30, 600)     # Google sign-in starts per client IP

RUN_ROUTES = frozenset({"/api/run", "/api/eng-run", "/api/stdlib-run", "/api/api-run", "/api/format"})
RUN_RATE_MINUTE = auth.RateLimiter(int(os.environ.get("EG_RUNS_PER_MINUTE", "20")), 60)
RUN_RATE_HOUR = auth.RateLimiter(int(os.environ.get("EG_RUNS_PER_HOUR", "300")), 3600)
_runs_lock = threading.Lock()
_runs_in_flight: set = set()


def dispatch_run(p: str, body: dict) -> dict:
    """POST /api/run, /api/eng-run, /api/stdlib-run, /api/api-run, /api/format."""
    s = lambda key, default="": str(body.get(key) or default)       # noqa: E731
    if p == "/api/run":
        code = s("code")
        if not code.strip():
            return {"ok": False, "stdout": "", "exitCode": -1, "ms": 0,
                    "stderr": "Nothing to run — the editor is empty."}
        return run_python(code) if s("lang", "py") == "py" else run_go(code)
    if p == "/api/eng-run":
        return run_eng(s("lang", "go"), s("topic"), s("code"))
    if p == "/api/stdlib-run":
        return run_stdlib(stdlib_lang(s("lang", "py")), s("pkg"), s("level"), s("code"))
    if p == "/api/api-run":
        return run_api_file(s("type"), s("section", "Foundation"), s("level"), s("lang", "py"), s("code"))
    return format_go(s("code"))


def hosted_config_js() -> bytes:
    """static/config.js as the hosted app serves it."""
    return ("/* Served by server.py in hosted mode (EG_AUTH=1). */\n"
            "window.EG_STATIC = false;\nwindow.EG_AUTH = true;\nwindow.EG_PROTECT = true;\n"
            f"window.EG_UPGRADE_URL = {json.dumps(UPGRADE_URL)};\n").encode()


# ----------------------------------------------------------------------------
# HTTP handler
# ----------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "DSAStudio/1.0"
    sys_version = ""

    def log_message(self, fmt, *args):  # quieter console
        if "/api/run" in (args[0] if args else ""):
            sys.stderr.write(f"  run  {args[0]}\n")

    # -- helpers ------------------------------------------------------------
    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("X-Frame-Options", "DENY")
        if AUTH_ENABLED:
            self.send_header("Content-Security-Policy", CSP)
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            if COOKIE_SECURE:
                self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

    def _send(self, code: int, body: bytes, ctype: str, headers: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        for k, v in (headers or {}).items():
            for one in (v if isinstance(v, list) else [v]):
                self.send_header(k, one)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass        # the browser moved on (navigation, reload) before the answer arrived

    def _json(self, obj, code: int = 200, headers: dict | None = None) -> None:
        self._send(code, json.dumps(obj).encode(), "application/json", headers)

    def _redirect(self, location: str) -> None:
        self._send(302, b"", "text/plain", {"Location": location})

    def _body(self) -> dict:
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return {}
        if n <= 0 or n > MAX_BODY:
            return {}
        try:
            body = json.loads(self.rfile.read(n))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
        return body if isinstance(body, dict) else {}

    def _static(self, rel: str) -> None:
        rel = rel.lstrip("/") or "index.html"
        if AUTH_ENABLED and rel == "config.js":
            self._send(200, hosted_config_js(), STATIC_TYPES[".js"])
            return
        path = (STATIC / rel).resolve()
        if not path.is_relative_to(STATIC.resolve()) or not path.is_file():
            self._send(404, b"Not found", "text/plain")
            return
        self._send(200, path.read_bytes(), STATIC_TYPES.get(path.suffix, "application/octet-stream"))

    # -- hosted mode: who is asking ------------------------------------------
    def _client_ip(self) -> str:
        if TRUST_PROXY:
            fwd = self.headers.get("X-Forwarded-For", "")
            if fwd:
                return fwd.split(",")[-1].strip()      # the address our own proxy saw
        return self.client_address[0]

    def _cookie(self, wanted: str) -> str | None:
        # Parsed by hand: http.cookies drops every cookie after one it cannot parse,
        # and other apps on the same host can set those.
        for part in (self.headers.get("Cookie") or "").split(";"):
            name, _, value = part.strip().partition("=")
            if name == wanted and value:
                return value
        return None

    def _session_token(self) -> str | None:
        return self._cookie(SESSION_COOKIE)

    def _oauth_cookie(self, value: str, max_age: int) -> str:
        # Lax, not Strict: it has to come back on the top-level redirect from Google.
        parts = [f"{OAUTH_COOKIE}={value}", "Path=/", "HttpOnly", "SameSite=Lax", f"Max-Age={max_age}"]
        if COOKIE_SECURE:
            parts.append("Secure")
        return "; ".join(parts)

    def _google_redirect_uri(self) -> str:
        if PUBLIC_ORIGIN:
            return f"{PUBLIC_ORIGIN}/api/auth/google/callback"
        host = (self.headers.get("X-Forwarded-Host") if TRUST_PROXY else None) or self.headers.get("Host", "")
        return f"{'https' if COOKIE_SECURE else 'http'}://{host}/api/auth/google/callback"

    def _signin_failed(self, code: str) -> None:
        self._send(302, b"", "text/plain", {
            "Location": f"/login.html?error={code if code in SIGNIN_ERRORS else 'google_failed'}",
            "Set-Cookie": self._oauth_cookie("", 0)})

    def _google_start(self, q: dict) -> None:
        if GOOGLE is None or not GOOGLE.enabled:
            self._signin_failed("google_off")
            return
        if not GOOGLE_START_RATE.allow(f"ip:{self._client_ip()}"):
            self._signin_failed("rate_limited")
            return
        url, binding = GOOGLE.start(self._google_redirect_uri(), (q.get("next") or [""])[0])
        self._send(302, b"", "text/plain", {"Location": url, "Set-Cookie": self._oauth_cookie(binding, 600)})

    def _google_callback(self, q: dict) -> None:
        one = lambda k: (q.get(k) or [""])[0]
        if GOOGLE is None or not GOOGLE.enabled:
            self._signin_failed("google_off")
            return
        if one("error"):                                   # cancelled on Google's screen
            AUTH.take_oauth_state(one("state"), self._cookie(OAUTH_COOKIE) or "")
            self._signin_failed("google_cancelled")
            return
        ip = self._client_ip()
        try:
            email, sub, next_hash = GOOGLE.finish(one("state"), one("code"), self._cookie(OAUTH_COOKIE) or "",
                                                  self._google_redirect_uri())
            token, _ = AUTH.sign_in_google(email, sub, ip, self.headers.get("User-Agent", ""))
        except google_signin.GoogleError as e:
            AUTH.log("google_failed", ip=ip, note=e.reason[:200])
            self._signin_failed("google_failed")
            return
        except auth.AuthError as e:
            self._signin_failed(e.code)
            return
        # A 200 page that moves on by itself, not a 302: this response ends a navigation
        # that started on Google's site, so a redirect from it would still count as
        # cross-site and the browser would hold back the new SameSite=Strict cookie.
        target = "/" + next_hash
        page = (f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={target}">'
                f'<title>Signing in</title><p style="font-family:sans-serif;padding:40px">Signed in. '
                f'<a href="{target}">Continue to the guide</a>.</p>').encode()
        self._send(200, page, "text/html; charset=utf-8", {"Set-Cookie": [
            self._session_cookie(token, auth.SESSION_TTL), self._oauth_cookie("", 0)]})

    def _session_cookie(self, token: str, max_age: int) -> str:
        parts = [f"{SESSION_COOKIE}={token}", "Path=/", "HttpOnly", "SameSite=Strict", f"Max-Age={max_age}"]
        if COOKIE_SECURE:
            parts.append("Secure")
        return "; ".join(parts)

    def _user(self):
        return AUTH.session_user(self._session_token()) if AUTH_ENABLED else None

    def _same_origin(self) -> bool:
        """POSTs must come from our own pages (with SameSite=Strict cookies, defence in depth
        against cross-site request forgery)."""
        origin = self.headers.get("Origin") or ""
        if not origin:
            ref = self.headers.get("Referer") or ""
            origin = f"{urlparse(ref).scheme}://{urlparse(ref).netloc}" if ref else ""
        if not origin:
            return False
        if PUBLIC_ORIGINS:
            return origin.rstrip("/") in PUBLIC_ORIGINS
        host = self.headers.get("X-Forwarded-Host") if TRUST_PROXY else None
        return urlparse(origin).netloc == (host or self.headers.get("Host") or "")

    def _user_state(self, user) -> dict:
        return AUTH.load_progress(user["id"], default_state())

    # -- routes -------------------------------------------------------------
    def do_GET(self) -> None:
        u = urlparse(self.path)
        if AUTH_ENABLED:
            self._hosted_get(u)
            return
        reply = api_get(u.path, parse_qs(u.query))
        if reply is None:
            self._static(u.path)
        else:
            self._json(*reply)

    def _hosted_get(self, u) -> None:
        rel = u.path.lstrip("/")
        # Decide on the normalised path: "vendor/fonts/../app.js" must not pass as public.
        if ".." in rel.split("/") or "\\" in rel:
            self._send(404, b"Not found", "text/plain")
            return
        user = self._user()
        if rel in ("login", "login.html"):
            if user:
                self._redirect("./")
            else:
                self._static("login.html")
            return
        if rel in PUBLIC_STATIC or rel.startswith(PUBLIC_PREFIXES):
            self._static(rel)
            return
        if u.path == "/api/auth/providers":
            self._json({"email": True, "google": bool(GOOGLE and GOOGLE.enabled)})
            return
        if u.path == "/api/auth/google/start":
            self._google_start(parse_qs(u.query))
            return
        if u.path == "/api/auth/google/callback":
            self._google_callback(parse_qs(u.query))
            return
        if u.path == "/api/me":
            self._json(AUTH.account(user) if user else {"error": "signed_out"}, 200 if user else 401)
            return
        if user is None:
            if u.path.startswith("/api/"):
                self._json({"error": "signed_out", "message": "Sign in to continue."}, 401)
            elif rel in ("", "index.html"):
                self._redirect("login.html")
            else:
                self._send(401, b"Sign in first.", "text/plain")
            return
        if not u.path.startswith("/api/"):
            self._static(u.path)
            return
        if not AUTH.allow_api(user):
            self._json({"error": "rate_limited", "message": "Too many requests. Slow down a little."}, 429,
                       {"Retry-After": "60"})
            return
        q = parse_qs(u.query)
        tier = AUTH.effective_tier(user)
        denied = entitlements.check(u.path, q, tier)
        if denied is not None:
            self._json(denied, 403)
            return
        if u.path == "/api/state":
            self._json(self._user_state(user))
            return
        reply = api_get(u.path, q)
        if reply is None:
            self._json({"error": "not_found"}, 404)
            return
        payload, status = reply
        if u.path == "/api/bootstrap":
            payload = {**payload, "state": self._user_state(user), "root": "",
                       "runtimes": code_runner().available, "account": AUTH.account(user)}
        self._json(entitlements.filter_payload(u.path, q, payload, tier), status)

    def do_POST(self) -> None:
        p = urlparse(self.path).path
        if AUTH_ENABLED:
            self._hosted_post(p)
            return
        self._local_post(p, self._body())

    def _hosted_post(self, p: str) -> None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY:
            self._json({"error": "too_large"}, 413)
            return
        if not self._same_origin() or "application/json" not in (self.headers.get("Content-Type") or ""):
            self._json({"error": "forbidden", "message": "Cross-site request refused."}, 403)
            return
        body = self._body()
        ip = self._client_ip()
        try:
            if p == "/api/auth/request-otp":
                self._json(AUTH.request_otp(body.get("email"), ip))
                return
            if p == "/api/auth/verify-otp":
                token, account = AUTH.verify_otp(body.get("email"), body.get("code"), ip,
                                                 self.headers.get("User-Agent", ""))
                self._json({"ok": True, "account": account}, 200,
                           {"Set-Cookie": self._session_cookie(token, auth.SESSION_TTL)})
                return
            if p == "/api/auth/logout":
                AUTH.logout(self._session_token())
                self._json({"ok": True}, 200, {"Set-Cookie": self._session_cookie("", 0)})
                return
            user = self._user()
            if user is None:
                self._json({"error": "signed_out", "message": "Sign in to continue."}, 401)
                return
            if p in RUN_ROUTES:
                self._hosted_run(p, body, user)
            elif p == "/api/state":
                state = default_state()
                state.update(body)
                AUTH.save_progress(user["id"], state)
                self._json({"ok": True})
            elif p == "/api/patch":
                with _state_lock:
                    AUTH.save_progress(user["id"], apply_patch(self._user_state(user), body))
                self._json({"ok": True})
            else:
                self._json({"error": "not_found"}, 404)
        except auth.AuthError as e:
            self._json(e.body(), e.status, {"Retry-After": str(e.retry_after)} if e.retry_after else None)

    def _hosted_run(self, p: str, body: dict, user) -> None:
        """Code runs on the hosted guide: only with a runner container, only for pages
        the reader's plan opens, one at a time per account, rate limited."""
        if not RUNNER_SOCKET:
            self._json({"ok": False, "exitCode": 1, "stdout": "", "stderr": CODE_RUN_OFF,
                        "error": CODE_RUN_OFF, "ms": 0})
            return
        denied = entitlements.check_run(p, body, AUTH.effective_tier(user))
        if denied:
            self._json(denied, 403)
            return
        key = f"user:{user['id']}"
        if not (RUN_RATE_MINUTE.allow(key) and RUN_RATE_HOUR.allow(key)):
            self._json(sandbox.failure("You are running code very often. Wait a minute and try again.",
                                       error="rate_limited"), 429, {"Retry-After": "60"})
            return
        with _runs_lock:
            busy = user["id"] in _runs_in_flight
            _runs_in_flight.add(user["id"])
        if busy:
            self._json(sandbox.failure("Your previous run is still going. Wait for it to finish.",
                                       error="busy"), 429)
            return
        try:
            self._json(dispatch_run(p, body))
        finally:
            with _runs_lock:
                _runs_in_flight.discard(user["id"])

    def _local_post(self, p: str, body: dict) -> None:
        if p in RUN_ROUTES:
            self._json(dispatch_run(p, body))
        elif p == "/api/state":
            with _state_lock:
                save_state(body)
            self._json({"ok": True})
        elif p == "/api/patch":
            # Merge a single problem's record without shipping whole state.
            with _state_lock:
                save_state(apply_patch(load_state(), body))
            self._json({"ok": True})
        else:
            self._send(404, b"Not found", "text/plain")


def open_auth_store():
    """Hosted mode: the account store, or exit with what is missing."""
    mailer = auth.Mailer()
    if not mailer.configured:
        sys.exit("EG_AUTH=1 needs a way to send sign-in codes: set EG_BREVO_API_KEY and EG_MAIL_FROM, "
                 "or EG_SMTP_HOST and EG_MAIL_FROM "
                 "(plus EG_SMTP_USER / EG_SMTP_PASSWORD), or EG_OTP_CONSOLE=1 for local development.")
    if mailer.provider == "console" and not LOOPBACK:
        print("  [warn] EG_OTP_CONSOLE=1 on a public address: codes go to this console, not by email.",
              file=sys.stderr)
    return auth.AuthStore(AUTH_DB, auth.load_secret(AUTH_DB.parent), mailer)


def open_google(store):
    g = google_signin.GoogleSignIn(store)
    if bool(g.client_id) != bool(g.client_secret):
        sys.exit("Sign in with Google needs both EG_GOOGLE_CLIENT_ID and EG_GOOGLE_CLIENT_SECRET.")
    return g


def main() -> None:
    global AUTH, GOOGLE
    if not TSV.exists():
        sys.exit(f"Missing {TSV}. Run this from the DSA-Practice repo.")
    if AUTH_ENABLED:
        AUTH = open_auth_store()       # hosted: writes only next to EG_AUTH_DB (the image's /data volume)
        GOOGLE = open_google(AUTH)
    else:
        DATA.mkdir(parents=True, exist_ok=True)
    if not AUTH_ENABLED and not LOOPBACK:
        sys.exit(f"EG_HOST={HOST}: the local app runs code you send it, so it only binds to loopback. "
                 "Set EG_AUTH=1 for the hosted mode (sign-in; code runs only in the runner container).")

    problems = load_curriculum()
    written = sum(1 for p in problems if p["has"]["pySolution"])
    go_ok = "yes" if go_bin() else "NOT FOUND (Python still runs)"

    try:
        srv = StudioServer((HOST, PORT), Handler)
    except PermissionError:
        sys.exit(f"Cannot bind port {PORT}: permission denied. Ports below 1024 need "
                  f"root on macOS/Linux. Use a port above 1024, e.g. DSA_PORT=8420 python3 webapp/server.py")
    except OSError as e:
        sys.exit(f"Cannot bind port {PORT}: {e}. Is another instance already running? "
                  f"Try a different port: DSA_PORT={PORT + 1}")
    url = f"http://{'127.0.0.1' if LOOPBACK else HOST}:{PORT}"
    print("=" * 62)
    print("  Ultimate Engineering Guide" + ("  ·  hosted (sign-in required)" if AUTH_ENABLED else ""))
    print("=" * 62)
    print(f"  URL         {url}")
    print(f"  Problems    {len(problems)} indexed, {written} written")
    if AUTH_ENABLED:
        print(f"  Accounts    {AUTH_DB.relative_to(ROOT) if AUTH_DB.is_relative_to(ROOT) else AUTH_DB}")
        print(f"  Codes via   {AUTH.mailer.describe()}")
        print(f"  Google      {'on' if GOOGLE.enabled else 'off (EG_GOOGLE_CLIENT_ID / _SECRET not set)'}")
        print(f"  Cookies     {'Secure (HTTPS only)' if COOKIE_SECURE else 'not Secure (development)'}")
        if RUNNER_SOCKET:
            reachable = code_runner().ping()
            print(f"  Code runs   runner container at {RUNNER_SOCKET}"
                  f"{'' if reachable else ' (not answering yet)'}")
        else:
            print("  Code runs   off (no EG_RUNNER_SOCKET; see deploy/compose.yaml)")
    else:
        print(f"  Python      {python_bin()}")
        print(f"  Go          {go_ok}")
        print(f"  Progress    {STATE_FILE.relative_to(ROOT)}")
    print("=" * 62)
    print("  Ctrl+C to stop\n", flush=True)

    if LOOPBACK and os.environ.get("EG_NO_BROWSER") != "1":
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped. Progress is saved on disk.")
        srv.shutdown()


if __name__ == "__main__":
    main()
