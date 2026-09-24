import re

path = '/Users/njasm/Njasm/AI/DSA-Practice/webapp/server.py'
with open(path, 'r') as f:
    content = f.read()

# Add API_DIR
content = content.replace('SOFTWARE_DESIGN_DIR = ROOT / "SoftwareDesign"', 'SOFTWARE_DESIGN_DIR = ROOT / "SoftwareDesign"\nAPI_DIR = ROOT / "API"')

# Add load_api function
load_api_fn = """
def load_api() -> list[dict]:
    if not API_DIR.exists():
        return []
    items = []
    # Collect Masterclass Guides and General Guides
    for path in sorted(API_DIR.glob("*/*.md")):
        items.append({
            "id": path.parent.name + "_" + path.stem,
            **doc_meta(path, path.stem.replace("_", " ").title()),
            "path": str(path.relative_to(API_DIR))
        })
    return items
"""
content = content.replace('def load_agentic_ai() -> list[dict]:', load_api_fn + '\n\ndef load_agentic_ai() -> list[dict]:')

# Add API endpoints in do_GET
api_endpoints = """
        elif p == "/api/apis":
            self._json({"items": load_api()})
        elif p == "/api/apis-doc":
            rel_path = q.get("path", [""])[0]
            if rel_path:
                self._json(read_markdown(API_DIR / rel_path))
            else:
                self._json({"content": "Not found", "title": "Not Found"})
"""
content = content.replace('        elif p == "/api/agentic-ai":', api_endpoints.strip('\n') + '\n        elif p == "/api/agentic-ai":')

with open(path, 'w') as f:
    f.write(content)
