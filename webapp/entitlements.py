"""Subscription tiers and what each one may read.

One table decides access for the hosted app (server.py with EG_AUTH=1) and for
the public static build (build_static.py, which publishes the free tier only).

    free     a sample of everything: every "Start here" page, the first chapter or
             two of each module, and DSA topics 01-02 in full
    base     the interview core: all of DSA (353 problems, guides, both languages),
             CS Fundamentals, Maths for CS Engineers, Google Behavioral
    pro      + System Design, Software Design (LLD), Go / Py Engineering, the
             standard libraries, API Technologies, SQL, NoSQL, the Query Lab,
             Tool-Kit, Testing, CI/CD and Data Engineering
    pro_max  + AI Roadmap, AI Library Guides, Agentic AI, MLOps, and the staff-level
             (L6) System Design problems 031-041

Every GET /api/* route must appear in ROUTES below; a route that does not is
refused for every tier (default deny), and tests/test_auth.py fails until it is
classified. List routes are open to every signed-in tier (titles are the shop
window) and each item comes back tagged with `requires` and `locked`; the
content behind an item is checked on its own route.

Standard library only.
"""
from __future__ import annotations

import re

TIERS = ("free", "base", "pro", "pro_max")
RANK = {t: i for i, t in enumerate(TIERS)}
TIER_NAMES = {"free": "Free", "base": "Base", "pro": "Pro", "pro_max": "Pro Max"}

# Concurrent signed-in devices per tier: a new sign-in beyond this signs out the
# oldest session, which keeps one paid account from being shared around.
MAX_SESSIONS = {"free": 1, "base": 2, "pro": 2, "pro_max": 3}

# Module keys are the client's (reader.js MODULES, app.js SECTIONS) plus "qlab".
MODULE_TIER = {
    "dsa": "base", "csfund": "base", "maths": "base", "behavioral": "base",
    "sd": "pro", "swd": "pro", "go": "pro", "py": "pro", "pystdlib": "pro", "gostdlib": "pro",
    "api": "pro", "sql": "pro", "nosql": "pro", "qlab": "pro",
    "toolkit": "pro", "testing": "pro", "cicd": "pro", "dataeng": "pro",
    "roadmap": "pro_max", "library": "pro_max", "agentic": "pro_max", "mlops": "pro_max",
}
MODULE_NAMES = {
    "dsa": "DSA", "csfund": "CS Fundamentals", "maths": "Maths for CS Engineers",
    "behavioral": "Google Behavioral", "sd": "System Design", "swd": "Software Design",
    "go": "Go Engineering", "py": "Py Engineering", "pystdlib": "Py Standard Library",
    "gostdlib": "Go Standard Library", "api": "API Technologies", "sql": "SQL", "nosql": "NoSQL",
    "qlab": "Query Lab", "toolkit": "Engineering Tool-Kit", "testing": "Testing & Quality",
    "cicd": "CI/CD & Deployment", "dataeng": "Data Engineering", "roadmap": "AI Roadmap",
    "library": "AI Library Guides", "agentic": "Agentic AI", "mlops": "MLOps & ML System Design",
}

# The free sample. "README"/"readme" (each module's Start here page) is free everywhere.
START_HERE = frozenset({"README", "readme"})
FREE_DSA_TOPICS = frozenset({"01_arrays_hashing", "02_two_pointers"})
FREE_IDS = {
    "csfund": {"07_complexity_analysis_deep_dive", "06_data_structure_internals_deep_dive"},
    "maths": {"00_maths_warm_up", "01_reading_maths_like_code"},
    "behavioral": {"01_how_google_scores_and_googleyness"},
    "sd": {"00_google_l5_playbook", "building_blocks/00_overview", "problem/001_url_shortener"},
    "swd": {"00_software_design_foundations"},
    "go": {"01_rest_api_service"},
    "py": {"01_rest_api_service"},
    "pystdlib": {"01_os"},
    "gostdlib": {"01_os"},
    "api": {"Fundamentals/01_api_fundamentals"},
    "sql": {"00_the_relational_model"},
    "nosql": {"mongodb/00_the_document_model"},
    "toolkit": {"01_docker_and_containers"},
    "testing": {"01_testing_pyramid"},
    "cicd": {"01_ci_fundamentals"},
    "dataeng": {"01_oltp_vs_olap"},
    "mlops": {"01_mlops_lifecycle"},
    "roadmap": {"0_day_prerequisites_and_notation", "1_day_vectors_dot_products"},
    "library": {"01_numpy_mastery"},
    "agentic": {"01_generative_ai_internals"},
}
# Staff-level System Design problems sit above Pro.
SD_STAFF_RE = re.compile(r"^problem/0(3[1-9]|4\d)_")

