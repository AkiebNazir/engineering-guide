#!/usr/bin/env python3
"""
Ultimate Engineering Guide — a local web app for the DSA, systems, data and AI curriculum.

Stdlib only. No pip install, no build step.

    python webapp/server.py          # then open http://127.0.0.1:8420

Binds to 127.0.0.1 only. It executes code you type, on your machine, as you —
the same trust model as a Jupyter notebook. Do not expose it to a network.
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class StudioServer(ThreadingHTTPServer):
    # The page pulls ~60 scripts at once; the default backlog of 5 made the
    # browser see ERR_CONNECTION_RESET on some of them and load half a page.
    request_queue_size = 128
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
WEBAPP = ROOT / "webapp"
STATIC = WEBAPP / "static"
DATA = WEBAPP / "data"
STATE_FILE = DATA / "progress.json"
TSV = ROOT / "tools" / "problems.tsv"
SYSTEM_DESIGN_GUIDE = ROOT / "SYSTEM_DESIGN_GUIDE.md"
SYSTEM_DESIGN = ROOT / "SystemDesign"
ENG_ROOTS = {"go": ROOT / "GoEngineering", "py": ROOT / "PyEngineering",
             "lld": ROOT / "SoftwareDesign" / "lld"}
ENG_EXT = {"go": "go", "py": "py", "lld": "py"}
LLD_ID_RE = re.compile(r"^\d{3}_[a-z0-9_]+$")
ROADMAP_DIR = ROOT / "AI-road-map"
LIBRARY_GUIDES_DIR = ROOT / "AI-Libraries-Guides"
AGENTIC_AI_DIR = ROOT / "Agentic-AI"
CS_FUNDAMENTALS_DIR = ROOT / "CSFundamentals"
CICD_DIR = ROOT / "CICD"
GOOGLE_BEHAVIORAL_DIR = ROOT / "GoogleBehavioral"
SOFTWARE_DESIGN_DIR = ROOT / "SoftwareDesign"
API_DIR = ROOT / "API"
TOOL_KIT_DIR = ROOT / "Tool-Kit"
SQL_DIR = ROOT / "SQL"
NOSQL_DIR = ROOT / "NoSQL"
STDLIB_ROOTS = {"py": ROOT / "PyStdLib", "go": ROOT / "GoStdLib"}

PORT = int(os.environ.get("DSA_PORT", "8420"))
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
    return ROOT / "PyDSA" / topic / f"{seq}_{snake(slug)}_{kind}.py"


def go_path(topic: str, seq: str, slug: str, kind: str) -> Path:
    return ROOT / "GoDSA" / topic / f"{seq}_{snake(slug)}" / f"{kind}.go"


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
            "py": (ROOT / "PyDSA" / tid / "_TOPIC_GUIDE.md").exists(),
            "go": (ROOT / "GoDSA" / tid / "_TOPIC_GUIDE.md").exists(),
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
    venv = ROOT / "PyEngineering" / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else python_bin()


_eng_run_lock = threading.Lock()


def run_eng(lang: str, topic: str, code: str) -> dict:
    """Runs the learner's edited explanation code.

    When the topic has a test file, tests are the real check: Go/Python
    tests are hardcoded to load the *_solution.* file by name, so the trick
    is to back up the real solution file, overwrite it with the learner's
    code (same package/module, same public surface), run the real test file
    against it, then always restore the original — even on timeout or
    crash. Many topics have no test file (by design — this curriculum
    doesn't require one), so when there isn't one we fall back to swapping
    the *explanation* file itself and just compiling/running it directly:
    `go vet` (which type-checks a `package main` fine even with no
    `func main()`) for Go, or executing the file for Python. Either way the
    swap always takes a lock and always restores the original file."""
    if not code.strip():
        return {"ok": False, "stdout": "", "exitCode": -1, "ms": 0,
                "stderr": "Nothing to run — the editor is empty."}

    expl = eng_file(lang, topic, "explanation")
    sol = eng_file(lang, topic, "solution")
    test = eng_file(lang, topic, "test")
    if not expl.exists():
        return {"ok": False, "stdout": "", "exitCode": -1, "ms": 0,
                "stderr": "This topic hasn't been authored yet — nothing to run."}

    if lang == "go" and not go_bin():
        return {"ok": False, "stdout": "", "exitCode": -1, "ms": 0,
                "stderr": "Go toolchain not found on PATH."}

    has_test = sol.exists() and test.exists()
    target = sol if has_test else expl

    with _eng_run_lock:
        original = target.read_text()
        started = time.perf_counter()
        try:
            target.write_text(code)
            if lang == "go":
                cmd = [go_bin(), "test", "-v", "./..."] if has_test else [go_bin(), "vet", "./..."]
                proc = subprocess.run(
                    cmd, capture_output=True, text=True,
                    timeout=RUN_TIMEOUT_ENG_GO, cwd=str(target.parent),
                    env={**os.environ, "GOFLAGS": "-mod=mod"},
                )
                stdout = proc.stdout
                if not has_test and proc.returncode == 0 and not stdout.strip():
                    stdout = "go vet: no issues found — code compiles cleanly.\n"
            elif has_test:
                proc = subprocess.run(
                    [eng_python_bin(), "-m", "pytest", test.name, "-v"],
                    capture_output=True, text=True,
                    timeout=RUN_TIMEOUT_ENG_PY, cwd=str(target.parent),
                )
                stdout = proc.stdout
            else:
                proc = subprocess.run(
                    [eng_python_bin(), expl.name],
                    capture_output=True, text=True,
                    timeout=RUN_TIMEOUT_ENG_PY, cwd=str(target.parent),
                )
                stdout = proc.stdout
            return {
                "ok": proc.returncode == 0,
                "stdout": stdout, "stderr": proc.stderr,
                "exitCode": proc.returncode,
                "ms": round((time.perf_counter() - started) * 1000),
            }
        except subprocess.TimeoutExpired:
            timeout = RUN_TIMEOUT_ENG_GO if lang == "go" else RUN_TIMEOUT_ENG_PY
            return {
                "ok": False, "stdout": "", "timeout": True, "exitCode": -1,
                "stderr": f"Timed out after {timeout}s — likely an infinite loop, "
                          f"a deadlock, or a server that never shuts down.",
                "ms": timeout * 1000,
            }
        finally:
            target.write_text(original)


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
SD_DRILLS = ("03_practice_prompts", "04_practice_answers", "05_architecture_blueprints",
             "06_spoken_walkthroughs")


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
    for sub, group in (("building_blocks", "Building blocks"),):
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
    elif m := re.fullmatch(r"(building_blocks)/([\w-]+)", doc_id):
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


def load_toolkit() -> list[dict]:
    if not TOOL_KIT_DIR.exists():
        return []
    items = []
    for path in sorted(TOOL_KIT_DIR.glob("*.md")):
        if path.name == "README.md": continue
        items.append({
            "id": path.stem,
            **doc_meta(path, path.stem.replace("_", " ").title()),
            "path": str(path.relative_to(TOOL_KIT_DIR))
        })
    for path in sorted(TOOL_KIT_DIR.iterdir()):
        if path.is_dir() and (path / f"{path.name}.md").exists():
            main_doc = path / f"{path.name}.md"
            items.append({
                "id": path.name,
                **doc_meta(main_doc, path.name.replace("_", " ").title()),
                "path": str(main_doc.relative_to(TOOL_KIT_DIR))
            })
    return items


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


def load_cicd() -> list[dict]:
    if not CICD_DIR.exists():
        return []
    items = []
    for path in sorted(CICD_DIR.iterdir()):
        if path.is_dir() and re.match(r"^\d+-", path.name):
            md_file = path / f"{path.name}.md"
            if md_file.exists():
                num = path.name.split('-')[0]
                items.append({
                    "id": path.name,
                    "num": num,
                    **doc_meta(md_file, path.name.replace("-", " ").title())
                })
    return items



def load_cs_fundamentals() -> list[dict]:
    """Load CSFundamentals deep-dive markdown files."""
    if not CS_FUNDAMENTALS_DIR.exists():
        return []
    items = []
    for path in sorted(CS_FUNDAMENTALS_DIR.glob("*_deep_dive.md")):
        m = re.match(r"^(\d+)_(.+?)_deep_dive\.md$", path.name)
        if not m:
            continue
        items.append({
            "id": path.stem, "num": m.group(1),
            **doc_meta(path, m.group(2).replace("_", " ").title()),
        })
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
DSA_GUIDE_ROOTS = {"py": "PyDSA", "go": "GoDSA"}


def load_dsa_guides(lang: str = "py") -> list[dict]:
    """One reader page per topic that has a _TOPIC_GUIDE.md in the given language's
    tree (PyDSA or GoDSA), in topic order."""
    root = DSA_GUIDE_ROOTS.get(lang, "PyDSA")
    items: list[dict] = []
    for path in sorted((ROOT / root).glob("*/_TOPIC_GUIDE.md")):
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
    return read_markdown(ROOT / DSA_GUIDE_ROOTS.get(lang, "PyDSA") / doc_id / "_TOPIC_GUIDE.md")


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


_stdlib_run_lock = threading.Lock()
# Dot-prefixed so the Go tool skips it when expanding ./... — an explicit
# relative path to it still builds, which is all `go run` needs.
GO_RUNTMP = ".runtmp"


def run_stdlib(lang: str, pkg: str, level: str, code: str) -> dict:
    """Runs the buffer the learner is looking at — never the file on disk.

    Python is trivial: a temp directory outside the repo. Go is not, because a
    level imports nothing but the stdlib yet still has to compile inside the
    GoStdLib module, so the throwaway package is created *under* GoStdLib and
    deleted in a finally. Either way the curriculum file is only ever read."""
    timeout = RUN_TIMEOUT_STDLIB_GO if lang == "go" else RUN_TIMEOUT_STDLIB_PY
    if not code.strip():
        return {"ok": False, "stdout": "", "stderr": "Nothing to run — the editor is empty.",
                "exitCode": -1, "ms": 0}
    if stdlib_level_path(lang, pkg, level) is None:
        return {"ok": False, "stdout": "", "stderr": "Unknown package or level.",
                "exitCode": -1, "ms": 0}

    def timed_out() -> dict:
        return {
            "ok": False, "stdout": "", "timeout": True, "exitCode": -1,
            "stderr": f"Timed out after {timeout}s — likely an infinite loop, a "
                      f"benchmark that is too big, or something waiting on input.",
            "ms": timeout * 1000,
        }

    def done(proc, started: float) -> dict:
        return {"ok": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr,
                "exitCode": proc.returncode,
                "ms": round((time.perf_counter() - started) * 1000)}

    if lang == "py":
        tmp = tempfile.mkdtemp(prefix="stdlib_py_")
        try:
            f = Path(tmp) / "main.py"
            f.write_text(code)
            started = time.perf_counter()
            try:
                return done(subprocess.run([python_bin(), str(f)], capture_output=True,
                                           text=True, timeout=timeout, cwd=tmp), started)
            except subprocess.TimeoutExpired:
                return timed_out()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    go = go_bin()
    if not go:
        return {"ok": False, "stdout": "", "exitCode": -1, "ms": 0,
                "stderr": "Go toolchain not found on PATH."}
    root = STDLIB_ROOTS["go"]
    # The scratch package lives inside the module, so serialise creation and
    # teardown against anything else mutating shared curriculum paths.
    with _stdlib_run_lock:
        holder = root / GO_RUNTMP
        holder.mkdir(exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix="run_", dir=str(holder)))
        try:
            (tmp / "main.go").write_text(code)
            started = time.perf_counter()
            try:
                return done(subprocess.run(
                    [go, "run", f"./{GO_RUNTMP}/{tmp.name}"], capture_output=True,
                    text=True, timeout=timeout, cwd=str(root),
                    env={**os.environ, "GOFLAGS": "-mod=mod"}), started)
            except subprocess.TimeoutExpired:
                return timed_out()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            try:
                holder.rmdir()          # only when nothing else is running
            except OSError:
                pass


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
API_TYPES = ["REST", "GraphQL", "Protobuf", "gRPC", "WebSockets", "Webhooks", "SOAP"]
API_LEVEL_RE = re.compile(r"^(\d{2})_([a-z0-9_]+)$")
RUN_TIMEOUT_API_PY = 30
RUN_TIMEOUT_API_GO = 45
API_RUNTMP = ".runtmp"


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


_api_run_lock = threading.Lock()


def run_api_file(type_name: str, section: str, level_id: str, lang: str, code: str) -> dict:
    """Runs the buffer the learner is looking at — never the file on disk (same
    principle as run_stdlib above). Python: the level's sibling files (some
    Protobuf/gRPC levels import generated *_pb2 / *_pb2_grpc stubs by bare
    name) are copied into a scratch dir alongside the edited code, so those
    imports still resolve, using the API/.venv interpreter that has fastapi,
    strawberry, grpcio, websockets etc. installed. Go: a scratch package
    created *under* API/ so it still compiles inside the dsapractice/api
    module and picks up its real dependencies (gin, echo, coder/websocket...)."""
    timeout = RUN_TIMEOUT_API_GO if lang == "go" else RUN_TIMEOUT_API_PY
    if not code.strip():
        return {"ok": False, "stdout": "", "stderr": "Nothing to run — the editor is empty.",
                "exitCode": -1, "ms": 0}
    target = api_resolve(type_name, section, level_id, lang)
    if not target or not target.exists():
        return {"ok": False, "stdout": "", "stderr": "Unknown type, section, level or language.",
                "exitCode": -1, "ms": 0}

    def timed_out() -> dict:
        return {"ok": False, "stdout": "", "timeout": True, "exitCode": -1,
                "stderr": f"Timed out after {timeout}s — likely an infinite loop, a "
                          f"deadlock, or a server that never shuts down.",
                "ms": timeout * 1000}

    def done(proc, started: float) -> dict:
        return {"ok": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr,
                "exitCode": proc.returncode, "ms": round((time.perf_counter() - started) * 1000)}

    if lang == "go":
        go = go_bin()
        if not go:
            return {"ok": False, "stdout": "", "exitCode": -1, "ms": 0,
                    "stderr": "Go toolchain not found on PATH."}
        with _api_run_lock:
            holder = API_DIR / API_RUNTMP
            holder.mkdir(exist_ok=True)
            tmp = Path(tempfile.mkdtemp(prefix="run_", dir=str(holder)))
            try:
                (tmp / "main.go").write_text(code)
                started = time.perf_counter()
                try:
                    return done(subprocess.run(
                        [go, "run", f"./{API_RUNTMP}/{tmp.name}"], capture_output=True,
                        text=True, timeout=timeout, cwd=str(API_DIR),
                        env={**os.environ, "GOFLAGS": "-mod=mod"}), started)
                except subprocess.TimeoutExpired:
                    return timed_out()
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
                try:
                    holder.rmdir()          # only when nothing else is running
                except OSError:
                    pass

    with tempfile.TemporaryDirectory(prefix="api_py_") as tmp:
        tmp_path = Path(tmp)
        for sib in target.parent.iterdir():
            if sib.is_file() and sib.suffix == ".py":
                shutil.copy2(sib, tmp_path / sib.name)
        (tmp_path / target.name).write_text(code)
        started = time.perf_counter()
        try:
            return done(subprocess.run(
                [api_python_bin(), target.name], capture_output=True, text=True,
                timeout=timeout, cwd=str(tmp_path)), started)
        except subprocess.TimeoutExpired:
            return timed_out()


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
PY_DOC = re.compile(r'^\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', re.S)
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


def read_guide(topic: str, lang: str) -> dict:
    folder = "PyDSA" if lang == "py" else "GoDSA"
    path = ROOT / folder / topic / "_TOPIC_GUIDE.md"
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
def run_python(code: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="dsa_py_") as tmp:
        f = Path(tmp) / "main.py"
        f.write_text(code)
        started = time.perf_counter()
        try:
            proc = subprocess.run(
                [python_bin(), str(f)],
                capture_output=True, text=True,
                timeout=RUN_TIMEOUT_PY, cwd=tmp,
            )
            return {
                "ok": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exitCode": proc.returncode,
                "ms": round((time.perf_counter() - started) * 1000),
            }
        except subprocess.TimeoutExpired:
            return {
                "ok": False, "stdout": "", "timeout": True, "exitCode": -1,
                "stderr": f"Timed out after {RUN_TIMEOUT_PY}s — "
                          f"likely an infinite loop or runaway recursion.",
                "ms": RUN_TIMEOUT_PY * 1000,
            }


def run_go(code: str) -> dict:
    go = go_bin()
    if not go:
        return {"ok": False, "stdout": "", "exitCode": -1, "ms": 0,
                "stderr": "Go toolchain not found on PATH. Install Go, or "
                          "set it up so `go` is runnable from a shell."}
    with tempfile.TemporaryDirectory(prefix="dsa_go_") as tmp:
        d = Path(tmp)
        (d / "main.go").write_text(code)
        (d / "go.mod").write_text("module dsascratch\n\ngo 1.21\n")
        started = time.perf_counter()
        env = {**os.environ, "GOFLAGS": "-mod=mod"}
        try:
            proc = subprocess.run(
                [go, "run", "."],
                capture_output=True, text=True,
                timeout=RUN_TIMEOUT_GO, cwd=str(d), env=env,
            )
            return {
                "ok": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exitCode": proc.returncode,
                "ms": round((time.perf_counter() - started) * 1000),
            }
        except subprocess.TimeoutExpired:
            return {
                "ok": False, "stdout": "", "timeout": True, "exitCode": -1,
                "stderr": f"Timed out after {RUN_TIMEOUT_GO}s — "
                          f"likely an infinite loop, or a very slow first build.",
                "ms": RUN_TIMEOUT_GO * 1000,
            }


def format_go(code: str) -> dict:
    go = go_bin()
    if not go:
        return {"ok": False, "code": code, "error": "Go toolchain not found."}
    gofmt = Path(go).parent / "gofmt"
    if not gofmt.exists():
        return {"ok": False, "code": code, "error": "gofmt not found."}
    try:
        proc = subprocess.run([str(gofmt)], input=code, capture_output=True,
                              text=True, timeout=10)
        if proc.returncode == 0:
            return {"ok": True, "code": proc.stdout}
        return {"ok": False, "code": code, "error": proc.stderr}
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": code, "error": "gofmt timed out."}


# ----------------------------------------------------------------------------
# HTTP handler
# ----------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "DSAStudio/1.0"

    def log_message(self, fmt, *args):  # quieter console
        if "/api/run" in (args[0] if args else ""):
            sys.stderr.write(f"  run  {args[0]}\n")

    # -- helpers ------------------------------------------------------------
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200) -> None:
        self._send(code, json.dumps(obj).encode(), "application/json")

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n))
        except json.JSONDecodeError:
            return {}

    def _static(self, rel: str) -> None:
        rel = rel.lstrip("/") or "index.html"
        path = (STATIC / rel).resolve()
        if not str(path).startswith(str(STATIC.resolve())) or not path.is_file():
            self._send(404, b"Not found", "text/plain")
            return
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".svg": "image/svg+xml",
            ".json": "application/json",
        }.get(path.suffix, "application/octet-stream")
        self._send(200, path.read_bytes(), ctype)

    # -- routes -------------------------------------------------------------
    def do_GET(self) -> None:
        u = urlparse(self.path)
        q = parse_qs(u.query)
        p = u.path

        if p == "/api/bootstrap":
            problems = load_curriculum()
            with _state_lock:
                state = load_state()
            self._json({
                "problems": problems,
                "topics": load_topics(problems),
                "engTopics": {
                    "go": load_eng_curriculum("go"),
                    "py": load_eng_curriculum("py"),
                    "lld": load_eng_curriculum("lld"),
                },
                "state": state,
                "runtimes": {"python": True, "go": go_bin() is not None},
                "root": str(ROOT),
            })
        elif p == "/api/eng-problem":
            r = read_eng_problem(q.get("lang", ["go"])[0], q.get("topic", [""])[0],
                                  q.get("kind", ["explanation"])[0])
            self._json(r, 200 if r["exists"] else 404)
        elif p == "/api/problem":
            r = read_problem(q.get("topic", [""])[0], q.get("seq", [""])[0],
                             q.get("kind", ["question"])[0],
                             q.get("lang", ["py"])[0])
            self._json(r if r else {"error": "unknown problem"},
                       200 if r else 404)
        elif p == "/api/guide":
            self._json(read_guide(q.get("topic", [""])[0],
                                  q.get("lang", ["py"])[0]))
        elif p == "/api/dsa-guides":
            self._json({"items": load_dsa_guides(q.get("lang", ["py"])[0])})
        elif p == "/api/dsa-guide-doc":
            self._json(read_dsa_guide(q.get("id", [""])[0], q.get("lang", ["py"])[0]))
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
                self._json({"exists": True, "markdown": "\n\n---\n\n".join(parts)})
            else:
                self._json({"exists": False, "markdown": ""}, 404)
        elif p == "/api/sd":
            self._json({"items": load_system_design()})
        elif p == "/api/sd-doc":
            self._json(read_system_design(q.get("id", [""])[0]))
        elif p == "/api/roadmap":
            self._json({"items": load_roadmap()})
        elif p == "/api/roadmap-doc":
            self._json(read_markdown(safe_md(ROADMAP_DIR, q.get("id", [""])[0])))
        elif p == "/api/library-guides":
            self._json({"items": load_library_guides()})
        elif p == "/api/library-guide-doc":
            self._json(read_markdown(safe_md(LIBRARY_GUIDES_DIR, q.get("id", [""])[0])))
        elif p == "/api/tool-kit":
            self._json({"items": load_toolkit()})
        elif p == "/api/tool-kit-doc":
            req_id = q.get("id", [""])[0]
            if req_id:
                p1 = TOOL_KIT_DIR / req_id / f"{req_id}.md"
                p2 = TOOL_KIT_DIR / f"{req_id}.md"
                if p1.exists():
                    self._json(read_markdown(p1))
                elif p2.exists():
                    self._json(read_markdown(p2))
                else:
                    self._json({"content": "Not found", "title": "Not Found"})
            else:
                self._json({"content": "Not found", "title": "Not Found"})
        elif p == "/api/apis":
            self._json({"items": load_api()})
        elif p == "/api/apis-doc":
            # The ID is now something like "REST/REST_API_Guide"
            req_id = q.get("id", [""])[0]
            if req_id:
                self._json(read_markdown(API_DIR / f"{req_id}.md"))
            else:
                self._json({"content": "Not found", "title": "Not Found"})
        elif p == "/api/api-types":
            self._json({"items": load_api_types()})
        elif p == "/api/api-type":
            r = load_api_type(q.get("type", [""])[0])
            self._json(r, 200 if r["exists"] else 404)
        elif p == "/api/api-file":
            r = read_api_file(q.get("type", [""])[0], q.get("section", ["Foundation"])[0],
                               q.get("level", [""])[0], q.get("lang", ["py"])[0])
            self._json(r, 200 if r["exists"] else 404)
        elif p == "/api/agentic-ai":
            self._json({"items": load_agentic_ai()})
        elif p == "/api/agentic-ai-doc":
            self._json(read_markdown(safe_md(AGENTIC_AI_DIR, q.get("id", [""])[0])))

        elif p == "/api/cicd":
            self._json({"items": load_cicd()})
        elif p == "/api/cicd-doc":
            doc_id = q.get("id", [""])[0]
            if not doc_id or "/" in doc_id or "\\" in doc_id:
                self._json({"exists": False})
            else:
                path = CICD_DIR / doc_id / f"{doc_id}.md"
                out = read_markdown(path)
                exercises_dir = CICD_DIR / doc_id / "exercises"
                if out["exists"] and exercises_dir.exists():
                    exercises_content = []
                    for ex_path in sorted(exercises_dir.glob("*.md")):
                        exercises_content.append(ex_path.read_text())
                    if exercises_content:
                        out["markdown"] += "\n\n---\n\n# Exercises\n\n" + "\n\n---\n\n".join(exercises_content)
                self._json(out)

        elif p == "/api/cs-fundamentals":
            self._json({"items": load_cs_fundamentals()})
        elif p == "/api/cs-fundamentals-doc":
            self._json(read_markdown(safe_md(CS_FUNDAMENTALS_DIR, q.get("id", [""])[0])))
        elif p == "/api/google-behavioral":
            self._json({"items": load_google_behavioral()})
        elif p == "/api/google-behavioral-doc":
            self._json(read_markdown(safe_md(GOOGLE_BEHAVIORAL_DIR, q.get("id", [""])[0])))
        elif p == "/api/sql":
            self._json({"items": load_sql()})
        elif p == "/api/sql-doc":
            self._json(read_sql(q.get("id", [""])[0]))
        elif p == "/api/nosql":
            self._json({"items": load_nosql()})
        elif p == "/api/nosql-doc":
            self._json(read_nosql(q.get("id", [""])[0]))
        elif p == "/api/stdlib":
            self._json({"items": load_stdlib(stdlib_lang(q.get("lang", ["py"])[0]))})
        elif p == "/api/stdlib-doc":
            self._json(stdlib_guide(stdlib_lang(q.get("lang", ["py"])[0]),
                                    q.get("id", [""])[0]))
        elif p == "/api/stdlib-file":
            self._json(read_stdlib_file(stdlib_lang(q.get("lang", ["py"])[0]),
                                        q.get("pkg", [""])[0], q.get("level", [""])[0]))
        elif p == "/api/software-design":
            self._json({"items": load_software_design()})
        elif p == "/api/software-design-doc":
            self._json(read_markdown(safe_md(SOFTWARE_DESIGN_DIR, q.get("id", [""])[0])))
        elif p == "/api/state":
            with _state_lock:
                self._json(load_state())
        else:
            self._static(p)

    def do_POST(self) -> None:
        p = urlparse(self.path).path
        body = self._body()

        if p == "/api/run":
            code = body.get("code", "")
            lang = body.get("lang", "py")
            if not code.strip():
                self._json({"ok": False, "stdout": "", "exitCode": -1, "ms": 0,
                            "stderr": "Nothing to run — the editor is empty."})
                return
            self._json(run_python(code) if lang == "py" else run_go(code))
        elif p == "/api/eng-run":
            self._json(run_eng(body.get("lang", "go"), body.get("topic", ""),
                                body.get("code", "")))
        elif p == "/api/stdlib-run":
            self._json(run_stdlib(stdlib_lang(body.get("lang", "py")),
                                  body.get("pkg", ""), body.get("level", ""),
                                  body.get("code", "")))
        elif p == "/api/api-run":
            self._json(run_api_file(body.get("type", ""), body.get("section", "Foundation"),
                                    body.get("level", ""), body.get("lang", "py"),
                                    body.get("code", "")))
        elif p == "/api/format":
            self._json(format_go(body.get("code", "")))
        elif p == "/api/state":
            with _state_lock:
                save_state(body)
            self._json({"ok": True})
        elif p == "/api/patch":
            # Merge a single problem's record without shipping whole state.
            with _state_lock:
                state = load_state()
                pid = body.get("id")
                if pid:
                    rec = state["problems"].setdefault(pid, {})
                    rec.update(body.get("patch", {}))
                if "settings" in body:
                    state["settings"].update(body["settings"])
                if body.get("doc"):
                    # Reading state for module pages: scroll depth, checked
                    # sections, highlights, completion.
                    docs = state.setdefault("docs", {})
                    docs.setdefault(body["doc"], {}).update(body.get("docPatch", {}))
                if "session" in body:
                    day = body["session"]["date"]
                    state["sessions"][day] = (
                        state["sessions"].get(day, 0) + body["session"]["seconds"]
                    )
                save_state(state)
            self._json({"ok": True})
        else:
            self._send(404, b"Not found", "text/plain")


def main() -> None:
    if not TSV.exists():
        sys.exit(f"Missing {TSV}. Run this from the DSA-Practice repo.")
    DATA.mkdir(parents=True, exist_ok=True)

    problems = load_curriculum()
    written = sum(1 for p in problems if p["has"]["pySolution"])
    go_ok = "yes" if go_bin() else "NOT FOUND (Python still runs)"

    try:
        srv = StudioServer(("127.0.0.1", PORT), Handler)
    except PermissionError:
        sys.exit(f"Cannot bind port {PORT}: permission denied. Ports below 1024 need "
                  f"root on macOS/Linux. Use a port above 1024, e.g. ./studio 8420")
    except OSError as e:
        sys.exit(f"Cannot bind port {PORT}: {e}. Is another instance already running? "
                  f"Try a different port: ./studio {PORT + 1}")
    url = f"http://127.0.0.1:{PORT}"
    print("=" * 62)
    print("  Ultimate Engineering Guide")
    print("=" * 62)
    print(f"  URL         {url}")
    print(f"  Problems    {len(problems)} indexed, {written} written")
    print(f"  Python      {python_bin()}")
    print(f"  Go          {go_ok}")
    print(f"  Progress    {STATE_FILE.relative_to(ROOT)}")
    print("=" * 62)
    print("  Ctrl+C to stop\n", flush=True)

    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped. Progress is saved on disk.")
        srv.shutdown()


if __name__ == "__main__":
    main()
