#!/usr/bin/env python3
import csv
import pathlib
import os
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
TSV = ROOT / "tools" / "problems.tsv"

def snake(slug):
    return slug.replace("-", "_")

def extract_comment_block(py_file_path):
    if not py_file_path.exists():
        return ""
    content = py_file_path.read_text(encoding="utf-8")
    
    # Extract the main block comment enclosed in """ ... """
    match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def main():
    with TSV.open() as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    created_count = 0
    
    for r in rows:
        topic = r["topic"]
        seq = r["seq"]
        slug = snake(r["slug"])
        
        go_dir = ROOT / "GoDSA" / topic / f"{seq}_{slug}"
        go_q = go_dir / "question.go"
        go_s = go_dir / "solution.go"
        
        if not go_q.exists() or not go_s.exists():
            go_dir.mkdir(parents=True, exist_ok=True)
            
            py_q = ROOT / "PyDSA" / topic / f"{seq}_{slug}_question.py"
            comment = extract_comment_block(py_q)
            
            if not go_q.exists():
                with go_q.open("w", encoding="utf-8") as f:
                    f.write("package main\n\n")
                    f.write("/*\n")
                    f.write(comment + "\n")
                    f.write("*/\n\n")
                    f.write("// TODO: Implement the stub\n")
            
            if not go_s.exists():
                with go_s.open("w", encoding="utf-8") as f:
                    f.write("package main\n\n")
                    f.write("import \"fmt\"\n\n")
                    f.write("/*\n")
                    f.write(comment + "\n")
                    f.write("*/\n\n")
                    f.write("func main() {\n")
                    f.write(f"\tfmt.Println(\"Solution for {r['title']} not implemented yet\")\n")
                    f.write("}\n")
            
            created_count += 1

    print(f"Scaffolded Go files for {created_count} problems.")

if __name__ == "__main__":
    main()
