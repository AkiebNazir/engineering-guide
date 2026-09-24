# Secure Code by Design

> "Security is a process, not a product." — Bruce Schneier
>
> "Make the secure way the easy way."

Most security vulnerabilities are not exotic. They are ordinary design mistakes in ordinary
code: a string concatenated into a query, a lookup that forgot the tenant, a URL fetched
without checking where it points, a comparison that leaks timing, an input with no size
limit. The OWASP Top 10 has been dominated by the same handful of categories for twenty
years.

The design lesson is that **"be careful" doesn't scale.** A codebase with 400 SQL queries
will have one that someone wrote carelessly. Secure design means structuring code so the
insecure version is **hard to write, easy to spot in review, and caught by tests** — the
same way `01`–`11` structure code so complexity and bugs are hard to introduce.

Examples are in **Python** with **Go** in §10. Every example was run; outputs are real.
All examples are defensive: they show vulnerable code only next to the fix, on local toy
data.

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| AuthN vs. AuthZ across services, OAuth/OIDC/JWT, KMS and envelope encryption, GDPR deletion, abuse prevention | `SystemDesign/building_blocks/14_security.md` |
| Where authorization lives in a layered service | `08_application_architecture_in_code.md` §5 |
| Keeping secrets and PII out of logs; redacting types | `10_designing_observable_code.md` §2, §9, §10 |
| Unsafe deserialisation (`pickle`, YAML) | `09_data_design_and_schema_evolution.md` §8 |
| Parse, don't validate; illegal states unrepresentable | `01_philosophy_of_software_design.md` §8 |
| Idempotency keys; error messages that don't leak internals | `06_error_handling_and_failure_design.md` §4, §8 |

---

## Contents

