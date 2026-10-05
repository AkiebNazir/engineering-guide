"""
LAB 04 (advanced) - HTTP caching and optimistic concurrency with ETag
=====================================================================
You will learn
  * ETag + If-None-Match  -> 304 Not Modified   (save bandwidth, keep caches correct)
  * ETag + If-Match       -> 412 Precondition Failed  (stop two editors silently overwriting each other)
  * 428 Precondition Required: forcing clients to send If-Match at all
  * Cache-Control for public/private caching

The "lost update" problem this fixes:
    alice loads doc v1 -> bob loads doc v1 -> alice saves -> bob saves  (alice's edit is gone!)

Needs   pip install fastapi httpx
Run it  python 04_etag_conditional_requests.py
"""
import hashlib
import json

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.testclient import TestClient

app = FastAPI()
DOCS = {1: {"id": 1, "title": "Design doc", "body": "v1 text", "version": 1}}


def etag_of(doc: dict) -> str:
    """A strong validator: changes iff the representation changes."""
    digest = hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()[:16]
    return f'"{digest}"'                                   # ETags are quoted strings


@app.get("/docs/{doc_id}")
def read(doc_id: int, request: Request, response: Response):
    doc = DOCS.get(doc_id)
    if not doc:
        raise HTTPException(404, "doc not found")
    tag = etag_of(doc)
    headers = {"ETag": tag, "Cache-Control": "private, max-age=0, must-revalidate"}
    # "Do you still have this exact version?  Then I will not resend it."
    if request.headers.get("if-none-match") == tag:
        return Response(status_code=304, headers=headers)      # no body at all
    response.headers.update(headers)
    return doc


@app.put("/docs/{doc_id}")
def replace(doc_id: int, new: dict, response: Response, if_match: str | None = Header(default=None)):
    doc = DOCS.get(doc_id)
    if not doc:
        raise HTTPException(404, "doc not found")
    if if_match is None:
        raise HTTPException(428, "send If-Match with the ETag you last read")   # force safe clients
    if if_match != etag_of(doc):
        raise HTTPException(412, "document changed since you read it; reload and retry")
    DOCS[doc_id] = {"id": doc_id, "title": new["title"], "body": new["body"], "version": doc["version"] + 1}
    response.headers["ETag"] = etag_of(DOCS[doc_id])
    return DOCS[doc_id]


def demo():
    c = TestClient(app)

    r = c.get("/docs/1")
    tag = r.headers["etag"]
    print("first GET        ->", r.status_code, "ETag", tag, "body bytes:", len(r.content))

    r = c.get("/docs/1", headers={"If-None-Match": tag})
    print("revalidate       ->", r.status_code, "body bytes:", len(r.content), "(cache copy is still good)")
    assert r.status_code == 304 and r.content == b""

    # ---- the lost-update scenario --------------------------------------------
    alice_tag = bob_tag = tag                       # both loaded version 1
    r = c.put("/docs/1", json={"title": "Design doc", "body": "alice's edit"}, headers={"If-Match": alice_tag})
    print("alice PUT        ->", r.status_code, "new ETag", r.headers["etag"])
    assert r.status_code == 200 and r.json()["version"] == 2

    r = c.put("/docs/1", json={"title": "Design doc", "body": "bob's edit"}, headers={"If-Match": bob_tag})
    print("bob PUT (stale)  ->", r.status_code, r.json()["detail"])
    assert r.status_code == 412 and DOCS[1]["body"] == "alice's edit"     # alice's work survived

    r = c.put("/docs/1", json={"title": "x", "body": "y"})
    print("PUT w/o If-Match ->", r.status_code, r.json()["detail"])
    assert r.status_code == 428

    # ---- bob reloads, merges, retries ---------------------------------------
    fresh = c.get("/docs/1")
    r = c.put("/docs/1", json={"title": "Design doc", "body": fresh.json()["body"] + " + bob"},
              headers={"If-Match": fresh.headers["etag"]})
    print("bob after reload ->", r.status_code, r.json()["body"])
    assert r.status_code == 200 and r.json()["version"] == 3
    print("OK")


if __name__ == "__main__":
    demo()
