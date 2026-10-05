#!/usr/bin/env python3
"""Build the static site: a self-contained folder any static host can serve.

    python3 webapp/build_static.py              # → dist/
    python3 webapp/build_static.py --out DIR    # → DIR/

The output is the app's front end (webapp/static/) plus every GET /api/* answer
the client asks for, pre-rendered to data/*.json. Answers come from server.py's
own api_get(), so the static site shows exactly what the local server shows.
Nothing in it needs a server: deploy the folder to GitHub Pages, Netlify,
Cloudflare Pages, Vercel, S3 + CloudFront, nginx, … as is.

What the static site cannot do (it has no backend): run code, and save progress
to webapp/data/progress.json. Progress is kept in the visitor's browser instead.

Standard library only; Python 3.10+.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import server  # noqa: E402  (needs the path above)

DEFAULT_OUT = server.ROOT / "dist"
SAFE = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.")


def static_key_escape(s: str) -> str:
    """File-name-safe form of a query: A-Z a-z 0-9 - _ . kept, every other UTF-8 byte → ~XX."""
    return "".join(chr(b) if b in SAFE else f"~{b:02X}" for b in s.encode())


def static_data_path(url: str) -> str:
    """/api/<name>?<query> → data/<name>[/<key>].json — twin of staticDataPath() in static/app.js."""
    u = urlparse(url)
    params = sorted(((k, v) for k, vs in parse_qs(u.query, keep_blank_values=True).items() for v in vs),
                    key=lambda kv: kv[0])
    key = "&".join(f"{k}={v}" for k, v in params)
    name = u.path.removeprefix("/api/")
    return f"data/{name}{'/' + static_key_escape(key) if key else ''}.json"


def api_url(path: str, **params: str) -> str:
    return f"{path}?{urlencode(params)}" if params else path


def client_requests() -> list[str]:
    """Every GET /api/* request the client can make, written the way the client writes it.

    Keep in step with the api(...) calls in static/*.js: app.js (problems, eng
    topics), reader.js (MODULES list/doc pairs), dsa-learn.js, api-practice.js,
    stdlib-practice.js, roadmap.js.
    """
    urls = ["/api/bootstrap", "/api/dsa-map"]

    # DSA problems (app.js): question + solution tabs, both languages
    problems = server.load_curriculum()
    for p in problems:
        for kind in ("question", "solution"):
            for lang in ("py", "go"):
                urls.append(api_url("/api/problem", topic=p["topic"], seq=p["seq"], kind=kind, lang=lang))

    # Go / Py Engineering and Software Design LLD workspaces (app.js engTabs)
    for lang in ("go", "py", "lld"):
        kinds = ("explanation", "solution") if lang == "lld" else ("explanation", "solution", "test")
        for t in server.load_eng_curriculum(lang):
            for kind in kinds:
                urls.append(api_url("/api/eng-problem", lang=lang, topic=t["id"], kind=kind))

    # Reading modules (reader.js MODULES): one list call, then one doc call per item
    modules = [("/api/sd", "/api/sd-doc", {}),
               ("/api/software-design", "/api/software-design-doc", {}),
               ("/api/roadmap", "/api/roadmap-doc", {}),
               ("/api/library-guides", "/api/library-guide-doc", {}),
               ("/api/agentic-ai", "/api/agentic-ai-doc", {}),
               ("/api/apis", "/api/apis-doc", {}),
               ("/api/cs-fundamentals", "/api/cs-fundamentals-doc", {}),
               ("/api/google-behavioral", "/api/google-behavioral-doc", {}),
               ("/api/sql", "/api/sql-doc", {}),
               ("/api/nosql", "/api/nosql-doc", {})]
    modules += [("/api/track", "/api/track-doc", {"m": m}) for m in server.TRACK_DIRS]
    modules += [("/api/dsa-guides", "/api/dsa-guide-doc", {"lang": lang}) for lang in ("py", "go")]
    for list_path, doc_path, extra in modules:
        urls.append(api_url(list_path, **extra))
        reply = server.api_get(list_path, {k: [v] for k, v in extra.items()})
        for item in reply[0]["items"]:
            urls.append(api_url(doc_path, **extra, id=item["id"]))

    # Standard-library modules (stdlib-practice.js)
    for lang in ("py", "go"):
        urls.append(api_url("/api/stdlib", lang=lang))
        for pkg in server.load_stdlib(lang):
            urls.append(api_url("/api/stdlib-doc", lang=lang, id=pkg["id"]))
            for level in pkg.get("levels", []):
                urls.append(api_url("/api/stdlib-file", lang=lang, pkg=pkg["id"], level=level["id"]))

    # API practice ladders (api-practice.js)
    urls.append("/api/api-types")
    for t in server.load_api_types():
        urls.append(api_url("/api/api-type", type=t["id"]))
        for section in ("Foundation", "labs"):
            for level in server.api_ladder(t["id"], section):
                for lang in ("py", "go"):
                    if level["has"].get(lang):
                        urls.append(api_url("/api/api-file", type=t["id"], section=section,
                                            level=level["id"], lang=lang))
    return list(dict.fromkeys(urls))       # de-duplicated, order kept


def build(out: Path) -> None:
    out, static = out.resolve(), server.STATIC.resolve()
    if server.ROOT.resolve().is_relative_to(out) or static.is_relative_to(out) or out.is_relative_to(static):
        sys.exit(f"Refusing to build into {out}: it would delete or overwrite source files.")
    print(f"Building static site → {out}")
    if out.exists():
        shutil.rmtree(out)
    junk = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")

    def ignore(folder: str, names: list[str]) -> set[str]:
        skip = set(junk(folder, names))
        if Path(folder).resolve() == static:
            skip.add("data")           # leftovers of older builds, which wrote into static/data/
        return skip

    shutil.copytree(server.STATIC, out, ignore=ignore)

    # Switch the client to static mode (see static/config.js).
    (out / "config.js").write_text(
        "/* Generated by webapp/build_static.py: this is a static build. */\nwindow.EG_STATIC = true;\n")
    # GitHub Pages: serve files as they are (no Jekyll processing).
    (out / ".nojekyll").write_text("")

    written, skipped, seen = 0, [], {}
    for url in client_requests():
        u = urlparse(url)
        status_payload = server.api_get(u.path, parse_qs(u.query, keep_blank_values=True))
        assert status_payload is not None, f"not an API route: {url}"
        payload, status = status_payload
        if status != 200:
            # The local server answers 404 here too; the static host will do the same.
            skipped.append(url)
            continue
        if u.path == "/api/bootstrap":
            # Ship a clean slate, not the local progress.json; no code runner online.
            payload = {**payload, "state": server.default_state(),
                       "runtimes": {"python": False, "go": False}, "root": ""}
        rel = static_data_path(url)
        if rel in seen:
            sys.exit(f"Static path collision: {url} and {seen[rel]} → {rel}")
        seen[rel] = url
        if len(Path(rel).name) > 200:
            sys.exit(f"Static file name too long for some hosts: {rel}")
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(payload, separators=(",", ":")))
        written += 1

    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"  {written} data files written, {len(skipped)} skipped (the server answers 404 for them too)")
    print(f"  {size / 1e6:.1f} MB total")
    print(f"Done. Preview it with:  python3 -m http.server -d {out} 8000   (or: make preview)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output folder (default: {DEFAULT_OUT})")
    build(ap.parse_args().out)


if __name__ == "__main__":
    main()
