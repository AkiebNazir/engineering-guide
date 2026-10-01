#!/usr/bin/env python3
"""Run every Python snippet in Maths/*.md and check its printed results.

The Maths module states numbers; this keeps them honest. For each chapter:

  * every ```python block runs, in order, in one namespace per chapter
    (like cells of a notebook), so later blocks may use earlier definitions;
  * a line written as `print(expr)  # → expected` must print exactly
    `expected`, exactly once (the arrow comment is the book's claim);
  * `assert` lines are checked simply by running.

A block whose first line is `# no-run` is skipped (pseudo-code, or code that
needs input). Exits non-zero on any failure, so it can gate a commit.

    python3 tools/check_maths_snippets.py            # all chapters
    python3 tools/check_maths_snippets.py 07 10      # chapters by number
"""
from __future__ import annotations

import builtins
import contextlib
import io
import re
import sys
import traceback
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATHS = ROOT / "Maths"
FENCE = re.compile(r"^```python[^\n]*\n(.*?)^```", re.S | re.M)
ARROW = re.compile(r"^\s*print\(.*\)\s*#\s*→\s*(.*?)\s*$")


def check_chapter(path: Path) -> tuple[int, int, list[str]]:
    text = path.read_text()
    ns: dict = {"__name__": "__main__"}
    blocks = checks = 0
    errors: list[str] = []
    for bi, m in enumerate(FENCE.finditer(text), 1):
        code = m.group(1)
        if code.lstrip().startswith("# no-run"):
            continue
        blocks += 1
        start_line = text[: m.start()].count("\n") + 2  # first code line in the .md
        fname = f"{path.name}:block{bi}"
        printed: dict[int, list[str]] = defaultdict(list)
        real_print = builtins.print

        def recording_print(*args, sep=" ", end="\n", file=None, flush=False):
            frame = sys._getframe(1)
            if frame.f_code.co_filename == fname:
                printed[frame.f_lineno].append(sep.join(map(str, args)))
            if file is None:
                real_print(*args, sep=sep, end=end, file=sink, flush=flush)
            else:
                real_print(*args, sep=sep, end=end, file=file, flush=flush)

        sink = io.StringIO()
        ns["print"] = recording_print
        try:
            with contextlib.redirect_stdout(sink):
                exec(compile(code, fname, "exec"), ns)
        except Exception:  # noqa: BLE001 - report every kind of failure
            tb = traceback.format_exc(limit=3).strip().splitlines()[-1]
            errors.append(f"{path.name} line {start_line}: block raised {tb}")
            continue
        for li, line in enumerate(code.splitlines(), 1):
            am = ARROW.match(line)
            if not am:
                continue
            checks += 1
            want, got = am.group(1), printed.get(li, [])
            md_line = start_line + li - 1
            if len(got) != 1:
                errors.append(f"{path.name} line {md_line}: expected one print, got {len(got)}: {got[:3]}")
            elif got[0] != want:
                errors.append(f"{path.name} line {md_line}: claims {want!r}, prints {got[0]!r}")
    return blocks, checks, errors


def main(argv: list[str]) -> int:
    files = sorted(MATHS.glob("[0-9][0-9]_*.md"))
    if argv:
        files = [f for f in files if f.name[:2] in argv]
    total_b = total_c = 0
    failed: list[str] = []
    for f in files:
        b, c, errs = check_chapter(f)
        total_b += b
        total_c += c
        failed += errs
        print(f"{'FAIL' if errs else 'ok  '} {f.name}: {b} blocks run, {c} printed claims checked")
    for e in failed:
        print("  ✗", e)
    print(f"\n{total_b} blocks, {total_c} claims, {len(failed)} failures")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
