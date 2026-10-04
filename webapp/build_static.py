#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

# Add webapp directory to path so we can import server.py
sys.path.insert(0, str(Path(__file__).resolve().parent))

import server

STATIC_DATA_DIR = server.STATIC / "data"

def write_json(rel_path: str, data: dict | list) -> None:
    p = STATIC_DATA_DIR / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        json.dump(data, f, separators=(',', ':'))

def build_static():
    print("Building static API data...")
    STATIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # /api/bootstrap
    problems = server.load_curriculum()
    write_json("bootstrap.json", {
        "problems": problems,
        "topics": server.load_topics(problems),
        "engTopics": {
            "go": server.load_eng_curriculum("go"),
            "py": server.load_eng_curriculum("py"),
            "lld": server.load_eng_curriculum("lld"),
        },
        "state": server.default_state(),
        "runtimes": {"python": False, "go": False},
        "root": "",
    })

    # /api/dsa-map
    write_json("dsa-map.json", server.load_dsa_map())

    # /api/dsa-guides
    write_json("dsa-guides-py.json", {"items": server.load_dsa_guides("py")})
    write_json("dsa-guides-go.json", {"items": server.load_dsa_guides("go")})

    # /api/system-design-guide
    if server.SYSTEM_DESIGN_GUIDE.exists():
        parts = []
        building_blocks_dir = server.SYSTEM_DESIGN / "building_blocks"
        for path in (
            server.SYSTEM_DESIGN / "README.md",
            *sorted(building_blocks_dir.glob("*.md")),
            server.SYSTEM_DESIGN / "02_problem_catalog.md",
            server.SYSTEM_DESIGN / "problems" / "001_url_shortener_question.md",
            server.SYSTEM_DESIGN / "solutions" / "001_url_shortener_solution.md",
            server.SYSTEM_DESIGN / "03_practice_prompts.md",
            server.SYSTEM_DESIGN / "04_practice_answers.md",
            server.SYSTEM_DESIGN / "05_architecture_blueprints.md",
            server.SYSTEM_DESIGN / "solutions" / "009_search_and_autocomplete_solution.md",
            server.SYSTEM_DESIGN / "solutions" / "002_rate_limiter_solution.md",
            server.SYSTEM_DESIGN / "solutions" / "003_pastebin_solution.md",
            server.SYSTEM_DESIGN / "solutions" / "004_notification_platform_solution.md",
            server.SYSTEM_DESIGN / "solutions" / "005_photo_pipeline_solution.md",
            server.SYSTEM_DESIGN / "solutions" / "006_chat_solution.md",
            server.SYSTEM_DESIGN_GUIDE,
        ):
            if path.exists():
                parts.append(path.read_text())
        write_json("system-design-guide.json", {"exists": True, "markdown": "\n\n---\n\n".join(parts)})
    else:
        write_json("system-design-guide.json", {"exists": False, "markdown": ""})

    # /api/sd
    sd_items = server.load_system_design()
    write_json("sd.json", {"items": sd_items})
    for item in sd_items:
        write_json(f"docs/sd/{item['id'].replace('/', '_')}.json", server.read_system_design(item['id']))

    # /api/roadmap
    roadmap_items = server.load_roadmap()
    write_json("roadmap.json", {"items": roadmap_items})
    for item in roadmap_items:
        if item['id'] != 'README':
            write_json(f"docs/roadmap/{item['id']}.json", server.read_markdown(server.safe_md(server.ROADMAP_DIR, item['id'])))

    # /api/library-guides
    lib_guides = server.load_library_guides()
    write_json("library-guides.json", {"items": lib_guides})
    for item in lib_guides:
        write_json(f"docs/library-guides/{item['id']}.json", server.read_markdown(server.safe_md(server.LIBRARY_GUIDES_DIR, item['id'])))
    
    # /api/apis
    apis_items = server.load_api()
    write_json("apis.json", {"items": apis_items})
    for item in apis_items:
        write_json(f"docs/apis/{item['id'].replace('/', '_')}.json", server.read_markdown(server.API_DIR / f"{item['id']}.md"))
    
    # /api/api-types
    api_types = server.load_api_types()
    write_json("api-types.json", {"items": api_types})
    for item in api_types:
        t = item['id']
        write_json(f"docs/api-type/{t}.json", server.load_api_type(t))
        for section in ["Foundation", "labs"]:
            for level in server.api_ladder(t, section):
                for lang in ["py", "go"]:
                    if level["has"].get(lang):
                        write_json(f"docs/api-file/{t}_{section}_{level['id']}_{lang}.json", server.read_api_file(t, section, level["id"], lang))
    
    # /api/agentic-ai
    agentic_items = server.load_agentic_ai()
    write_json("agentic-ai.json", {"items": agentic_items})
    for item in agentic_items:
        write_json(f"docs/agentic-ai/{item['id']}.json", server.read_markdown(server.safe_md(server.AGENTIC_AI_DIR, item['id'])))

    # /api/track
    for track in server.TRACK_DIRS:
        items = server.load_track(track)
        write_json(f"track-{track}.json", {"items": items})
        for item in items:
            write_json(f"docs/track-{track}/{item['id']}.json", server.read_markdown(server.safe_md(server.TRACK_DIRS[track], item['id'])))

    # /api/cs-fundamentals
    cs_items = server.load_cs_fundamentals()
    write_json("cs-fundamentals.json", {"items": cs_items})
    for item in cs_items:
        write_json(f"docs/cs-fundamentals/{item['id']}.json", server.read_markdown(server.safe_md(server.CS_FUNDAMENTALS_DIR, item['id'])))
        
    # /api/google-behavioral
    gb_items = server.load_google_behavioral()
    write_json("google-behavioral.json", {"items": gb_items})
    for item in gb_items:
        write_json(f"docs/google-behavioral/{item['id']}.json", server.read_markdown(server.safe_md(server.GOOGLE_BEHAVIORAL_DIR, item['id'])))
        
    # /api/sql
    sql_items = server.load_sql()
    write_json("sql.json", {"items": sql_items})
    for item in sql_items:
        write_json(f"docs/sql/{item['id']}.json", server.read_sql(item['id']))
        
    # /api/nosql
    nosql_items = server.load_nosql()
    write_json("nosql.json", {"items": nosql_items})
    for item in nosql_items:
        write_json(f"docs/nosql/{item['id'].replace('/', '_')}.json", server.read_nosql(item['id']))
        
    # /api/stdlib
    for lang in ["py", "go"]:
        stdlib_items = server.load_stdlib(lang)
        write_json(f"stdlib-{lang}.json", {"items": stdlib_items})
        for item in stdlib_items:
            pkg = item["id"]
            write_json(f"docs/stdlib-doc/{lang}_{pkg}.json", server.stdlib_guide(lang, pkg))
            for level in item.get("levels", []):
                write_json(f"docs/stdlib-file/{lang}_{pkg}_{level['id']}.json", server.read_stdlib_file(lang, pkg, level["id"]))
                
    # /api/software-design
    sd2_items = server.load_software_design()
    write_json("software-design.json", {"items": sd2_items})
    for item in sd2_items:
        if item.get("kind") == "doc":
            write_json(f"docs/software-design/{item['id']}.json", server.read_markdown(server.safe_md(server.SOFTWARE_DESIGN_DIR, item['id'])))

    # Iterating over problems for /api/problem and /api/eng-problem
    for p in problems:
        for lang in ["py", "go"]:
            for kind in ["question", "solution"]:
                res = server.read_problem(p['topic'], p['seq'], kind, lang)
                if not res:
                    res = {"exists": False, "doc": "", "code": "", "path": ""}
                write_json(f"docs/problems/{p['topic']}_{p['seq']}_{kind}_{lang}.json", res)
                
    # /api/guide and /api/dsa-guide-doc
    topics = server.load_topics(problems)
    for topic in topics:
        for lang in ["py", "go"]:
            write_json(f"docs/guide/{topic['id']}_{lang}.json", server.read_guide(topic['id'], lang))
            write_json(f"docs/dsa-guide-doc/{topic['id']}_{lang}.json", server.read_dsa_guide(topic['id'], lang))
            
    # /api/eng-problem
    for lang in ["go", "py", "lld"]:
        eng_items = server.load_eng_curriculum(lang)
        for item in eng_items:
            topic_id = item['id']
            for kind in ["explanation", "solution", "test"]:
                write_json(f"docs/eng/{lang}_{topic_id}_{kind}.json", server.read_eng_problem(lang, topic_id, kind))
                
    # /api/state
    write_json("state.json", server.default_state())

    print("Static build complete.")

if __name__ == "__main__":
    build_static()
