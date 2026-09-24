import re

path = '/Users/njasm/Njasm/AI/DSA-Practice/webapp/server.py'
with open(path, 'r') as f:
    content = f.read()

# Fix load_api
new_load_api = """def load_api() -> list[dict]:
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
    return items"""

content = re.sub(r'def load_api\(\).*?return items', new_load_api, content, flags=re.DOTALL)

# Fix endpoint
new_endpoint = """        elif p == "/api/apis":
            self._json({"items": load_api()})
        elif p == "/api/apis-doc":
            # The ID is now something like "REST/REST_API_Guide"
            req_id = q.get("id", [""])[0]
            if req_id:
                self._json(read_markdown(API_DIR / f"{req_id}.md"))
            else:
                self._json({"content": "Not found", "title": "Not Found"})"""

content = re.sub(r'        elif p == "/api/apis":.*?self._json\(\{"content": "Not found", "title": "Not Found"\}\)', new_endpoint, content, flags=re.DOTALL)

with open(path, 'w') as f:
    f.write(content)