PLANS = [
    {"id": "free", "name": "Free", "devices": MAX_SESSIONS["free"],
     "summary": "Try the guide: every Start here page, the first chapters of each module and DSA topics 01-02.",
     "includes": ["DSA: Arrays & Hashing and Two Pointers, in full",
                  "First chapter or two of every module", "Progress saved to your account"]},
    {"id": "base", "name": "Base", "devices": MAX_SESSIONS["base"],
     "summary": "The interview core, complete.",
     "includes": ["All 353 DSA problems with solutions, Python and Go",
                  "28 topic guides, playbooks and the recognition drill",
                  "CS Fundamentals, Maths for CS Engineers, Google Behavioral"]},
    {"id": "pro", "name": "Pro", "devices": MAX_SESSIONS["pro"],
     "summary": "Everything for a senior (L5) loop.",
     "includes": ["Everything in Base", "System Design: 33 building blocks, problems 001-030",
                  "Software Design and LLD, Go / Py Engineering, standard libraries",
                  "API Technologies, SQL, NoSQL and the Query Lab",
                  "Tool-Kit, Testing, CI/CD, Data Engineering"]},
    {"id": "pro_max", "name": "Pro Max", "devices": MAX_SESSIONS["pro_max"],
     "summary": "The whole library, staff level and AI engineering included.",
     "includes": ["Everything in Pro", "Staff-level (L6) System Design problems 031-041",
                  "AI Roadmap, AI Library Guides, Agentic AI, MLOps"]},
]


def allows(tier: str, required: str) -> bool:
    return RANK.get(tier, 0) >= RANK[required]


def item_tier(module: str, item_id: str) -> str:
    """The lowest tier that may open `item_id` in `module`."""
    if module == "dsa":
        return "free" if item_id.split("/")[0] in FREE_DSA_TOPICS else "base"
    if item_id in START_HERE or item_id in FREE_IDS.get(module, ()):
        return "free"
    if module == "sd" and SD_STAFF_RE.match(item_id):
        return "pro_max"
    return MODULE_TIER[module]


def _one(q: dict, key: str, default: str = "") -> str:
    return (q.get(key) or [default])[0]


def _eng_module(lang: str) -> str:
    return {"go": "go", "py": "py", "lld": "swd"}.get(lang, "")


def _stdlib_module(lang: str) -> str:
    return "gostdlib" if lang == "go" else "pystdlib"


def _track_module(q: dict) -> str:
    m = _one(q, "m")
    return m if m in MODULE_TIER else ""


# route → ("doc", resolver(q) -> (module, item_id))   content: checked per item
#         ("list", resolver(q) -> module)            listing: open, items tagged
#         ("open", None)                             any signed-in user
ROUTES = {
    "/api/bootstrap": ("open", None),
    "/api/state": ("open", None),
    "/api/dsa-map": ("open", None),          # filtered to the readable topics by filter_payload()
    "/api/api-types": ("list", lambda q: "api"),
    "/api/api-type": ("open", None),         # a ladder's outline: titles only
    "/api/problem": ("doc", lambda q: ("dsa", f"{_one(q, 'topic')}/{_one(q, 'seq')}")),
    "/api/guide": ("doc", lambda q: ("dsa", _one(q, "topic"))),
    "/api/dsa-guides": ("list", lambda q: "dsa"),
    "/api/dsa-guide-doc": ("doc", lambda q: ("dsa", _one(q, "id"))),
    "/api/eng-problem": ("doc", lambda q: (_eng_module(_one(q, "lang", "go")), _one(q, "topic"))),
    "/api/system-design-guide": ("doc", lambda q: ("sd", "guide")),
    "/api/sd": ("list", lambda q: "sd"),
    "/api/sd-doc": ("doc", lambda q: ("sd", _one(q, "id"))),
    "/api/software-design": ("list", lambda q: "swd"),
    "/api/software-design-doc": ("doc", lambda q: ("swd", _one(q, "id"))),
    "/api/roadmap": ("list", lambda q: "roadmap"),
    "/api/roadmap-doc": ("doc", lambda q: ("roadmap", _one(q, "id"))),
    "/api/library-guides": ("list", lambda q: "library"),
    "/api/library-guide-doc": ("doc", lambda q: ("library", _one(q, "id"))),
    "/api/agentic-ai": ("list", lambda q: "agentic"),
    "/api/agentic-ai-doc": ("doc", lambda q: ("agentic", _one(q, "id"))),
    "/api/apis": ("list", lambda q: "api"),
    "/api/apis-doc": ("doc", lambda q: ("api", _one(q, "id"))),
    "/api/api-file": ("doc", lambda q: ("api", f"ladder/{_one(q, 'type')}")),
    "/api/track": ("list", _track_module),
    "/api/track-doc": ("doc", lambda q: (_track_module(q), _one(q, "id"))),
    "/api/cs-fundamentals": ("list", lambda q: "csfund"),
    "/api/cs-fundamentals-doc": ("doc", lambda q: ("csfund", _one(q, "id"))),
    "/api/google-behavioral": ("list", lambda q: "behavioral"),
    "/api/google-behavioral-doc": ("doc", lambda q: ("behavioral", _one(q, "id"))),
    "/api/sql": ("list", lambda q: "sql"),
    "/api/sql-doc": ("doc", lambda q: ("sql", _one(q, "id"))),
    "/api/nosql": ("list", lambda q: "nosql"),
    "/api/nosql-doc": ("doc", lambda q: ("nosql", _one(q, "id"))),
    "/api/query-lab": ("doc", lambda q: ("qlab", _one(q, "engine"))),
    "/api/query-lab-data": ("doc", lambda q: ("qlab", _one(q, "engine"))),
    "/api/stdlib": ("list", lambda q: _stdlib_module(_one(q, "lang", "py"))),
    "/api/stdlib-doc": ("doc", lambda q: (_stdlib_module(_one(q, "lang", "py")), _one(q, "id"))),
    "/api/stdlib-file": ("doc", lambda q: (_stdlib_module(_one(q, "lang", "py")), _one(q, "pkg"))),
}


