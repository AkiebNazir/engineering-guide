#!/usr/bin/env python3
"""Keep file names out of the prose: a reference to another page is a titled link.

Readers see pages, not the repo tree, so a guide that says "see
`03_api_design_high_level.md`" should say "see [API Design — High Level](...)".
This tool finds every such reference in the learner-facing markdown and
rewrites it as a link titled with the target page's own heading:

  `03_api_design_high_level.md`             -> [API Design — High Level](03_api_design_high_level.md)
  `CSFundamentals/03_x_deep_dive.md` §5     -> [<its title>](../CSFundamentals/03_x_deep_dive.md) §5
  [06_stack/_TOPIC_GUIDE.md](../06_stack/…) -> [Stack topic guide (Go)](../06_stack/…)
  `PyDSA/08_linked_list/014_x_solution.py`  -> [<LeetCode title>](../08_linked_list/014_x_solution.py)

Only references that resolve to a tracked page are touched. Code stays code:
fenced blocks are skipped, and a source file the app has no page for
(`app.py` in a lab's run instructions) is left as it is.

    python3 tools/link_file_refs.py            # report; exit 1 if anything needs fixing
    python3 tools/link_file_refs.py --write    # rewrite in place

The report also lists relative links to .md/.py/.go files that point nowhere.
Developer notes (CONTEXT.md, REVIEW_LEDGER.md, the generated CURRICULUM.md,
webapp/, _archive/) are out of scope: file paths are their subject.
"""
import csv
import os
import re
import subprocess
import sys
from collections import Counter

ROOT = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
os.chdir(ROOT)
TRACKED = set(subprocess.check_output(['git', 'ls-files'], text=True).split('\n'))


# The curriculum lives in content/<group>/<Module>/; the page patterns below (and the app's
# reader) speak in module-rooted paths ("PyDSA/01_x/..."). virt() maps a real path to that
# form; links are always computed between real paths.
def virt(p):
    m = re.match(r'^content/[\w-]+/(.+)$', p)
    return m.group(1) if m else p


VIRT2REAL = {virt(p): p for p in TRACKED}
DEV_NOTES = re.compile(r'^(_archive/|webapp/|docs/|.*node_modules/|CONTEXT\.md$|REVIEW_LEDGER\.md$|CURRICULUM\.md$)')
DOCS = sorted(p for p in TRACKED if p.endswith('.md') and not DEV_NOTES.match(virt(p)))
BY_NAME = {}
for p in TRACKED:
    BY_NAME.setdefault(os.path.basename(p), []).append(p)


def module_root(p):
    """content/<group>/<Module> for a curriculum file, else its first folder"""
    parts = p.split('/')
    return '/'.join(parts[:3]) if parts[0] == 'content' and len(parts) > 3 else (parts[0] if len(parts) > 1 else '')

# source files the app shows as a page of their own
PAGE_SOURCES = re.compile(r'^((Py|Go)DSA/\d{2}_\w+/\d{3}_|API/\w+/(Foundation|labs)/(python|golang)/'
                          r'|SoftwareDesign/lld/|(Py|Go)StdLib/\d+_\w+/level_)')
DSA_FILE = re.compile(r'^(?:Py|Go)DSA/(\d{2}_\w+?)/(\d{3})_\w+?(?:(?:_(?:question|solution))?\.(?:py|go)|/(?:question|solution)\.go)$')

with open('tools/problems.tsv', encoding='utf-8') as fh:
    PROBLEMS = {(r['topic'], r['seq']): r['title'] for r in csv.DictReader(fh, delimiter='\t')}


def plain(t):
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)
    t = re.sub(r'[`*_]{1,3}([^`*_]+)[`*_]{1,3}', r'\1', t)
    t = re.sub(r'[\U0001F000-\U0001FFFF☀-➿️]', '', t)
    return re.sub(r'\s+', ' ', t).strip(' #:')


def from_name(name):
    s = re.sub(r'\.[a-z]+$', '', name, flags=re.I)
    s = re.sub(r'^(level_)?\d+_', '', s)
    s = re.sub(r'_(solution|question|deep_dive)$', '', s)
    s = re.sub(r'[_-]+', ' ', s)
    return s[:1].upper() + s[1:]


def shorten(t):
    """"002 — Rate Limiter: Full System Design Solution" -> "Rate Limiter"; a long
    "Main Title — subtitle" keeps the main title when it can stand alone"""
    t = re.sub(r'^\d{2,3}\s*[—–·:-]\s*', '', t)
    t = re.sub(r':\s*Full System Design Solution$', '', t)
    if len(t) > 50:
        head = re.split(r' — |: ', t, maxsplit=1)[0]
        if len(head) >= 10 and head != t:
            t = head
    return t


