"""
FOUNDATION LEVEL 09 - Authentication: proving who you are
=============================================================
Middleware (level 08) is the mechanism and context (level 07) is the carrier;
authentication is the first real thing to put in them. It answers exactly ONE
question: "do we recognize this caller at all?" It says NOTHING about what
that caller may do - that is level 10, authorization, and keeping the two
apart is the whole reason they are separate levels.

The shape, which never changes in real systems:
  1. the transport hands you a credential - by convention the HTTP header
     `Authorization: Bearer <token>` (level 11 reads it off a real request;
     here we pass it in beside the query, because there is no HTTP yet)
  2. middleware resolves it into an identity ONCE, before execution
  3. it puts that identity (or None) in the context
  4. a protected field's resolver checks the context and refuses if absent

There is no 401 to send: GraphQL has no per-field status codes, and the HTTP
response - when there is one - is a 200 carrying `errors` (level 06). The
community convention that replaces the status code is an `extensions.code`
on the error, and `UNAUTHENTICATED` is the agreed name for this one.

Note where the check lives: in the FIELD, not in the middleware. One request
may mix public and protected fields, and rejecting the whole request because
one field needed a token would be wrong. Level 06's partial responses are
exactly what makes this work.

You will learn
  * the `Authorization: Bearer <token>` convention, and resolving it once
  * that authentication middleware IDENTIFIES but does not reject - the
    protected field decides
  * `errors[].extensions.code = "UNAUTHENTICATED"` as GraphQL's 401-equivalent
  * that a missing and an INVALID token are the same outcome, on purpose: never
    tell an attacker which half of the guess was right
  * that public fields in the same request still return real data

Run it   python 09_authentication_bearer_tokens.py
"""
import json
import logging
from typing import Callable

import strawberry
from graphql import GraphQLError

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

# A stand-in for "who is allowed in". A real service verifies a signed JWT or
# looks the token up in a store - see ../labs/python/04_auth_permissions_and_masking.py.
# The SHAPE of everything below is identical either way.
TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}

Request = dict
Response = dict
Execute = Callable[[Request], Response]


def current_user(info: strawberry.Info) -> dict:
    """Used by every protected resolver. Either returns the identity that
    authentication middleware put in the context, or refuses."""
    user = info.context.get("user")
    if user is None:
        # One deliberately vague message for both "no token" and "bad token".
        raise GraphQLError("not authenticated", extensions={"code": "UNAUTHENTICATED"})
    return user


@strawberry.type
class Query:
    @strawberry.field
    def public_notice(self) -> str:
        # No check at all: anyone may read this, token or not.
        return "the service is up"

    @strawberry.field
    def me(self, info: strawberry.Info) -> str | None:
        user = current_user(info)
        return f"{user['user']} ({user['role']})"

    @strawberry.field
    def secret_report(self, info: strawberry.Info) -> str | None:
        user = current_user(info)
        return f"revenue is fine, {user['user']}"


schema = strawberry.Schema(Query)


# ---- the authentication middleware -------------------------------------
def with_authentication(next_execute: Execute) -> Execute:
    """Runs once per request, BEFORE execution. It resolves the credential
    and records the result - it never rejects, because it cannot know whether
    the query even touches a protected field."""
    def wrapped(request: Request) -> Response:
        header = request.get("headers", {}).get("Authorization", "")
        user = None
        if header.startswith("Bearer "):
            user = TOKENS.get(header.removeprefix("Bearer "))  # None if unknown
        request["context"] = {"user": user}
        note = f"identified as {user['user']}" if user else "anonymous"
        print(f"  [auth] Authorization: {header or '<none>'!s:<26} -> {note}")
        return next_execute(request)
    return wrapped


def run_query(request: Request) -> Response:
    result = schema.execute_sync(
        request.get("query", ""),
        variable_values=request.get("variables"),
        context_value=request.get("context", {}),
    )
    response: Response = {"data": result.data}
    if result.errors:
        response["errors"] = [
            {"message": e.message, "path": e.path, "extensions": e.extensions} for e in result.errors
        ]
    return response


execute: Execute = with_authentication(run_query)


def run(title: str, query: str, token: str | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    print(f"\n# {title}")
    print(f"query    : {' '.join(query.split())}")
    response = execute({"query": query, "headers": headers})
    print(f"response : {json.dumps(response)}")
    return response


if __name__ == "__main__":
    res = run("1. a public field needs nothing", "{ publicNotice }")
    assert res["data"] == {"publicNotice": "the service is up"} and "errors" not in res

    res = run("2. a protected field with NO token -> UNAUTHENTICATED", "{ me }")
    assert res["data"] == {"me": None}
    assert res["errors"][0]["message"] == "not authenticated"
    assert res["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED"
    print("   -> there is no HTTP status here to set; the error IS the 401")

    res = run("3. a token that is not recognized -> the SAME answer, deliberately",
              "{ me }", token="not-a-real-token")
    assert res["data"] == {"me": None}
    assert res["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED"
    print("   -> 'no token' and 'wrong token' must be indistinguishable to the caller")

    res = run("4. a valid token -> the field resolves", "{ me }", token="alice-token")
    assert res["data"] == {"me": "alice (admin)"} and "errors" not in res

    res = run("5. a different valid token -> a different identity, same code",
              "{ me secretReport }", token="bob-token")
    assert res["data"] == {"me": "bob (viewer)", "secretReport": "revenue is fine, bob"}
    print("   -> note bob, a 'viewer', could read the secret report. Nothing so far stops him.")
    print("      That is level 10's job: authentication is not authorization.")

    # The partial-response rule from level 06 is what makes per-field auth usable.
    res = run("6. one request mixing public and protected fields, unauthenticated",
              "{ publicNotice me secretReport }")
    assert res["data"] == {"publicNotice": "the service is up", "me": None, "secretReport": None}
    assert len(res["errors"]) == 2
    assert {tuple(e["path"]) for e in res["errors"]} == {("me",), ("secretReport",)}
    print("   -> the public field still answered. Rejecting the whole request would have been wrong.")

    print("\nOK")
