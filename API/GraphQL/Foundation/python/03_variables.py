"""
FOUNDATION LEVEL 03 - Variables: one query text, many different inputs
==========================================================================
In level 02 the argument value was baked into the query text: `greet(name:
"Ada")`. Asking about Grace meant building a DIFFERENT string. Variables fix
that: the query text declares typed placeholders (`$name: String!`), and the
actual values travel next to it in a separate `variables` map.

Why this matters, concretely:
  - the query text becomes a constant in your code, not a string you build.
    No quoting, no escaping, no accidental injection of a `"` or a `}`.
  - because the text never changes, it can be cached, logged, whitelisted, or
    registered with the server once by ID (that last one is "persisted
    queries" - see ../labs/, it is exactly this idea taken further).
  - the variable's declared type is checked against the schema, so a wrong
    value is rejected with a clear error before any resolver runs.
  - this is the ONLY way a real client works: `{"query": "...", "variables":
    {...}}` is the JSON body you will POST in levels 11-13.

Note the named operation: `query Greet($name: String!) { ... }`. Once you
declare variables you need that `query` keyword and (by convention) a name -
which also gives you something useful in logs and traces.

You will learn
  * how to declare variables in a query and pass them separately
  * that the query text is now reusable and cacheable - the interesting
    difference from level 02
  * that variable types are validated against the schema (missing, wrong type,
    or null-for-non-null are all caught the same way)
  * that a variable with a default in the query text can be omitted entirely

Run it   python 03_variables.py
"""
import json
import logging

import strawberry

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

USERS = {"1": "Ada", "2": "Grace", "3": "Katherine"}


@strawberry.type
class Query:
    @strawberry.field
    def greet(self, name: str, excited: bool = False) -> str:
        return f"hello, {name}" + ("!" if excited else "")

    @strawberry.field
    def user_name(self, id: strawberry.ID) -> str | None:
        return USERS.get(str(id))


schema = strawberry.Schema(Query)

# ONE constant string, declared once, reused for every caller below. This is
# the shape you want in real code: a module-level constant, never an f-string.
GREET = """
query Greet($name: String!, $excited: Boolean = false) {
  greet(name: $name, excited: $excited)
}
"""

LOOKUP = """
query Lookup($id: ID!) {
  userName(id: $id)
}
"""


def run(title: str, query: str, variables: dict | None = None):
    result = schema.execute_sync(query, variable_values=variables)
    payload = {"data": result.data}
    if result.errors:
        payload["errors"] = [{"message": e.message} for e in result.errors]
    print(f"\n# {title}")
    print(f"query    : {' '.join(query.split())}")
    print(f"variables: {json.dumps(variables)}")
    print(f"response : {json.dumps(payload)}")
    return result


if __name__ == "__main__":
    r = run("1. the query text with a placeholder, values passed beside it", GREET, {"name": "Ada"})
    assert r.data == {"greet": "hello, Ada"}

    # Exactly the same string as above. Only the variables map changed - this
    # is the whole lesson.
    r = run("2. SAME query text, different variables", GREET, {"name": "Grace", "excited": True})
    assert r.data == {"greet": "hello, Grace!"}

    # A variable with a default in the query text may be left out of the map.
    r = run("3. $excited has a default in the query text, so it can be omitted", GREET, {"name": "Katherine"})
    assert r.data == {"greet": "hello, Katherine"}

    r = run("4. a non-null variable that was not supplied -> clear error, no resolver runs",
            GREET, {"excited": True})
    assert r.data is None
    assert "$name" in r.errors[0].message and "was not provided" in r.errors[0].message

    r = run("5. a variable of the wrong type -> rejected against the schema", GREET, {"name": 42})
    assert r.data is None and "String cannot represent a non string value" in r.errors[0].message

    r = run("6. variables carry data, never syntax: a quote-heavy value is just a value",
            GREET, {"name": 'Bobby "); DROP TABLE users; --'})
    assert r.data["greet"] == 'hello, Bobby "); DROP TABLE users; --'
    print("   -> the value never becomes part of the query document, so it cannot change its meaning")

    r = run("7. a second reusable query, looking a user up by ID", LOOKUP, {"id": "2"})
    assert r.data == {"userName": "Grace"}

    r = run("8. same text, an ID that does not exist -> null, not an error", LOOKUP, {"id": "999"})
    assert r.data == {"userName": None} and not r.errors

    print("\nOK")