_titles = {}
def title_of(path):
    if path in _titles:
        return _titles[path]
    v = virt(path)
    m = DSA_FILE.match(v)
    if path.endswith('.md'):
        with open(path, encoding='utf-8') as fh:
            head = fh.read(20000)
        h = re.search(r'^# +(.+)$', head, re.M) or re.search(r'^#{2,3} +(.+)$', head, re.M)
        t = plain(h.group(1)) if h else ''
        if path.endswith('_TOPIC_GUIDE.md'):
            topic = re.sub(r'^Topic \d+ · ', '', t).split(' — ')[0] or from_name(v.split('/')[1])
            t = f"{topic} topic guide ({'Go' if v.startswith('GoDSA') else 'Python'})"
        t = t or from_name(os.path.basename(os.path.dirname(path)) if path.endswith('README.md') else os.path.basename(path))
    elif m:
        t = PROBLEMS.get((m.group(1), m.group(2))) or from_name(v.split('/')[2])
    else:
        t = from_name(os.path.basename(path))
    _titles[path] = t = shorten(t)
    return t


def resolve(ref, doc):
    """a reference as written in `doc` -> the tracked page it means, or None"""
    p = re.sub(r'^\./', '', ref.split('#')[0])
    if not re.search(r'\.(md|py|go)$', p) or re.search(r'[<>*{}\s]|NN|XX', p):
        return None
    mod = module_root(doc)
    cands = [os.path.normpath(os.path.join(os.path.dirname(doc), p)), os.path.normpath(p),
             VIRT2REAL.get(os.path.normpath(p), '')]      # a module-rooted path ("SystemDesign/…")
    if mod:
        cands.append(os.path.normpath(os.path.join(mod, p)))
    hit = next((c for c in cands if c in TRACKED), None)
    if not hit and '/' not in p:
        same = BY_NAME.get(p, [])
        near = [x for x in same if mod and x.startswith(mod + '/')]
        hit = near[0] if len(near) == 1 else same[0] if len(same) == 1 and p.endswith('.md') else None
    if not hit:
        return None
    if hit.endswith('.md'):
        return None if DEV_NOTES.match(virt(hit)) and virt(hit) not in ('REVIEW_LEDGER.md', 'CURRICULUM.md') else hit
    return hit if PAGE_SOURCES.match(virt(hit)) else None


FENCE = re.compile(r'^\s*(```|~~~)')
LINK = re.compile(r'\[((?:`[^`]*`|[^\[\]])*)\]\(([^)\s]+)\)')
TICK = re.compile(r'`([^`\n]+)`')
is_path_text = lambda s: re.fullmatch(r'`?[^\s`]+\.(md|py|go)(#[\w-]*)?`?', s.strip()) is not None

fixes = Counter()
broken = []


def fix_line(line, doc, n):
    def retitle(m):
        text, href = m.group(1), m.group(2)
        if re.match(r'^[a-z]+:', href):
            return m.group(0)
        if re.search(r'\.(md|py|go)(#.*)?$', href) and not resolve(href, doc):
            target = href.split('#')[0]
            # the reader also accepts repo-root paths ("SystemDesign/…") from any page
            if (os.path.normpath(os.path.join(os.path.dirname(doc), target)) not in TRACKED
                    and target not in TRACKED and target not in VIRT2REAL):
                broken.append(f'{doc}:{n}: {href}')
        if is_path_text(text):
            tgt = resolve(href, doc) or resolve(text.strip().strip('`'), doc)
            if tgt:
                fixes['link text'] += 1
                return f'[{title_of(tgt)}]({href})'
        return m.group(0)

    line = LINK.sub(retitle, line)
    masked = LINK.sub(lambda m: '\0' * len(m.group(0)), line)    # leave link texts and targets alone
    out, last = [], 0
    for m in TICK.finditer(masked):
        ref = m.group(1).strip()
        tgt = re.search(r'\.(md|py|go)(#[\w-]*)?$', ref) and resolve(ref, doc)
        if not tgt:
            continue
        anchor = '#' + ref.split('#', 1)[1] if '#' in ref else ''
        out += [line[last:m.start()], f'[{title_of(tgt)}]({os.path.relpath(tgt, os.path.dirname(doc) or ".")}{anchor})']
        last = m.end()
        fixes['file name'] += 1
    return ''.join(out) + line[last:]


def main():
    write = '--write' in sys.argv
    changed = []
    for doc in DOCS:
        with open(doc, encoding='utf-8') as fh:
            lines = fh.read().split('\n')
        fenced, new = False, []
        for n, ln in enumerate(lines, 1):
            if FENCE.match(ln):
                fenced = not fenced
                new.append(ln)
            else:
                new.append(ln if fenced else fix_line(ln, doc, n))
        if new != lines:
            changed.append(doc)
            if write:
                with open(doc, 'w', encoding='utf-8') as fh:
                    fh.write('\n'.join(new))
    verb = 'rewrote' if write else 'would rewrite'
    print(f'{len(DOCS)} pages checked; {verb} {sum(fixes.values())} references in {len(changed)} files '
          f"({fixes['file name']} file names, {fixes['link text']} link texts)")
    for d in changed[:40]:
        print(f'  {d}')
    if broken:
        print(f'{len(broken)} links point at files that do not exist:')
        for b in broken:
            print(f'  {b}')
    sys.exit(1 if (changed and not write) or broken else 0)


if __name__ == '__main__':
    main()
