import csv
import pathlib

def snake(s): return s.replace("-", "_")

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY_DSA = ROOT / "content" / "interview-core" / "PyDSA"
GO_DSA = ROOT / "content" / "interview-core" / "GoDSA"
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
    py_q = PY_DSA / topic / f"{seq}_{slug}_question.py"
    py_s = PY_DSA / topic / f"{seq}_{slug}_solution.py"
    if not py_q.exists() or not py_s.exists():
        missing_py.append(f"content/interview-core/PyDSA/{topic}/{seq}_{slug}")
        
    # Check GoDSA
    go_q = GO_DSA / topic / f"{seq}_{slug}" / "question.go"
    go_s = GO_DSA / topic / f"{seq}_{slug}" / "solution.go"
    if not go_q.exists() or not go_s.exists():
        missing_go.append(f"content/interview-core/GoDSA/{topic}/{seq}_{slug}")

print(f"Missing Py: {len(missing_py)}")
print(f"Missing Go: {len(missing_go)}")
if missing_go:
    print("First 10 missing Go:", missing_go[:10])
