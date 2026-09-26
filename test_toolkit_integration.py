from pathlib import Path
import os

TOOL_KIT_DIR = Path("./Tool-Kit")

def get_integrated_markdown(req_id):
    p1 = TOOL_KIT_DIR / req_id / f"{req_id}.md"
    p2 = TOOL_KIT_DIR / f"{req_id}.md"
    doc_path = p1 if p1.exists() else (p2 if p2.exists() else None)
    
    if not doc_path:
        return None
        
    markdown = doc_path.read_text()
    
    topic_dir = doc_path.parent
    examples = []
    for ex_dir in sorted(topic_dir.glob("examples/*")):
        if ex_dir.is_dir():
            examples.append(ex_dir)
    for ex_dir in sorted(topic_dir.glob("examples_go/*")):
        if ex_dir.is_dir():
            examples.append(ex_dir)
            
    if examples:
        markdown += "\n\n---\n\n## Examples & Exercises\n\n"
        for ex in examples:
            markdown += f"### {ex.name}\n\n"
            readme = ex / "README.md"
            if readme.exists():
                markdown += readme.read_text() + "\n\n"
            
            for f in sorted(ex.iterdir()):
                if f.is_file() and f.name != "README.md":
                    lang = "bash"
                    if f.name.endswith(".py"): lang = "python"
                    elif f.name.endswith(".go"): lang = "go"
                    elif f.name.endswith(".yaml") or f.name.endswith(".yml"): lang = "yaml"
                    elif f.name == "Dockerfile": lang = "dockerfile"
                    elif f.name.endswith(".js"): lang = "javascript"
                    elif f.name.endswith(".json"): lang = "json"
                    elif f.name.endswith(".txt") or f.name.endswith(".env"): lang = "text"
                    markdown += f"**`{f.name}`**\n\n```{lang}\n{f.read_text().strip()}\n```\n\n"
                    
    return markdown

print(len(get_integrated_markdown("Docker_Container") or ""))
