import re

with open("webapp/server.py", "r") as f:
    code = f.read()

# Remove the 'projects' extraction from load_data_engineering
# Find the start of "# Load projects" and end of the function
start_idx = code.find("# Load projects")
if start_idx != -1:
    end_idx = code.find("return items", start_idx)
    if end_idx != -1:
        code = code[:start_idx] + code[end_idx:]

# Update the read_data_engineering_doc
old_str = """            else:
                path = DATA_ENGINEERING_DIR / doc_id / f"{doc_id}.md"
                self._json(read_markdown(path))"""

new_str = """            else:
                path = DATA_ENGINEERING_DIR / doc_id / f"{doc_id}.md"
                data = read_markdown(path)
                if data.get("exists"):
                    projects_html = ["\\n<hr>\\n<h2>Interactive Code Examples</h2>\\n<div class='de-code-examples'>"]
                    for lang, dlang in [("python", "de-py"), ("golang", "de-go")]:
                        proj_dir = DATA_ENGINEERING_DIR / doc_id / "projects" / lang
                        if proj_dir.exists():
                            for pdir in sorted(proj_dir.iterdir()):
                                if pdir.is_dir() and re.match(r"^\\d+_", pdir.name):
                                    name = pdir.name.replace("_", " ").title()
                                    link = f"#/eng/{dlang}/{doc_id}/{pdir.name}"
                                    projects_html.append(f"<a href='{link}' class='btn mod-btn de-btn-{lang}'>💻 Run {lang.capitalize()}: {name}</a>")
                    projects_html.append("</div>")
                    if len(projects_html) > 2:
                        data["html"] += "\\n".join(projects_html)
                self._json(data)"""

code = code.replace(old_str, new_str)

with open("webapp/server.py", "w") as f:
    f.write(code)
