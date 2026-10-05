"""
FOUNDATION LEVEL 06 - Errors: why a GraphQL response can be half-successful
===============================================================================
This is the level where GraphQL stops resembling REST at all, so it is worth
slowing down for.

In REST, one request has ONE outcome: a 200 or a 500, success or failure,
never both. In GraphQL one request asks for many fields, each resolved by a
different function, possibly hitting different services. If two fields work
and one fails, "the request" is neither successful nor failed. So the
response carries BOTH: `data` with whatever resolved, and `errors` with a
list of what did not - each entry naming its `path` in the response tree.

The rule that decides how much damage one failure does is nullability:
  - a NULLABLE field (`String`) that fails becomes null, an entry is added to
    `errors`, and its siblings are untouched -> partial data.
  - a NON-NULL field (`String!`) that fails cannot be null. So the engine
    nulls its PARENT instead. If the parent is also non-null, it nulls the
    grandparent, and so on. This is "null propagation", and at the top level
    it wipes `data` entirely.
That is why `!` is a promise, not decoration: promise only what cannot fail.

One more thing that trips people up: the HTTP status for all of this is
normally 200. The transport delivered the message fine; the message just
happens to describe failures (levels 11-13 show that literally).

You will learn
  * that `data` and `errors` can both be populated in one response
  * how to read an error's `path` to find which field failed
  * partial data: one nullable field failing does not harm its siblings
  * null propagation: a failing NON-NULL field nulls its parent instead
  * the three distinct failure moments: parse -> validate -> execute, and that
    only execution errors can ever produce partial data

Run it   python 06_errors_and_partial_responses.py
"""
import json
import logging

import strawberry

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)


@strawberry.type
class Profile:
    name: str

    @strawberry.field
    def avatar(self) -> str | None:
        # NULLABLE and failing: becomes null, siblings survive.
        raise RuntimeError("avatar service timed out")

    @strawberry.field
    def handle(self) -> str:
        # NON-NULL and failing: cannot be null, so Profile itself gets nulled.
        raise RuntimeError("handle service timed out")


@strawberry.type
class Query:
    @strawberry.field
    def healthy(self) -> bool:
        return True

    @strawberry.field
    def version(self) -> str:
        return "3.1.0"

    @strawberry.field
    def flaky(self) -> str | None:
        raise RuntimeError("upstream cache is down")

    @strawberry.field
    def strict(self) -> str:
        raise RuntimeError("upstream cache is down")

    @strawberry.field
    def profile(self) -> Profile | None:
        return Profile(name="Ada")


schema = strawberry.Schema(Query)


def run(title: str, query: str):
    result = schema.execute_sync(query)
    payload = {"data": result.data}
    if result.errors:
        payload["errors"] = [{"message": e.message, "path": e.path} for e in result.errors]
    print(f"\n# {title}")
    print(f"query    : {' '.join(query.split())}")
    print(f"response : {json.dumps(payload)}")
    return result


if __name__ == "__main__":
    # ---- failure moment 1: PARSE. The text is not a GraphQL document. ----
    r = run("1. a syntax error: nothing is even understood, let alone run", "{ healthy ")
    assert r.data is None and "Syntax Error" in r.errors[0].message

    # ---- failure moment 2: VALIDATE. Valid text, but it contradicts the schema. ----
    r = run("2. a validation error: understood, but not allowed by the schema", "{ healthy nope }")
    assert r.data is None and "Cannot query field 'nope'" in r.errors[0].message
    print("   -> parse and validate errors are all-or-nothing: `data` is null, no resolver ran")

    # ---- failure moment 3: EXECUTE. This is the only one that can be partial. ----
    r = run("3. THE INTERESTING ONE: a nullable field fails, its siblings do not care",
            "{ healthy version flaky }")
    assert r.data == {"healthy": True, "version": "3.1.0", "flaky": None}
    assert r.errors and r.errors[0].path == ["flaky"]
    print("   -> data AND errors, together. `healthy` and `version` are real answers.")
    print("   -> a REST client would have seen one 500 and thrown the good data away")

    r = run("4. the same failure on a NON-NULL field: the null bubbles up and wipes data",
            "{ healthy version strict }")
    assert r.data is None
    assert r.errors[0].path == ["strict"]
    print("   -> `strict: String!` promised a value; the only place to put the null was `data` itself")

    # Nested: the propagation stops at the first nullable ancestor.
    r = run("5. nested, nullable child: only that leaf is lost", "{ profile { name avatar } }")
    assert r.data == {"profile": {"name": "Ada", "avatar": None}}
    assert r.errors[0].path == ["profile", "avatar"]
    print("   -> the path says exactly where: profile.avatar")

    r = run("6. nested, NON-NULL child: the whole parent object is nulled instead",
            "{ healthy profile { name handle } }")
    assert r.data == {"healthy": True, "profile": None}
    assert r.errors[0].path == ["profile", "handle"]
    print("   -> `profile` is nullable, so the damage stopped there: `healthy` still answered")

    # Several failures, several errors: the list is not capped at one.
    r = run("7. two independent failures -> two entries in errors", "{ flaky profile { avatar } }")
    assert len(r.errors) == 2
    assert {tuple(e.path) for e in r.errors} == {("flaky",), ("profile", "avatar")}
    print("   -> every failing field reports itself; the client decides what is fatal")

    print("\nOK")
