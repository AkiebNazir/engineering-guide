"""
LAB 05 (advanced) - Safe retries and stable pagination
======================================================
You will learn
  * Idempotency-Key: a retried POST /payments must NOT charge twice
      - same key + same body   -> replay the saved response
      - same key + other body  -> 422 (client bug)
      - same key while running -> 409 (still in flight)
  * a REAL race: 8 threads fire the same request at once and exactly one charge happens
  * keyset (cursor) pagination: stable and fast, unlike OFFSET which duplicates rows when data changes

Needs   pip install fastapi httpx
Run it  python 05_idempotency_and_cursor_pagination.py
"""
import base64
import hashlib
import json
import threading
import time

from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.testclient import TestClient

app = FastAPI()

# ============================ idempotency ====================================
CHARGES: list[dict] = []
KEYS: dict[str, dict] = {}            # key -> {"fingerprint", "state", "status", "body"}
LOCK = threading.Lock()               # production: Redis SET NX / DB unique constraint


@app.post("/payments", status_code=201)
def pay(payload: dict, response: Response, idempotency_key: str = Header(...)):
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    with LOCK:
        saved = KEYS.get(idempotency_key)
        if saved is None:
            KEYS[idempotency_key] = {"fingerprint": fingerprint, "state": "running"}   # reserve the key
        elif saved["fingerprint"] != fingerprint:
            raise HTTPException(422, "Idempotency-Key reused with a different request body")
        elif saved["state"] == "running":
            raise HTTPException(409, "a request with this key is still being processed")
        else:
            response.headers["Idempotent-Replay"] = "true"
            response.status_code = saved["status"]
            return saved["body"]                          # replay - NO second charge

    time.sleep(0.05)                                      # pretend to call the card network
    charge = {"charge_id": f"ch_{len(CHARGES) + 1}", "amount": payload["amount"]}
    CHARGES.append(charge)
    with LOCK:
        KEYS[idempotency_key].update(state="done", status=201, body=charge)
    return charge


# ============================ cursor pagination ==============================
ITEMS = [{"id": i, "name": f"item-{i}"} for i in range(1, 26)]     # sorted by id


def encode_cursor(last_id: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"id": last_id}).encode()).decode()


def decode_cursor(cursor: str) -> int:
    try:
        return json.loads(base64.urlsafe_b64decode(cursor))["id"]
    except Exception:
        raise HTTPException(400, "invalid cursor")


@app.get("/items")
def list_items(limit: int = 10, cursor: str | None = None):
    limit = max(1, min(limit, 100))                       # ALWAYS cap the page size
    after = decode_cursor(cursor) if cursor else 0
    # SQL equivalent:  SELECT * FROM items WHERE id > :after ORDER BY id LIMIT :limit+1
    rows = [i for i in ITEMS if i["id"] > after][: limit + 1]      # fetch one extra to know "has_more"
    page, has_more = rows[:limit], len(rows) > limit
    return {"data": page, "has_more": has_more, "next_cursor": encode_cursor(page[-1]["id"]) if has_more else None}


def demo():
    c = TestClient(app)
    body = {"amount": 500}

    # -- basic replay ---------------------------------------------------------
    r1 = c.post("/payments", json=body, headers={"Idempotency-Key": "k1"})
    r2 = c.post("/payments", json=body, headers={"Idempotency-Key": "k1"})
    print("first  ->", r1.status_code, r1.json())
    print("retry  ->", r2.status_code, r2.json(), "replay header:", r2.headers.get("idempotent-replay"))
    assert r1.json() == r2.json() and len(CHARGES) == 1

    r3 = c.post("/payments", json={"amount": 999}, headers={"Idempotency-Key": "k1"})
    print("same key, other body ->", r3.status_code)
    assert r3.status_code == 422

    # -- a real race ----------------------------------------------------------
    results = []
    def fire():
        r = TestClient(app).post("/payments", json=body, headers={"Idempotency-Key": "race"})
        results.append(r.status_code)
    threads = [threading.Thread(target=fire) for _ in range(8)]
    [t.start() for t in threads]; [t.join() for t in threads]
    race_charges = [ch for ch in CHARGES if ch["charge_id"] != "ch_1"]
    print(f"8 concurrent requests -> statuses {sorted(results)} ; charges created: {len(race_charges)}")
    assert len(race_charges) == 1 and results.count(201) >= 1   # exactly ONE charge no matter what

    # -- pagination -----------------------------------------------------------
    seen, cursor, pages = [], None, 0
    while True:
        r = c.get("/items", params={"limit": 10, **({"cursor": cursor} if cursor else {})}).json()
        seen += [i["id"] for i in r["data"]]
        pages += 1
        if not r["has_more"]:
            break
        cursor = r["next_cursor"]
    print(f"walked {pages} pages -> ids {seen[0]}..{seen[-1]}, total {len(seen)}")
    assert seen == list(range(1, 26))

    # Rows inserted at the FRONT while a client is mid-walk: cursor pagination does not repeat anything.
    first = c.get("/items", params={"limit": 10}).json()
    ITEMS.insert(0, {"id": 0, "name": "new-front-row"})    # OFFSET pagination would now repeat id 10 on page 2
    second = c.get("/items", params={"limit": 10, "cursor": first["next_cursor"]}).json()
    overlap = {i["id"] for i in first["data"]} & {i["id"] for i in second["data"]}
    print("overlap between page 1 and 2 after a concurrent insert:", overlap or "none")
    assert not overlap
    assert c.get("/items", params={"cursor": "garbage"}).status_code == 400
    print("OK")


if __name__ == "__main__":
    demo()
