import csv
import pathlib

def snake(s): return s.replace("-", "_")

ROOT = pathlib.Path(".")
TSV = ROOT / "tools" / "problems.tsv"

with TSV.open() as fh:
    rows = list(csv.DictReader(fh, delimiter="\t"))

missing_py = []
missing_go = []

for r in rows:
    topic = r["topic"]
    seq = r["seq"]
    slug = snake(r["slug"])
    
    # Check PyDSA
    py_q = ROOT / "PyDSA" / topic / f"{seq}_{slug}_question.py"
    py_s = ROOT / "PyDSA" / topic / f"{seq}_{slug}_solution.py"
    if not py_q.exists() or not py_s.exists():
        missing_py.append(f"PyDSA/{topic}/{seq}_{slug}")
        
    # Check GoDSA
    go_q = ROOT / "GoDSA" / topic / f"{seq}_{slug}" / "question.go"
    go_s = ROOT / "GoDSA" / topic / f"{seq}_{slug}" / "solution.go"
    if not go_q.exists() or not go_s.exists():
        missing_go.append(f"GoDSA/{topic}/{seq}_{slug}")

print(f"Missing Py: {len(missing_py)}")
print(f"Missing Go: {len(missing_go)}")
if missing_go:
    print("First 10 missing Go:", missing_go[:10])
