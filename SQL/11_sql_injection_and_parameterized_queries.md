# <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> Injection and Parameterized Queries

This is a security-critical lesson. The exploit below is run for real, against the
live lab database, so the failure is something you see happen — not something you
take on faith.

## The mental model

<abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> injection happens when untrusted input is spliced directly into a <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> string
instead of being passed as data separate from the query's structure. The database
has no way to tell "a value the user typed" from "a fragment of <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> syntax" once
they've been concatenated into the same string — from the database's point of view,
it's all just <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> it was asked to run. A **parameterized query** fixes this at the
protocol level: the <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> text and the values are sent to the database *separately*,
so a value can never be reinterpreted as part of the query's structure, no matter
what characters it contains.

## Setup used for this level

```sql
CREATE TABLE users (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username      TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin      BOOLEAN NOT NULL DEFAULT false
);
INSERT INTO users (username, password_hash, is_admin) VALUES
    ('alice', 'hash_alice_secret', false),
    ('bob',   'hash_bob_secret',   false),
    ('root',  'hash_super_secret_admin_password', true);
```

## The vulnerable version — do not do this

```python
def vulnerable_login(conn, username, password_hash):
    """DO NOT DO THIS: builds SQL via string formatting."""
    query = f"""
        SELECT id, username, is_admin FROM users
        WHERE username = '{username}' AND password_hash = '{password_hash}'
    """
    return conn.execute(query).fetchall()
```

It works correctly for legitimate input:

```python
print(vulnerable_login(conn, "alice", "hash_alice_secret"))
```
```text
[(1, 'alice', False)]
```

```python
print(vulnerable_login(conn, "alice", "wrong"))
```
```text
[]
```

Looks fine. The bug is invisible until someone sends input containing a `'`
character.

**Go, the same bug:** `database/sql` and pgx never string-format a query for you —
you have to go out of your way to reintroduce this, exactly the way `fmt.Sprintf`
does here:

```go
// DO NOT DO THIS: builds SQL via string formatting (fmt.Sprintf).
func vulnerableLogin(username, password string) ([]string, error) {
    query := fmt.Sprintf(
        "SELECT id, username, is_admin FROM users WHERE username = '%s' AND password_hash = '%s'",
        username, password,
    )
    rows, err := db.QueryContext(ctx, query)
    // ... scan rows into out, see below for the full loop
    return out, err
}
```

## The live exploit

**Payload 1 — classic auth bypass**, submitted as both the "username" and
"password" fields: `' OR '1'='1`

```python
payload_user = "' OR '1'='1"
payload_pass = "' OR '1'='1"
rows = vulnerable_login(conn, payload_user, payload_pass)
print("rows returned:", rows)
```

Real output — **every user in the table, including the admin account**:

```text
rows returned: [(1, 'alice', False), (2, 'bob', False), (3, 'root', True)]
```

What actually got sent to Postgres, once the f-string substituted the payload in:

```sql
SELECT id, username, is_admin FROM users
WHERE username = '' OR '1'='1' AND password_hash = '' OR '1'='1'
```

`'1'='1'` is always true, so the `WHERE` clause is satisfied for every row in the
table regardless of the real username/password check — the injected `OR` rewrote
the query's logic entirely.

Running the identical payload through Go's `vulnerableLogin`:

```go
rows, err := vulnerableLogin("' OR '1'='1", "' OR '1'='1")
fmt.Println("rows returned:", rows, err)
```

Real output — same full-table leak, same admin account included:

```text
rows returned: [(1, alice, false) (2, bob, false) (3, root, true)] <nil>
```

**Payload 2 — comment out the rest of the query**, log in as a specific account
(`root`) with no valid password at all: `root' -- `

```python
payload_user2 = "root' -- "
rows = vulnerable_login(conn, payload_user2, "irrelevant")
print("rows returned:", rows)
```

Real output — **logged in as the admin account with zero knowledge of its
password**:

```text
rows returned: [(3, 'root', True)]
```

What actually got sent:

```sql
SELECT id, username, is_admin FROM users
WHERE username = 'root' -- ' AND password_hash = 'irrelevant'
```

`--` starts a <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> comment; everything after it on that line — including the entire
password check — is discarded before Postgres even parses it. The query becomes
"find the user named root," full stop.

Same payload through Go:

```go
rows, err := vulnerableLogin("root' -- ", "irrelevant")
fmt.Println("rows returned:", rows, err)
```

