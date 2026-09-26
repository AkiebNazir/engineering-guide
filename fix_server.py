import re

with open("webapp/server.py", "r") as f:
    content = f.read()

# I will just write a python script to replace the /api/tool-kit-doc block
new_block = """        elif p == "/api/tool-kit-doc":
            req_id = q.get("id", [""])[0]
            if req_id:
                p1 = TOOL_KIT_DIR / req_id / f"{req_id}.md"
                p2 = TOOL_KIT_DIR / f"{req_id}.md"
                doc_path = p1 if p1.exists() else (p2 if p2.exists() else None)
                if doc_path:
                    res = read_markdown(doc_path)
                    
                    topic_dir = doc_path.parent
                    examples = []
                    
                    for ex_dir in sorted(topic_dir.glob("examples/*")):
                        if ex_dir.is_dir():
                            files = []
                            for f in sorted(ex_dir.rglob("*")):
                                if f.is_file() and not f.name.startswith("."):
                                    files.append({"name": str(f.relative_to(ex_dir)), "content": f.read_text(errors='replace')})
                            examples.append({"id": ex_dir.name, "lang": "python", "files": files})
                            
                    for ex_dir in sorted(topic_dir.glob("examples_go/*")):
                        if ex_dir.is_dir():
                            files = []
                            for f in sorted(ex_dir.rglob("*")):
                                if f.is_file() and not f.name.startswith("."):
                                    files.append({"name": str(f.relative_to(ex_dir)), "content": f.read_text(errors='replace')})
                            examples.append({"id": ex_dir.name, "lang": "go", "files": files})
                            
                    res["examples"] = examples
                    self._json(res)
                else:
                    self._json({"content": "Not found", "title": "Not Found"})
            else:
                self._json({"content": "Not found", "title": "Not Found"})"""

start_str = '        elif p == "/api/tool-kit-doc":'
end_str = '        elif p == "/api/apis":'

start_idx = content.find(start_str)
end_idx = content.find(end_str)

new_content = content[:start_idx] + new_block + "\n" + content[end_idx:]

with open("webapp/server.py", "w") as f:
    f.write(new_content)