1. [Think in trust boundaries](#1--think-in-trust-boundaries)
2. [Injection: keep data from becoming code](#2--injection-keep-data-from-becoming-code)
3. [Authorization designed to be hard to forget](#3--authorization-designed-to-be-hard-to-forget)
4. [Secrets, randomness, passwords, and tokens](#4--secrets-randomness-passwords-and-tokens)
5. [Server-side request forgery (SSRF)](#5--server-side-request-forgery-ssrf)
6. [Resource exhaustion as a security bug](#6--resource-exhaustion-as-a-security-bug)
7. [Output encoding and cross-site scripting](#7--output-encoding-and-cross-site-scripting)
8. [Race conditions with security impact](#8--race-conditions-with-security-impact)
9. [Secure defaults and failing closed](#9--secure-defaults-and-failing-closed)
10. [The same ideas in Go](#10--the-same-ideas-in-go)
11. [Dependencies and the supply chain](#11--dependencies-and-the-supply-chain)
12. [Threat modeling in a design review](#12--threat-modeling-in-a-design-review)
13. [Testing security properties](#13--testing-security-properties)
14. [Red flags](#14--red-flags)
15. [Interview questions and model answers](#15--interview-questions-and-model-answers)
16. [Checklist](#16--checklist)

---

## 1 · Think in trust boundaries

A **trust boundary** is any point where data or control passes from something you don't
control to something you do. Every vulnerability in this file is untrusted data crossing a
boundary without being checked, encoded, or bounded.

```
 UNTRUSTED                               │  YOUR PROCESS                     │  INTERPRETERS / RESOURCES
                                         │                                   │
 HTTP body, headers, query, cookies  ──▶ │  parse + validate + bound  ──▶    │ ──▶ SQL engine        (injection)
 uploaded files, archives            ──▶ │  (typed domain objects)           │ ──▶ shell             (command injection)
 queue messages from other teams     ──▶ │                                   │ ──▶ filesystem        (path traversal)
 webhooks, third-party API responses ──▶ │  authorize against the            │ ──▶ HTTP client       (SSRF)
 DNS answers, URLs, redirects        ──▶ │  VERIFIED principal               │ ──▶ HTML/JS renderer  (XSS)
 environment the attacker influences ──▶ │                                   │ ──▶ regex engine, CPU (DoS)
                                         │  encode for the destination  ──▶  │ ──▶ logs              (log injection)
```

Rules that follow:

1. **Validate at the entry boundary; encode at the exit boundary.** Input validation
   ("is this a positive integer ≤ 100?") and output encoding ("escape this for SQL / HTML /
   shell") are different jobs. You need both; neither replaces the other.
2. **Identity comes from verified credentials, never from request fields.** A `user_id`
   in the JSON body or an `X-Tenant-ID` header is attacker-controlled.
3. **"Internal" is not "trusted".** Messages from another team's service, rows written by
   another system, and responses from partner APIs are inputs too. Most breaches pivot
   through something that was trusted because it was internal.
4. **Minimise the surface.** Every endpoint, flag, parser, and dependency is attack
   surface. Code that doesn't exist has no vulnerabilities.

---

## 2 · Injection: keep data from becoming code

Injection happens whenever untrusted data is **concatenated into a string that another
interpreter parses** — SQL, a shell, a file path, HTML, LDAP, a template, a log line. The
fix is always the same shape: **pass data through a channel that the interpreter never
parses as code** (parameters, argv arrays, path APIs, auto-escaping templates).

The shape of the bug, stripped to just the strings involved — no database yet:

```python
def where_clause_unsafe(email: str) -> str:
    return f"SELECT role FROM users WHERE email = '{email}'"   # data becomes part of the query text


def where_clause_safe(email: str) -> tuple[str, tuple]:
    return "SELECT role FROM users WHERE email = ?", (email,)  # data stays a parameter, sent separately


attacker_input = "x' OR '1'='1"
print("unsafe query:", where_clause_unsafe(attacker_input))
print("safe query:  ", where_clause_safe(attacker_input))
```

Output:

```
unsafe query: SELECT role FROM users WHERE email = 'x' OR '1'='1'
safe query:   ('SELECT role FROM users WHERE email = ?', ("x' OR '1'='1",))
```

The unsafe version's `WHERE` clause now says "or true" — the attacker's string became
part of the query's logic. The safe version's query text never changes; the input travels
as data the SQL engine treats literally, however it's spelled. The example below shows
that same difference changing a query's *result* against a real database, plus the same
shape of bug in a shell command and a file path.

```python
# Injection: data crossing into an interpreter (SQL, shell, filesystem) must never become code.
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------- SQL ----------
db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, is_admin INTEGER)")
db.executemany("INSERT INTO users (email, is_admin) VALUES (?, ?)",
               [("ada@x.com", 1), ("bob@x.com", 0), ("eve@x.com", 0)])

def find_user_unsafe(email: str):
    return db.execute(f"SELECT id, email FROM users WHERE email = '{email}'").fetchall()

def find_user_safe(email: str):
    return db.execute("SELECT id, email FROM users WHERE email = ?", (email,)).fetchall()

attack = "nobody' OR '1'='1"
print("unsafe:", find_user_unsafe(attack))           # every user
print("safe:  ", find_user_safe(attack))             # nobody
assert len(find_user_unsafe(attack)) == 3 and find_user_safe(attack) == []

# Identifiers (column/table names) can't be parameters: allowlist them.
SORTABLE = {"email": "email", "id": "id"}
def list_users(sort: str):
    column = SORTABLE.get(sort)
    if column is None:
        raise ValueError(f"cannot sort by {sort!r}")
    return db.execute(f"SELECT email FROM users ORDER BY {column}").fetchall()
try:
    list_users("email; DROP TABLE users")
except ValueError as e:
    print("rejected:", e)

# ---------- Shell ----------
filename = "report.txt; echo INJECTED"
unsafe = subprocess.run(f"echo processing {filename}", shell=True, capture_output=True, text=True)
safe = subprocess.run(["echo", "processing", filename], capture_output=True, text=True)  # argv list, no shell
print("shell=True:", unsafe.stdout.split("\n")[:2])
print("argv list: ", safe.stdout.strip())
assert "INJECTED" in unsafe.stdout.splitlines() and safe.stdout.count("\n") == 1

# ---------- Filesystem: path traversal ----------
uploads = Path(tempfile.mkdtemp()).resolve()
(uploads / "invoice-1.pdf").write_text("ok")
secret = uploads.parent / "secret.env"
secret.write_text("DB_PASSWORD=hunter2")

def read_upload_unsafe(name: str) -> str:
    return (uploads / name).read_text()

def read_upload_safe(name: str) -> str:
    target = (uploads / name).resolve()               # collapses .. and follows symlinks
    if not target.is_relative_to(uploads):
        raise PermissionError(f"path escapes upload dir: {name!r}")
    return target.read_text()

evil = "../secret.env"
print("unsafe read:", read_upload_unsafe(evil))
try:
    read_upload_safe(evil)
except PermissionError as e:
    print("safe read:  ", e)
assert read_upload_safe("invoice-1.pdf") == "ok"
print("ALL PASSED")
```

Output:

```
unsafe: [(1, 'ada@x.com'), (2, 'bob@x.com'), (3, 'eve@x.com')]
safe:   []
rejected: cannot sort by 'email; DROP TABLE users'
shell=True: ['processing report.txt', 'INJECTED']
argv list:  processing report.txt; echo INJECTED
unsafe read: DB_PASSWORD=hunter2
safe read:   path escapes upload dir: '../secret.env'
ALL PASSED
```

| Interpreter | Vulnerable | Safe design |
|---|---|---|
| SQL | f-strings / `%` / `+` building queries | Placeholders (`?`, `%s`, `$1`) for values; **allowlist** for identifiers like sort columns; query builders / ORMs that parameterise |
| Shell | `shell=True`, `os.system`, `sh -c` with interpolation | `subprocess.run([...])` argv list; no shell; pass `--` before user-supplied arguments so `-rf` isn't read as an option |
| Filesystem | `base / user_name` then open | Generate server-side names (UUIDs) and store the user's name as metadata; if you must use user paths, resolve and check containment; Go `os.Root` (§10) |
| HTML | String templates, `innerHTML` | Auto-escaping templates (§7) |
| Logs | Writing raw user input with newlines | Structured JSON logs (`10` §2) escape control characters |
| Regex | `re.compile(user_input)` | `re.escape()` when matching literally |
| Templates | Rendering user-supplied *templates* (Jinja2 `Template(user_str)`) | Never; that is remote code execution (SSTI). Users supply data, not templates |

Design moves that make the safe version the default:

- **Repository methods take typed values, never SQL fragments** (`08` §4). There is no
  `where: str` parameter to concatenate into.
- **Ban the dangerous API with a linter**: Bandit (`B602` shell=True, `B608` SQL string
  building), Semgrep rules, `gosec` in Go. A pattern that fails CI is not a pattern that
  appears in code.
- **Prefer generated identifiers** over user-supplied names for anything that becomes a
  path, key, or command argument.

The `resolve()` + `is_relative_to` check above also follows symlinks, but it has a
time-of-check-to-time-of-use gap: a symlink swapped in between the check and the `open`
defeats it. Where attackers can write into the directory, use an API that resolves and opens
atomically relative to a directory handle (`openat`-style; Go's `os.Root`).

---

## 3 · Authorization designed to be hard to forget

Broken access control is the #1 category in the OWASP Top 10 (2021). The typical bug is
not a wrong rule; it is **a missing check** on one of hundreds of code paths — an endpoint
added later, an export job, a GraphQL resolver, a bulk API.

So design authorization so that forgetting it is structurally difficult:

Deny-by-default, minimal — the core idea the full example below builds on:

```python
PERMISSIONS = {"editor": {"read", "write"}, "viewer": {"read"}}


def can(role: str, action: str) -> bool:
    return action in PERMISSIONS.get(role, set())     # unknown role -> empty set -> denied


print("editor write:", can("editor", "write"))
print("viewer write:", can("viewer", "write"))
print("guest read:  ", can("guest", "read"))           # "guest" isn't in the table at all
```

Output:

```
editor write: True
viewer write: False
guest read:   False
```

`PERMISSIONS.get(role, set())` is the whole mechanism: a role that was never granted
anything — misspelled, new, or simply not written into the table yet — gets an empty
set back and every check fails. Nobody had to remember to deny `"guest"`; there's no
code path that grants by omission. The full example below adds the two things a real
authorization check also needs: the resource's own owner and tenant, and a principal
that can only come from a verified token.

```python
# Authorization designed so the secure path is the only path: deny by default,
# tenant scoping built into the repository, and an exhaustive authorization matrix test.
from dataclasses import dataclass
from enum import Enum, auto
from itertools import product


class Role(Enum):
    VIEWER = auto()
    EDITOR = auto()
    ADMIN = auto()


class Action(Enum):
    READ = auto()
    UPDATE = auto()
    DELETE = auto()
    SHARE = auto()


@dataclass(frozen=True)
class Principal:                     # built ONLY from a verified token, never from request fields
    user_id: str
    tenant_id: str
    role: Role


@dataclass
class Document:
    id: str
    tenant_id: str
    owner_id: str
    title: str


class NotFound(Exception): ...
class Forbidden(Exception): ...


# ---- policy: one table, deny by default ----
ALLOWED: dict[Role, set[Action]] = {
    Role.VIEWER: {Action.READ},
    Role.EDITOR: {Action.READ, Action.UPDATE},
    Role.ADMIN: {Action.READ, Action.UPDATE, Action.DELETE, Action.SHARE},
}

def can(p: Principal, action: Action, doc: Document) -> bool:
    if doc.tenant_id != p.tenant_id:
        return False                                      # never cross tenants, whatever the role
    if action in ALLOWED.get(p.role, set()):
        return True
    return doc.owner_id == p.user_id and action in {Action.READ, Action.UPDATE, Action.SHARE}


# ---- repository that cannot be queried without a tenant ----
class DocumentStore:
    def __init__(self):
        self._rows: dict[str, Document] = {}
    def put(self, d: Document):
        self._rows[d.id] = d
    def for_tenant(self, tenant_id: str) -> "TenantDocuments":
        return TenantDocuments(self._rows, tenant_id)


class TenantDocuments:
    """Every query is scoped; there is no method that ignores tenant_id."""
    def __init__(self, rows, tenant_id):
        self._rows, self._tenant = rows, tenant_id
    def get(self, doc_id: str) -> Document:
        d = self._rows.get(doc_id)
        if d is None or d.tenant_id != self._tenant:
            raise NotFound(doc_id)                         # same answer for "absent" and "other tenant"
        return d
    def list(self) -> list[Document]:
        return [d for d in self._rows.values() if d.tenant_id == self._tenant]


# ---- use case: load through scoped repo, then check the action ----
def delete_document(store: DocumentStore, p: Principal, doc_id: str) -> None:
    doc = store.for_tenant(p.tenant_id).get(doc_id)
    if not can(p, Action.DELETE, doc):
        raise NotFound(doc_id) if not can(p, Action.READ, doc) else Forbidden(doc_id)
    print(f"  deleted {doc_id} by {p.user_id}")


if __name__ == "__main__":
    store = DocumentStore()
    store.put(Document("d1", "acme", "u-ann", "Q3 plan"))
    store.put(Document("d2", "globex", "u-gus", "Globex secrets"))

    ann_viewer = Principal("u-ann", "acme", Role.VIEWER)
    bob_editor = Principal("u-bob", "acme", Role.EDITOR)
    eve_admin_other = Principal("u-eve", "globex", Role.ADMIN)
    cy_admin = Principal("u-cy", "acme", Role.ADMIN)

    for who, doc_id in [(eve_admin_other, "d1"), (bob_editor, "d1"), (cy_admin, "d1")]:
        try:
            delete_document(store, who, doc_id)
        except (NotFound, Forbidden) as e:
            print(f"  {who.user_id} ({who.role.name}, {who.tenant_id}) → {type(e).__name__}")

    # Authorization matrix: the EXPECTED policy written out literally, checked exhaustively.
    # R=read U=update D=delete S=share. A reviewer can read this table; a test enforces it.
    EXPECTED = {
        (Role.VIEWER, "own"): "RUS",  (Role.VIEWER, "same-tenant"): "R",    (Role.VIEWER, "other-tenant"): "",
        (Role.EDITOR, "own"): "RUS",  (Role.EDITOR, "same-tenant"): "RU",   (Role.EDITOR, "other-tenant"): "",
        (Role.ADMIN, "own"): "RUDS",  (Role.ADMIN, "same-tenant"): "RUDS",  (Role.ADMIN, "other-tenant"): "",
    }
    letter = {Action.READ: "R", Action.UPDATE: "U", Action.DELETE: "D", Action.SHARE: "S"}
    cases = 0
    for role, action, relation in product(Role, Action, ["own", "same-tenant", "other-tenant"]):
        p = Principal("u-1", "acme", role)
        doc = Document("x", "globex" if relation == "other-tenant" else "acme",
                       "u-1" if relation == "own" else "u-2", "t")
        want = letter[action] in EXPECTED[(role, relation)]
        assert can(p, action, doc) == want, (role.name, action.name, relation)
        cases += 1
    print("authorization matrix cases verified:", cases)
    print("ALL PASSED")
```

Output:

```
  u-eve (ADMIN, globex) → NotFound
  u-bob (EDITOR, acme) → Forbidden
  deleted d1 by u-cy
authorization matrix cases verified: 36
ALL PASSED
```

The design choices:

| Choice | Why it matters |
|---|---|
| **`Principal` is built only from a verified token** | Handlers can't accidentally authorise based on `body["user_id"]` |
| **Tenant scoping lives in the repository's construction** (`store.for_tenant(t).get(id)`) | There is no `get(id)` that ignores tenancy. A cross-tenant leak requires deliberately bypassing the API, which is visible in review |
| **Policy in one table, deny by default** | Unlisted role or action → denied. Adding a role grants nothing until someone writes the grant |
| **Tenant check before role check in `can`** | An admin of Globex is not an admin of Acme — the most common multi-tenant bug |
| **`NotFound` for resources the caller may not even see** | Returning `403` for another tenant's document confirms it exists (enumeration). `403` only when the caller can see it but not do this action |
| **Load the resource, then authorise** | Object-level checks need the object's owner and tenant (IDOR prevention) |
| **Literal expected-policy table in a test** | A reviewer reads the table; the test enforces every role × action × relationship. A policy change that isn't reflected in the table fails CI |

Beyond the example:

- **Database-level enforcement** as defence in depth: PostgreSQL Row-Level Security with
  `SET app.tenant_id` per transaction makes a forgotten `WHERE tenant_id` return nothing
  instead of everything.
- **Centralise decisions for complex policies** — a policy engine (OPA/Rego, Cedar, Google
  Zanzibar-style relationship checks such as SpiceDB/OpenFGA) — but keep enforcement calls at
  every use case.
- **Authorise bulk and list operations per item** or with a scoped query; "can list
  documents" doesn't mean "can list every document".
- **Mass assignment:** never copy request JSON directly onto a model
  (`user.update(**body)`), or a client sends `{"role": "admin"}`. Parse into a command DTO
  that contains only the fields the caller may set.
- **Re-check on sensitive actions** (password change, payout destination, deleting an
  account): require recent authentication.

---

## 4 · Secrets, randomness, passwords, and tokens

```python
# Secrets, randomness, password hashing, and signed tokens — using the standard library correctly.
import base64
import hashlib
import hmac
import json
import random
import secrets
import time


# ---- 1. Randomness: `random` is predictable; `secrets` is not ----
r = random.Random(1234)                                 # an attacker who sees outputs can recover state
print("random  token:", "%032x" % r.getrandbits(128))
print("secrets token:", secrets.token_urlsafe(32))      # CSPRNG: session IDs, reset links, API keys


# ---- 2. Passwords: slow, salted, memory-hard KDF; never a plain fast hash ----
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    n, r_, p = 2**14, 8, 1
    dk = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r_, p=p, dklen=32)
    return f"scrypt${n}${r_}${p}${salt.hex()}${dk.hex()}"   # parameters stored → can be raised later

def verify_password(password: str, stored: str) -> bool:
    _, n, r_, p, salt, expected = stored.split("$")
    dk = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r_), p=int(p), dklen=32)
    return hmac.compare_digest(dk.hex(), expected)          # constant-time comparison

stored = hash_password("correct horse battery staple")
t = time.perf_counter(); ok = verify_password("correct horse battery staple", stored); slow = time.perf_counter() - t
t = time.perf_counter(); hashlib.sha256(b"x").digest(); fast = time.perf_counter() - t
print(f"scrypt verify {slow * 1000:.1f} ms vs sha256 {fast * 1e6:.1f} µs  → ~{slow / fast:,.0f}x more work per guess")
assert ok and not verify_password("Tr0ub4dor&3", stored)
assert hash_password("same") != hash_password("same")        # salt: identical passwords differ


# ---- 3. Signed, expiring tokens (HMAC) ----
SIGNING_KEY = secrets.token_bytes(32)                       # from a secret manager in production

def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def sign(claims: dict, ttl_s: int, now: float) -> str:
    body = _b64(json.dumps({**claims, "exp": int(now + ttl_s)}, sort_keys=True).encode())
    mac = hmac.new(SIGNING_KEY, body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64(mac)}"

class InvalidToken(Exception): ...

def verify(token: str, now: float) -> dict:
    try:
        body, mac = token.split(".")
    except ValueError:
        raise InvalidToken("malformed") from None
    expected = hmac.new(SIGNING_KEY, body.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _unb64(mac)):      # verify BEFORE parsing/trusting the body
        raise InvalidToken("bad signature")
    claims = json.loads(_unb64(body))
    if now >= claims["exp"]:
        raise InvalidToken("expired")
    return claims

now = 1_800_000_000
tok = sign({"sub": "u-17", "scope": "read"}, ttl_s=900, now=now)
print("claims:", verify(tok, now + 60))

body, mac = tok.split(".")
forged_body = _b64(json.dumps({"sub": "u-17", "scope": "admin", "exp": now + 900}, sort_keys=True).encode())
for label, candidate, at in [("tampered", f"{forged_body}.{mac}", now + 60),
                             ("expired", tok, now + 901),
                             ("garbage", "not-a-token", now)]:
    try:
        verify(candidate, at)
        raise AssertionError(label)
    except InvalidToken as e:
        print(f"{label:<9} → rejected: {e}")
print("ALL PASSED")
```

Output (tokens are random; timings vary):

```
random  token: 1de9ea6670d3da1fc735df5ef7697fb9
secrets token: EUvH2jZCQvJcNBSsWqlI6efpFzERc-YhmDmGanpNm9Y
scrypt verify 18.3 ms vs sha256 6.5 µs  → ~2,802x more work per guess
claims: {'exp': 1800000900, 'scope': 'read', 'sub': 'u-17'}
tampered  → rejected: bad signature
expired   → rejected: expired
garbage   → rejected: malformed
ALL PASSED
```

Note that the `random` token prints **the same value every run** — seeded generators are
reproducible, and Python's Mersenne Twister state can be reconstructed from 624 observed
32-bit outputs. That is fine for simulations, fatal for session IDs.

### Rules

| Need | Use | Never |
|---|---|---|
| Session IDs, reset tokens, API keys, nonces | `secrets.token_urlsafe(32)`, Go `crypto/rand` | `random`, `math/rand`, UUIDv1, timestamps, incrementing IDs |
| Store passwords | `argon2id` (via `argon2-cffi`), `scrypt`, or `bcrypt`, with per-password salt and stored parameters | MD5/SHA-1/SHA-256 (fast hashes, even salted), reversible encryption |
| Compare secrets, MACs, tokens | `hmac.compare_digest`, Go `subtle.ConstantTimeCompare` | `==`, which can return early at the first differing byte and leak timing |
| Integrity of data you issue (tokens, signed URLs, cookies) | HMAC-SHA-256 with a server-held key, or a vetted library (`itsdangerous`, a JWT library with algorithm allowlisting) | Plain hashes (`sha256(key + data)` is vulnerable to length extension), unsigned base64 |
| Encrypt data | AEAD: AES-GCM or ChaCha20-Poly1305 via `cryptography`, Go `crypto/cipher` | Designing your own scheme; ECB mode; encryption without authentication |
| Store secrets | Secret manager / workload identity, injected at runtime | Source code, config files in the repo, container images, environment dumps in logs |

### Token verification order matters

In `verify`: **check the signature first, then parse, then check expiry and claims.**
Parsing attacker-controlled data before authenticating it exposes the parser; checking
claims before the signature trusts forged claims. For JWTs specifically
(`SystemDesign/building_blocks/14`): pin the algorithm, check `iss`/`aud`/`exp`, and reject
`alg: none`.

### Designing APIs that handle secrets

- **Give secrets their own type** whose `__repr__`/`String()` redacts (`10` §9), so they
  can't be logged or included in exceptions by accident.
- **Make keys rotatable from day one:** tokens carry a key ID (`kid`); verification accepts
  current and previous keys; signing uses only the current key.
- **Scope and expire everything:** a token for "read invoices for 15 minutes" limits the
  blast radius of a leak far more than a permanent all-access key.
- **Don't reinvent crypto protocols.** The example's HMAC token is fine for learning and for
  simple internal use; for anything user-facing, use a maintained library.

---

## 5 · Server-side request forgery (SSRF)

Any feature where **the server fetches a URL a user supplied** — link previews, webhooks,
"import from URL", image proxies, PDF renderers — lets an attacker make requests *from
inside your network*: to the cloud metadata service (instance credentials), admin panels
on `localhost`, internal databases, or other tenants' services.

A first, naive attempt at a check — checking the URL's *text*:

```python
from urllib.parse import urlsplit

BLOCKED_HOSTS = {"localhost", "127.0.0.1", "169.254.169.254"}


def looks_safe(url: str) -> bool:
    host = urlsplit(url).hostname
    return url.startswith("https://") and host not in BLOCKED_HOSTS


for url in ["https://example.com/cat.png", "https://169.254.169.254/", "http://example.com/cat.png"]:
    print(url, "->", "ALLOW" if looks_safe(url) else "BLOCK")
```

Output:

```
https://example.com/cat.png -> ALLOW
https://169.254.169.254/ -> BLOCK
http://example.com/cat.png -> BLOCK
```

That looks reasonable and is exactly what real SSRF filters get bypassed through: the
denylist checks the *hostname string*, not where it actually resolves. A domain the
attacker controls can point at `169.254.169.254` and never appear in `BLOCKED_HOSTS`;
the same address is spellable as `2130706433` or `[::ffff:127.0.0.1]`; and a DNS answer
can change between the check and the connect. The full example below fixes all of that
by checking the **resolved** address against an allowlist of "public", not a denylist of
hostnames.

```python
# SSRF: the server fetches a URL the user supplied. Validate scheme, host, and the RESOLVED address.
import ipaddress
import socket
from urllib.parse import urlsplit


class BlockedURL(Exception): ...


ALLOWED_SCHEMES = {"https"}
ALLOWED_PORTS = {443}


def resolve_all(host: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    return [ipaddress.ip_address(info[4][0].split("%")[0]) for info in infos]


def check_outbound_url(url: str, resolver=resolve_all) -> tuple[str, list]:
    parts = urlsplit(url)
    if parts.scheme not in ALLOWED_SCHEMES:
        raise BlockedURL(f"scheme {parts.scheme!r} not allowed")
    if parts.username or parts.password:
        raise BlockedURL("credentials in URL not allowed")
    host = parts.hostname
    if not host:
        raise BlockedURL("missing host")
    if (parts.port or 443) not in ALLOWED_PORTS:
        raise BlockedURL(f"port {parts.port} not allowed")
    addresses = resolver(host)
    for ip in addresses:
        if not ip.is_global or ip.is_multicast:          # allowlist "public", don't denylist ranges
            raise BlockedURL(f"{host} resolves to non-public address {ip}")
    # Connect to one of THESE addresses (pin them); re-resolving later allows DNS rebinding.
    return host, addresses


if __name__ == "__main__":
    fake_dns = {
        "images.example.com": ["93.184.215.14"],
        "metadata.attacker.test": ["169.254.169.254"],      # cloud metadata endpoint
        "rebind.attacker.test": ["93.184.215.14", "10.0.0.5"],
    }
    def resolver(host):
        try:
            return [ipaddress.ip_address(a) for a in fake_dns[host]]
        except KeyError:
            return resolve_all(host)                        # real resolution for literals / localhost

    cases = [
        "https://images.example.com/cat.png",
        "http://images.example.com/cat.png",
        "file:///etc/passwd",
        "https://metadata.attacker.test/latest/meta-data/iam/",
        "https://rebind.attacker.test/x",
        "https://127.0.0.1/admin",
        "https://[::1]/admin",
        "https://2130706433/admin",                          # 127.0.0.1 written as an integer
        "https://[::ffff:127.0.0.1]/admin",                  # IPv4-mapped IPv6 loopback
        "https://user:pw@images.example.com/",
        "https://images.example.com:22/",
    ]
    allowed = []
    for url in cases:
        try:
            check_outbound_url(url, resolver)
            print(f"ALLOW  {url}")
            allowed.append(url)
        except (BlockedURL, OSError) as e:
            print(f"BLOCK  {url:<55} {e}")
    assert allowed == ["https://images.example.com/cat.png"]
    print("ALL PASSED")
```

Output:

```
ALLOW  https://images.example.com/cat.png
BLOCK  http://images.example.com/cat.png                       scheme 'http' not allowed
BLOCK  file:///etc/passwd                                      scheme 'file' not allowed
BLOCK  https://metadata.attacker.test/latest/meta-data/iam/    metadata.attacker.test resolves to non-public address 169.254.169.254
BLOCK  https://rebind.attacker.test/x                          rebind.attacker.test resolves to non-public address 10.0.0.5
BLOCK  https://127.0.0.1/admin                                 127.0.0.1 resolves to non-public address 127.0.0.1
BLOCK  https://[::1]/admin                                     ::1 resolves to non-public address ::1
BLOCK  https://2130706433/admin                                2130706433 resolves to non-public address 127.0.0.1
BLOCK  https://[::ffff:127.0.0.1]/admin                        ::ffff:127.0.0.1 resolves to non-public address ::ffff:127.0.0.1
BLOCK  https://user:pw@images.example.com/                     credentials in URL not allowed
BLOCK  https://images.example.com:22/                          port 22 not allowed
ALL PASSED
```

Why each part of the design is necessary:

- **Check the resolved IP, not the hostname string.** Attackers own domains that resolve to
  `169.254.169.254`, and IPs have many spellings (`2130706433`, `0x7f.1`, `[::ffff:127.0.0.1]`).
  String denylists always miss one.
- **Allowlist "public" (`is_global`) rather than denylisting private ranges.** New special
  ranges appear; an allowlist fails closed.
- **Check every resolved address.** A name with one public and one private A record passes a
  check that looks only at the first.
- **Pin the checked address for the connection.** If the HTTP client re-resolves the name, a
  **DNS rebinding** attacker returns a public IP to the check and a private IP to the
  connect. Connect to the validated IP (with the original `Host` header / SNI), or route
  through an egress proxy that enforces the policy at connect time.
- **Re-validate redirects** — or disable them. A public URL that 302-redirects to
  `http://169.254.169.254/` bypasses a check done only on the first URL.
- **Defence in depth at the network layer:** run URL-fetching workers in an isolated
  network segment with no route to internal services; require IMDSv2 (session tokens) on
  AWS so a simple GET can't read instance credentials.
- **Prefer allowlists of destinations** when the feature allows it (webhooks to verified
  domains, imports from known providers).

---

## 6 · Resource exhaustion as a security bug

Availability is part of security. Any input whose processing cost is unbounded lets one
cheap request consume large amounts of memory or CPU.

The general shape, minimal — reject before doing the work, not after:

```python
def parse_ids(raw: str, max_items: int = 100) -> list[int]:
    items = raw.split(",")
    if len(items) > max_items:
        raise ValueError(f"too many items: {len(items)} > {max_items}")
    return [int(x) for x in items]


print(parse_ids("1,2,3"))
try:
    parse_ids(",".join(str(i) for i in range(1000)))
except ValueError as e:
    print("rejected:", e)
```

Output:

```
[1, 2, 3]
rejected: too many items: 1000 > 100
```

The check runs before `int(x)` is called on a single item — cheap. The three cases
below are the same principle applied where "cheap" is less obvious: a byte stream whose
declared length you can't trust, a compressed archive that expands far past what it
looked like on the wire, and a regex whose *time*, not its input size, is unbounded.

```python
# Resource exhaustion: every input needs a size bound, and some algorithms need an input bound too.
import io
import re
import time
import zipfile


# ---- 1. Bounded reads ----
class TooLarge(Exception): ...

def read_bounded(stream: io.BufferedIOBase, limit: int) -> bytes:
    data = stream.read(limit + 1)                           # read at most one byte past the limit
    if len(data) > limit:
        raise TooLarge(f"body exceeds {limit} bytes")
    return data

try:
    read_bounded(io.BytesIO(b"x" * 5_000_000), limit=1_000_000)
except TooLarge as e:
    print("rejected:", e)


# ---- 2. Decompression bombs: trust neither the compressed size nor the declared size ----
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("zeros.bin", b"\0" * 200_000_000)            # 200 MB of zeros
print(f"archive on the wire: {buf.tell() / 1024:.0f} KB")

def extract_bounded(archive: bytes, max_total: int, max_files: int = 1_000) -> dict[str, bytes]:
    out, total = {}, 0
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        infos = z.infolist()
        if len(infos) > max_files:
            raise TooLarge("too many files")
        for info in infos:
            with z.open(info) as f:
                chunks = []
                while chunk := f.read(64_000):              # count ACTUAL bytes produced
                    total += len(chunk)
                    if total > max_total:
                        raise TooLarge(f"decompressed size exceeds {max_total} bytes")
                    chunks.append(chunk)
                out[info.filename] = b"".join(chunks)
    return out

try:
    extract_bounded(buf.getvalue(), max_total=10_000_000)
except TooLarge as e:
    print("rejected:", e)


# ---- 3. ReDoS: catastrophic backtracking on attacker-controlled input ----
evil = re.compile(r"^(a+)+$")                                # nested quantifier
safe = re.compile(r"^a+$")                                   # same language, linear
times = []
for n in (16, 18, 20):
    s = "a" * n + "!"
    t = time.perf_counter(); evil.match(s); te = time.perf_counter() - t
    t = time.perf_counter(); safe.match(s); ts = time.perf_counter() - t
    times.append(te)
    print(f"n={n}: nested {te * 1000:7.1f} ms   linear {ts * 1e6:5.1f} µs")
assert times[2] > 2 * times[0]                              # grows exponentially: ~2x per extra char
print("ALL PASSED")
```

Output:

```
rejected: body exceeds 1000000 bytes
archive on the wire: 190 KB
rejected: decompressed size exceeds 10000000 bytes
n=16: nested     1.4 ms   linear   0.8 µs
n=18: nested     5.4 ms   linear   1.1 µs
n=20: nested    22.0 ms   linear   1.6 µs
ALL PASSED
```

A 190 KB upload expands to 200 MB; each extra character of input doubles the nested regex's
time — at n = 40 that is hours of CPU from a 41-byte string.

| Input | Bound |
|---|---|
| Request bodies, uploads | Max size at the proxy **and** in the app; streaming reads with a limit |
| Archives, compressed bodies (`Content-Encoding: gzip`) | Count decompressed bytes as they are produced; limit file count and nesting |
| JSON / XML | Max size, max depth, max array length; disable XML external entities and DTDs (`defusedxml`) |
| Collections in requests (IDs, batch items) | Max items per request (`11` §3) |
| Pagination | Max page size, server-enforced |
| Regex on user input | No nested quantifiers; length limits; a linear-time engine (RE2 / `google-re2`, Go `regexp`) |
| Expensive operations (password hashing, report generation, search) | Rate limits per identity and per IP; queues with bounded depth |
| Images | Check pixel dimensions before decoding (a small PNG can declare 50,000 × 50,000 pixels) |
| Anything that fans out (webhooks, emails, invitations) | Per-account quotas |
| Time | Timeouts on every request and outbound call (`06` §6) |

The general design rule: **the cost of processing a request should be bounded by a
limit you chose, not by what the client sent.**

---

## 7 · Output encoding and cross-site scripting

XSS is injection into HTML/JavaScript: user data rendered into a page is parsed as markup
or script in *another user's* browser, where it runs with that user's session.

The correct escaping **depends on the output context**:

| Context | Example | Escaping needed |
|---|---|---|
| HTML body | `<p>{name}</p>` | HTML entities: `<` → `&lt;` |
| HTML attribute | `<input value="{name}">` | Attribute encoding, always quoted |
| URL in `href`/`src` | `<a href="{url}">` | Scheme allowlist (`https:`), then URL encoding — `javascript:` URLs execute |
| Inside `<script>` | `var user = {name};` | JavaScript string encoding (JSON with `<`, `>`, `&` escaped) |
| CSS | `style="color: {c}"` | Avoid; allowlist values |

That's why "sanitise input" is the wrong mental model — the same string needs different
treatment in each context, and the context is only known at output time.

The HTML-body row of that table, concretely:

```python
import html


def render_comment_unsafe(name: str) -> str:
    return f"<p>Comment by {name}</p>"


def render_comment_safe(name: str) -> str:
    return f"<p>Comment by {html.escape(name)}</p>"


attacker_name = "<script>alert(document.cookie)</script>"
print("unsafe:", render_comment_unsafe(attacker_name))
print("safe:  ", render_comment_safe(attacker_name))
assert "<script>" not in render_comment_safe(attacker_name)
print("ALL PASSED")
```

Output:

```
unsafe: <p>Comment by <script>alert(document.cookie)</script></p>
safe:   <p>Comment by &lt;script&gt;alert(document.cookie)&lt;/script&gt;</p>
ALL PASSED
```

The unsafe version hands the browser a real `<script>` tag; the safe version hands it
the literal text `<script>`, rendered as visible characters instead of parsed as markup.
`html.escape` covers the HTML-body context only — the attribute, URL, and `<script>`-body
rows in the table above each need their own encoding, which is exactly why a hand-rolled
`html.escape()` call at every output site doesn't scale and an auto-escaping template
that picks the right encoding for each context (below) does.

Design defences:

1. **Auto-escaping, context-aware templates** — Jinja2 with `autoescape=True`, Django
   templates, React/Vue/Angular's default text binding, Go `html/template` (§10). The
   insecure path (`|safe`, `Markup()`, `dangerouslySetInnerHTML`, `v-html`) is then
   explicit, greppable, and reviewable.
2. **Never build HTML with string concatenation or f-strings.**
3. **If users submit rich HTML** (comments with formatting), sanitise with an allowlist
   library (`nh3`/`bleach`, DOMPurify), never a regex.
4. **Content Security Policy** as defence in depth: `script-src 'self'` with nonces blocks
   injected inline scripts even if escaping fails somewhere.
5. **Cookies:** `HttpOnly` (scripts can't read session cookies), `Secure`, `SameSite=Lax` or
   `Strict` (also the primary CSRF defence, together with CSRF tokens for state-changing
   form posts).
6. **JSON APIs:** serve with `Content-Type: application/json` and `X-Content-Type-Options:
   nosniff` so responses can't be interpreted as HTML.

---

## 8 · Race conditions with security impact

Concurrency bugs (`07`) become security bugs when the invariant being raced is a limit or a
permission.

| Race | Exploit | Fix |
|---|---|---|
| **Check-then-act on a balance or quota** | Send 50 parallel withdrawals or coupon redemptions; each sees the old balance | Atomic conditional update: `UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?` and check the row count |
| **One-time token reuse** | Submit a password-reset or invite token twice in parallel | Consume atomically: `DELETE … WHERE token = ? RETURNING …`, or a unique constraint on "used" |
| **TOCTOU on files** | Swap a checked file for a symlink before it's opened | Open first, then check the opened handle (`fstat`); `openat`/`os.Root`; `O_NOFOLLOW` |
| **Permission revoked mid-operation** | A long export continues after the user's access is removed | Re-check authorisation at commit; short-lived credentials |
| **Signup uniqueness** | Two parallel signups with the same email both pass "email not taken" | Unique index on the normalised email; handle the constraint violation |
| **Limit enforcement across instances** | Per-process rate limiter; attacker spreads requests across 20 instances | Shared store (Redis) with atomic operations, or limit at the gateway |

The rule from `07` §4 applies with higher stakes: **make the check and the act one
atomic operation — ideally in the database, which already knows how.**

---

## 9 · Secure defaults and failing closed

Libraries and services should be secure when used naively. Every opt-in security feature
is a feature someone forgets to opt into.

| Insecure default | Secure default |
|---|---|
| `verify=False` option commonly copied from Stack Overflow | TLS verification always on; a custom CA bundle option instead of a disable switch |
| New endpoints public unless decorated `@requires_auth` | Every route requires authentication unless explicitly decorated `@public` |
| Roles grant access unless denied | Deny unless granted (§3) |
| Debug mode, stack traces, admin consoles enabled by default | Off unless an explicit development profile is selected |
| CORS `*` with credentials | Explicit origin allowlist |
| Cookies without flags | `HttpOnly; Secure; SameSite=Lax` from the framework config |
| Storage buckets created world-readable | Private; public access requires a separate, audited action |
| Service binds `0.0.0.0` in development containers | `127.0.0.1` unless configured |

**Fail closed:** when a security control errors, deny.

```python
def is_allowed(principal, action, resource) -> bool:
    try:
        return policy_client.check(principal, action, resource, timeout_s=0.2)
    except Exception:
        metrics.inc("authz_check_errors_total")
        return False          # policy service down → deny, not allow
```

Contrast with degrading non-essential features (`06` §10), where failing *open* is right: a
recommendations outage should show bestsellers. Decide per control and write down why —
fail-closed controls need their own availability engineering (caching recent decisions,
local policy evaluation), because they turn dependency outages into user-facing errors.

**Error messages:** don't reveal whether an account exists ("email not found" vs. "wrong
password" lets attackers enumerate users); don't return stack traces, SQL errors, or
internal hostnames (`06` §4).

---

## 10 · The same ideas in Go

Go's standard library puts several secure-by-default designs within reach: contextual
auto-escaping templates, traversal-resistant file access (`os.Root`, Go 1.24), a
cryptographically secure `crypto/rand`, constant-time comparison, and a linear-time
`regexp` engine that cannot suffer catastrophic backtracking.

```go
package main

import (
	"crypto/rand"
	"crypto/subtle"
	"encoding/base64"
	"fmt"
	"html/template"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	// ---- 1. Contextual auto-escaping: html/template, never text/template for HTML ----
	page := template.Must(template.New("p").Parse(
		`<p>Hello, {{.Name}}</p><a href="{{.Site}}">site</a><script>var user = {{.Name}};</script>` + "\n"))
	_ = page.Execute(os.Stdout, map[string]string{
		"Name": `</script><script>alert(1)</script>`,
		"Site": `javascript:alert(document.cookie)`,
	})

	// ---- 2. Traversal-resistant file access: os.Root (Go 1.24) ----
	dir, _ := os.MkdirTemp("", "uploads")
	defer os.RemoveAll(dir)
	uploads := filepath.Join(dir, "uploads")
	_ = os.Mkdir(uploads, 0o755)
	_ = os.WriteFile(filepath.Join(uploads, "invoice.pdf"), []byte("ok"), 0o644)
	_ = os.WriteFile(filepath.Join(dir, "secret.env"), []byte("DB_PASSWORD=hunter2"), 0o600)
	_ = os.Symlink(filepath.Join(dir, "secret.env"), filepath.Join(uploads, "link.pdf"))

	root, err := os.OpenRoot(uploads)
	if err != nil {
		panic(err)
	}
	defer root.Close()
	for _, name := range []string{"invoice.pdf", "../secret.env", "link.pdf"} {
		f, err := root.Open(name) // every path component is resolved inside the root, symlinks included
		if err != nil {
			fmt.Printf("root.Open(%-15q) blocked: %v\n", name, err)
			continue
		}
		b := make([]byte, 64)
		n, _ := f.Read(b)
		f.Close()
		fmt.Printf("root.Open(%-15q) ok: %s\n", name, b[:n])
	}

	// ---- 3. Secrets: crypto/rand for tokens, constant-time comparison ----
	tok := make([]byte, 32)
	_, _ = rand.Read(tok)
	apiKey := base64.RawURLEncoding.EncodeToString(tok)
	check := func(presented string) bool {
		return subtle.ConstantTimeCompare([]byte(presented), []byte(apiKey)) == 1
	}
	fmt.Println("valid key:", check(apiKey), "| wrong key:", check(strings.Repeat("A", len(apiKey))))
}
```

Output:

```
<p>Hello, &lt;/script&gt;&lt;script&gt;alert(1)&lt;/script&gt;</p><a href="#ZgotmplZ">site</a><script>var user = "</script><script>alert(1)</script>";</script>
root.Open("invoice.pdf"  ) ok: ok
root.Open("../secret.env") blocked: openat ../secret.env: path escapes from parent
root.Open("link.pdf"     ) blocked: openat link.pdf: path escapes from parent
valid key: true | wrong key: false
```

What happened:

- **One template value, three encodings:** HTML-escaped in the body, replaced with the
  safe placeholder `#ZgotmplZ` in `href` because `javascript:` is an unsafe URL scheme, and
  JavaScript-string-encoded inside `<script>`. `text/template` would have emitted all three
  raw — same API, very different safety; `gosec` and code review should flag
  `text/template` producing HTML.
- **`os.Root`** blocks both `../` traversal and a **symlink** pointing outside the
  directory, with no separate check-then-open gap.
- **`subtle.ConstantTimeCompare`** for API keys; `crypto/rand` for key material. (`math/rand`
  is for simulations only.)
- Go's `database/sql` placeholders (`db.QueryContext(ctx, "… WHERE id = $1", id)`) and
  `exec.Command(name, args...)` (no shell) follow the same rules as §2.
- Run **`govulncheck`** (reports only vulnerabilities in code paths you actually call) and
  **`gosec`** in CI.

---

## 11 · Dependencies and the supply chain

Most code in a service is third-party. Supply-chain attacks (typosquatted packages,
compromised maintainer accounts, malicious updates, build-system compromise) target that.

| Practice | How |
|---|---|
| **Pin exact versions with hashes** | `uv lock` / `pip-tools --generate-hashes`; `go.sum` (checked automatically) |
| **Scan for known vulnerabilities** | `pip-audit`, `govulncheck`, Dependabot/Renovate, OSV-Scanner |
| **Minimise dependencies** | "A little copying is better than a little dependency" (`01` §14) — especially for trivial helpers |
| **Review new dependencies** | Maintainer activity, download counts vs. name similarity (typosquats), install scripts, permissions it needs; OpenSSF Scorecard |
| **Verify provenance** | Sigstore signatures, SLSA build provenance, PyPI Trusted Publishing |
| **Private registry / proxy** | Mirror approved packages; prevents dependency confusion (a public package with your internal package's name) |
| **Least-privilege CI** | Build jobs without production credentials; pinned CI actions by commit SHA; secrets scoped per job |
| **SBOM** | Generate a software bill of materials so "are we affected by CVE-X?" is a query, not an investigation |
| **Secret scanning** | Pre-commit hooks and repository scanning (gitleaks, GitHub secret scanning); rotate anything that leaked — deleting the commit is not enough |

---

## 12 · Threat modeling in a design review

A threat model is a structured way to ask "how could this be abused?" before building. It
belongs in the design doc's cross-cutting section (`13`).

**Four questions** (Adam Shostack):

1. What are we building? (a data-flow diagram with trust boundaries marked)
2. What can go wrong?
3. What are we going to do about it?
4. Did we do a good job?

**STRIDE** as a prompt list for question 2, applied to each element crossing a boundary:

| Threat | Violates | Example question for a "share document by link" feature |
|---|---|---|
| **S**poofing | Authentication | Can someone use a link without being the intended recipient? |
| **T**ampering | Integrity | Can the link's permission level be edited in the URL? |
| **R**epudiation | Non-repudiation | Can we prove who created and used a link? (audit log) |
| **I**nformation disclosure | Confidentiality | Are link IDs guessable? Do they leak via `Referer` headers or logs? |
| **D**enial of service | Availability | Can someone generate millions of links? |
| **E**levation of privilege | Authorization | Can a viewer create an editor link? |

Resulting design decisions for that feature: 128-bit random link tokens (`secrets`), the
permission stored server-side (not in the URL), links scoped to one document with expiry and
revocation, creator limited to their own permission level, `Referrer-Policy: no-referrer`,
link tokens redacted in access logs, audit events on creation and use, per-user rate limit on
link creation.

---

## 13 · Testing security properties

| Test | Catches | Example |
|---|---|---|
| **Authorization matrix tests** | Missing or wrong access checks | §3: every role × action × relationship, including cross-tenant |
| **Negative tests for every endpoint** | Endpoints added without auth | A test that enumerates all routes and asserts each returns 401 without credentials, unless on an explicit public allowlist |
| **Injection payload tests** | Concatenation regressions | Quotes, `;`, `../`, `$(…)`, `<script>` through each input; assert no behaviour change |
| **Canary secrets** | Secrets in logs/responses/errors | `10` §11 |
| **Fuzzing parsers** | Crashes, hangs, memory blow-ups on malformed input | Atheris / Hypothesis (Python), `go test -fuzz` |
| **Limits tests** | Missing bounds | Oversized body, deeply nested JSON, zip bomb, 10,000-item batch → rejected quickly |
| **Race tests on limits** | Double-spend, token reuse | Fire 50 concurrent redemptions; assert exactly one succeeds |
| **SAST in CI** | Known-bad patterns | Bandit, Semgrep, CodeQL, gosec |
| **Dependency scanning** | Known CVEs | `pip-audit`, `govulncheck` |
| **DAST / penetration tests** | Deployed misconfiguration | OWASP ZAP in staging; external pentests for major launches |

```python
PUBLIC_ROUTES = {("GET", "/healthz"), ("POST", "/login"), ("GET", "/docs")}

def test_every_route_requires_authentication(client, app):
    for route in app.routes:
        for method in route.methods:
            if (method, route.path) in PUBLIC_ROUTES:
                continue
            response = client.request(method, route.path.replace("{id}", "x"))
            assert response.status_code == 401, f"{method} {route.path} is reachable anonymously"
```

A new endpoint without authentication fails this test by default — the secure default
again, enforced in CI.

---

## 14 · Red flags

| Red flag | Vulnerability | Fix |
|---|---|---|
| f-string / `+` / `%` building SQL | SQL injection | Placeholders; identifier allowlists |
| `shell=True`, `os.system`, `sh -c` with variables | Command injection | argv lists |
| `open(base + user_path)` | Path traversal | Generated names; containment check; `os.Root` |
| `requests.get(user_url)` | SSRF | §5 validation, pinned IPs, isolated egress |
| `user_id` / `tenant_id` / `role` read from the request body or a plain header | Broken authentication / authorization | Principal from verified credentials |
| `repo.get(id)` with no tenant or owner check | IDOR, cross-tenant leak | Scoped repositories; load-then-authorise |
| `model.update(**request.json)` | Mass assignment | Explicit command DTOs |
| `random` / `math/rand` for tokens | Predictable tokens | `secrets` / `crypto/rand` |
| `sha256(password)` or `md5` | Fast offline cracking | argon2id / scrypt / bcrypt |
| `token == expected` | Timing leak | Constant-time compare |
| Hand-rolled crypto, ECB, unauthenticated encryption | Broken confidentiality/integrity | AEAD via a vetted library |
| Secrets in repo, image, or logs | Credential theft | Secret manager; redacting types; scanning |
| `verify=False`, `InsecureSkipVerify: true` | Man-in-the-middle | Fix the CA configuration instead |
| No request/upload/decompression limits | DoS | Bounds everywhere (§6) |
| Nested regex quantifiers on user input | ReDoS | Linear regex engine; input limits |
| `\|safe`, `Markup`, `dangerouslySetInnerHTML`, `text/template` for HTML | XSS | Auto-escaping; allowlist sanitiser |
| Check-then-act on balances, quotas, one-time tokens | Race exploits | Atomic conditional updates |
| Authz check that fails open on errors | Bypass during outages | Fail closed for security controls |
| Different errors for "no such user" and "wrong password" | Account enumeration | Uniform responses |
| `pickle.loads` / `yaml.load` on external data | Remote code execution | Schema-based formats |

---

## 15 · Interview questions and model answers

**Q: How do you prevent SQL injection?**
Never build queries by string concatenation with user data. Use parameterised queries for
values; for identifiers such as sort columns, map user input through an allowlist. Keep
repository interfaces typed so no SQL fragments cross them, and enforce it with a linter like
Bandit or Semgrep in CI. Database accounts with least privilege limit the damage if something
slips through.

**Q: What's an IDOR and how do you design against it?**
Insecure direct object reference: the API returns or modifies an object by ID without checking
that the caller may access that specific object. Design against it by deriving the principal
from verified credentials, loading resources through repositories scoped to the caller's tenant,
authorising each action on the loaded object with a deny-by-default policy, returning 404 for
objects the caller can't see, and testing a full role × action × relationship matrix — plus
row-level security in the database as defence in depth.

**Q: How should passwords be stored?**
With a slow, salted, memory-hard password hashing function — argon2id, scrypt, or bcrypt —
storing the salt and parameters with the hash so they can be raised later, and verifying with a
constant-time comparison. Never a fast hash like SHA-256, even salted, because GPUs try billions
of those per second.

**Q: A feature fetches a user-supplied URL. What are the risks?**
SSRF: the server can be steered to internal services, localhost admin endpoints, or the cloud
metadata service to steal credentials. Mitigate with a scheme and port allowlist, resolving the
host and requiring every address to be public, connecting to the validated address to defeat DNS
rebinding, re-validating or disabling redirects, size and time limits on the response, and running
fetchers in a network segment with no internal access.

**Q: Input validation or output encoding?**
Both, for different reasons. Validation at the entry boundary rejects data that doesn't fit the
domain — types, ranges, sizes. Encoding at the output boundary makes data inert for a specific
interpreter — SQL parameters, argv arrays, context-aware HTML escaping. Validation can't replace
encoding, because a perfectly valid name like `O'Brien` or `<3` still breaks a concatenated query or
page.

**Q: What does "fail closed" mean and when would you not do it?**
When a security control can't reach a decision — the policy service is down — deny rather than
allow. It's right for authentication, authorisation, and fraud checks. For non-security features
like recommendations, failing open or degrading is right. Fail-closed controls then need their own
reliability work, like caching recent decisions or evaluating policy locally.

**Q: How do you make a codebase secure when you can't review every line?**
Make the secure path the default and the insecure path conspicuous: typed repository APIs,
auto-escaping templates, authentication required on every route unless explicitly marked public,
deny-by-default policies, secret types that redact themselves. Enforce with linters and tests that
fail CI — route-auth tests, authorization matrices, dependency scanning — and do threat modeling in
design reviews for high-risk features.

---

## 16 · Checklist

**Boundaries and input**
- [ ] Trust boundaries are identified; "internal" inputs are treated as untrusted.
- [ ] Every input has type, range, size, and count limits enforced server-side.
- [ ] Parsers are bounded (depth, decompressed size, dimensions); XML entities disabled.
- [ ] Regexes on user input are linear-time or length-limited.

**Injection and output**
- [ ] SQL uses placeholders; identifiers come from allowlists.
- [ ] Processes are started with argv lists, no shell.
- [ ] File paths are generated, or contained with traversal-resistant APIs.
- [ ] HTML is rendered through context-aware auto-escaping; raw-HTML escapes are rare and reviewed.
- [ ] Outbound fetches of user URLs are validated against resolved, pinned, public addresses.

**Access control**
- [ ] The principal comes only from verified credentials.
- [ ] Repositories are tenant-scoped by construction; resources are loaded, then authorised.
- [ ] Policy is deny-by-default and covered by an exhaustive matrix test.
- [ ] Every route requires auth unless on an explicit public allowlist, enforced by a test.
- [ ] Security controls fail closed.

**Secrets and crypto**
- [ ] Tokens from a CSPRNG; secrets compared in constant time.
- [ ] Passwords hashed with argon2id/scrypt/bcrypt and stored parameters.
- [ ] No hand-rolled crypto; AEAD via vetted libraries; keys rotatable with key IDs.
- [ ] Secrets come from a secret manager and have redacting types.

**Process**
- [ ] Limits, balances, and one-time tokens are enforced atomically.
- [ ] Dependencies are pinned, scanned, and minimised; CI has least privilege.
- [ ] High-risk features get a STRIDE threat model in the design doc.
- [ ] SAST, dependency scanning, fuzzing, and negative tests run in CI.