```text
rows returned: [(3, root, true)] <nil>
```

## The fix — parameterized queries

```python
def safe_login(conn, username, password_hash):
    """Parameterized: the driver sends the value out-of-band from the SQL text."""
    return conn.execute(
        "SELECT id, username, is_admin FROM users WHERE username = %s AND password_hash = %s",
        (username, password_hash),
    ).fetchall()
```

The `%s` placeholders are not string formatting — `psycopg` sends the query text
`SELECT ... WHERE username = %s AND password_hash = %s` to Postgres as a prepared
statement, then sends the two values separately over the wire protocol as literal
data for the two parameter slots. There is no step where Postgres re-parses a value
as <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> syntax, because the value is never part of the <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> text at all.

**Go (`database/sql` + pgx):** the same fix, Go's placeholder syntax is positional
(`$1`, `$2` — Postgres's native numbered-parameter style, which pgx uses directly;
`lib/pq` accepts the same `$N` syntax):

```go
// The fix: $1/$2 placeholders -- values sent out-of-band from the SQL text.
func safeLogin(username, password string) ([]string, error) {
    rows, err := db.QueryContext(ctx,
        "SELECT id, username, is_admin FROM users WHERE username = $1 AND password_hash = $2",
        username, password,
    )
    // ... identical scan loop to vulnerableLogin
    return out, err
}
```

Running the **exact same two exploit payloads** through `safe_login`:

```python
print("payload1 as literal credentials:", safe_login(conn, payload_user, payload_pass))
print("payload2 as literal credentials:", safe_login(conn, payload_user2, "irrelevant"))
```

Real output:

```text
payload1 as literal credentials: []
payload2 as literal credentials: []
```

Both exploits now return nothing at all. `%s` treated `"' OR '1'='1"` and
`"root' -- "` as ordinary (and, in this table, nonexistent) literal username
strings — the `'`, `OR`, and `--` characters have no special meaning to a
parameter value; they're just characters being compared against the `username`
column with plain `=`.

Running the same two payloads through Go's `safeLogin`:

```go
r1, _ := safeLogin("' OR '1'='1", "' OR '1'='1")
r2, _ := safeLogin("root' -- ", "irrelevant")
fmt.Println("payload1 as literal credentials:", r1)
fmt.Println("payload2 as literal credentials:", r2)
```

Real output — identical result to the Python fix, zero rows for both:

```text
payload1 as literal credentials: []
payload2 as literal credentials: []
```

## Common mistakes

- **"We escape quotes, so we're safe."** Naive escaping (doubling `'` to `''`, or
  stripping quotes) is a well-documented source of bypasses of its own (encoding
  tricks, forgetting a character class, database-specific escaping rules) —
  parameterized queries are not "better escaping," they're a different mechanism
  entirely that makes the class of bug structurally impossible, not just harder to
  trigger.
- **Parameterizing values but not identifiers.** `%s` placeholders work for
  *values* (`WHERE username = %s`). They cannot be used for table or column names —
  `f"SELECT * FROM {table_name}"` is still injectable no matter how you handle
  values elsewhere. If a table/column name genuinely needs to be dynamic, validate
  it against an explicit allowlist of known-safe names, or use your driver's
  identifier-quoting helper (`psycopg.sql.Identifier`) — never string-format it in.
- **Assuming an <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> makes this automatically safe.** Most ORMs parameterize
  standard query-builder calls, but nearly all of them also offer a raw/literal <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>
  escape hatch (`.raw()`, `.extra()`, string-built `WHERE` fragments) — and a raw
  query built with an f-string through an <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> is exactly as vulnerable as the
  `vulnerable_login` function above.
- **Trusting client-side validation.** Nothing stops an attacker from sending
  requests directly to your <abbr title="Application Programming Interface">API</abbr>, bypassing whatever a browser form does — the
  parameterization has to happen at the query layer, not the input form.
- **In Go specifically: building a query with `fmt.Sprintf` "just this once."**
  `database/sql` and pgx are exactly as safe as psycopg when you use `$1`/`$2`
  placeholders — the vulnerability demonstrated above only exists because
  `vulnerableLogin` deliberately bypassed that with `fmt.Sprintf`. There's no
  compiler warning for this in Go; a code reviewer has to catch it.

## What's next

Level 12 covers changing a live schema safely — including how a Postgres-specific
locking detail interacts with the kind of `ALTER TABLE` you'll run in production.