# POST routes that run code (hosted mode with a runner). A run copies the page's files
# into the sandbox, so it needs the same plan as reading that page. The DSA editor and
# gofmt carry only the learner's own code: any signed-in reader.
RUN_ROUTES = {
    "/api/run": ("open", None),
    "/api/format": ("open", None),
    "/api/eng-run": ("doc", lambda b: (_eng_module(_one(b, "lang", "go")), _one(b, "topic"))),
    "/api/stdlib-run": ("doc", lambda b: (_stdlib_module(_one(b, "lang", "py")), _one(b, "pkg"))),
    "/api/api-run": ("doc", lambda b: ("api", f"ladder/{_one(b, 'type')}")),
}


def upgrade_reply(tier: str, required: str, module: str) -> dict:
    name = MODULE_NAMES.get(module, "This page")
    return {"error": "upgrade_required", "requires": required, "tier": tier, "module": module,
            "message": f"{name}: this page is part of the {TIER_NAMES[required]} plan. "
                       f"You are on {TIER_NAMES.get(tier, 'Free')}."}


def check(path: str, q: dict, tier: str) -> dict | None:
    """None when `tier` may make this GET; otherwise the 403 body to send."""
    rule = ROUTES.get(path)
    if rule is None:
        return {"error": "forbidden", "message": "Unknown route."}
    kind, resolve = rule
    if kind != "doc":
        return None
    module, item_id = resolve(q)
    if module not in MODULE_TIER:
        return {"error": "forbidden", "message": "Unknown module."}
    required = item_tier(module, item_id)
    return None if allows(tier, required) else upgrade_reply(tier, required, module)


def check_run(path: str, body: dict, tier: str) -> dict | None:
    """None when `tier` may run this code; otherwise the 403 body to send."""
    rule = RUN_ROUTES.get(path)
    if rule is None:
        return {"error": "forbidden", "message": "Unknown route."}
    kind, resolve = rule
    if kind != "doc":
        return None
    q = {k: [v] for k, v in body.items() if isinstance(v, str)}
    module, item_id = resolve(q)
    if module not in MODULE_TIER:
        return {"error": "forbidden", "message": "Unknown module."}
    required = item_tier(module, item_id)
    return None if allows(tier, required) else upgrade_reply(tier, required, module)


def _tag(items: list, module: str, tier: str, item_id=lambda it: it["id"]) -> list:
    out = []
    for it in items:
        required = item_tier(module, item_id(it))
        out.append({**it, "requires": required, "locked": not allows(tier, required)})
    return out


def filter_payload(path: str, q: dict, payload, tier: str):
    """Tag list items with their tier, and drop what this tier may not read from
    the few routes that carry content for many items at once."""
    rule = ROUTES.get(path)
    if rule is None or not isinstance(payload, dict):
        return payload
    kind, resolve = rule
    if kind == "list" and isinstance(payload.get("items"), list):
        module = resolve(q)
        if module in MODULE_TIER:
            if path == "/api/api-types":
                return {**payload, "items": _tag(payload["items"], module, tier, lambda it: f"ladder/{it['id']}")}
            return {**payload, "items": _tag(payload["items"], module, tier)}
    if path == "/api/bootstrap":
        eng = payload.get("engTopics") or {}
        return {**payload,
                "problems": _tag(payload.get("problems", []), "dsa", tier),
                "engTopics": {lang: _tag(items, _eng_module(lang), tier) for lang, items in eng.items()}}
    if path == "/api/dsa-map" and isinstance(payload.get("problems"), dict):
        return {**payload, "problems": {pid: v for pid, v in payload["problems"].items()
                                        if allows(tier, item_tier("dsa", pid))}}
    return payload


def account_view(tier: str) -> dict:
    """What the client needs to draw locks and the plans page."""
    return {
        "tier": tier,
        "tierName": TIER_NAMES.get(tier, "Free"),
        "tiers": list(TIERS),
        "tierNames": TIER_NAMES,
        "plans": PLANS,
        "modules": {m: {"requires": t, "full": allows(tier, t), "name": MODULE_NAMES[m]}
                    for m, t in MODULE_TIER.items()},
    }
