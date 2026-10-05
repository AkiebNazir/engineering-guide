"""
FOUNDATION LEVEL 02 - Field arguments: fields that take input
=================================================================
So far every field returned a constant. Arguments make a field a FUNCTION:
`greet(name: "Ada")` instead of just `greet`. In REST you would express this
as a path parameter (`/greet/Ada`) or a query string (`/greet?name=Ada`), and
you would parse and validate it yourself. Here the argument is part of the
schema, so the engine parses, type-checks, and rejects bad input for you
before your resolver is ever called.

Arguments belong to a FIELD, not to the request. Two fields in the same query
can each take their own, and a nested field deep in the tree can take
arguments too (level 04).

You will learn
  * how to declare an argument and read it inside the resolver
  * required (`String!`) vs optional-with-a-default (`Int = 2`) arguments
  * that a missing required argument is a VALIDATION error: caught against the
    schema before any resolver runs, so your resolver never sees bad input
  * that a wrong-typed argument (`Int` given a string) is rejected the same way
  * that arguments are typed data, not string interpolation - which is why
    GraphQL has no equivalent of SQL-style query-string injection

Run it   python 02_field_arguments.py
"""
import json
import logging

import strawberry

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

resolver_ran = {"greet": 0, "power": 0}


@strawberry.type
class Query:
    # A parameter with no default becomes a REQUIRED argument: name: String!
    @strawberry.field
    def greet(self, name: str) -> str:
        resolver_ran["greet"] += 1
        # By the time this line runs, `name` is guaranteed to be a str and
        # guaranteed to be present. We did not check either of those things.
        return f"hello, {name}"

    # A parameter with a default becomes an OPTIONAL argument: exp: Int! = 2.
    # Defaults live in the schema, so every client sees them in the contract
    # instead of having to read your docs.
    @strawberry.field
    def power(self, base: int, exp: int = 2) -> int:
        resolver_ran["power"] += 1
        return base**exp

    # `str | None = None` is a nullable, optional argument: the client may
    # omit it, or explicitly pass null, and both mean "no filter".
    @strawberry.field
    def shout(self, text: str, suffix: str | None = None) -> str:
        return text.upper() + (suffix or "")


schema = strawberry.Schema(Query)


def run(title: str, query: str):
    result = schema.execute_sync(query)
    payload = {"data": result.data}
    if result.errors:
        payload["errors"] = [{"message": e.message} for e in result.errors]
    print(f"\n# {title}")
    print(f"query    : {query}")
    print(f"response : {json.dumps(payload)}")
    return result


if __name__ == "__main__":
    print("=== the schema, as SDL: arguments are part of the contract ===")
    print(schema.as_str())

    r = run("1. a field that takes an argument", '{ greet(name: "Ada") }')
    assert r.data == {"greet": "hello, Ada"}

    # Same field, called twice in one query with different arguments. Aliases
    # (`en:` / `fr:`) are needed because both results are keys in one object.
    r = run("2. the same field twice, with different arguments (aliases)",
            '{ en: greet(name: "Ada")  other: greet(name: "Grace") }')
    assert r.data == {"en": "hello, Ada", "other": "hello, Grace"}

    r = run("3. an optional argument, left out -> the schema's default (exp = 2)", "{ power(base: 5) }")
    assert r.data == {"power": 25}

    r = run("4. the same field, default overridden", "{ power(base: 2, exp: 10) }")
    assert r.data == {"power": 1024}

    # The interesting part: bad input never reaches the resolver.
    before = resolver_ran["greet"]
    r = run("5. a REQUIRED argument left out -> validation error, resolver never runs", "{ greet }")
    assert r.data is None
    assert "argument 'name' of type 'String!' is required" in r.errors[0].message
    assert resolver_ran["greet"] == before, "the resolver must not have been called"
    print("   -> compare REST, where an empty ?name= arrives as your problem to handle")

    r = run("6. a wrong-TYPED argument -> rejected the same way", '{ power(base: "five") }')
    assert r.data is None and "Int cannot represent non-integer value" in r.errors[0].message

    r = run("7. an optional nullable argument, omitted and then given",
            '{ plain: shout(text: "hi")  loud: shout(text: "hi", suffix: "!!!") }')
    assert r.data == {"plain": "HI", "loud": "HI!!!"}

    print("\nOK")
