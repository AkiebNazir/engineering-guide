"""
FOUNDATION LEVEL 10 - Authorization: what an identified caller may do
=========================================================================
Level 09 ended on a deliberate cliffhanger: bob, a "viewer", was allowed to
read a secret report just because his token was valid. Authentication had
done its whole job correctly - it only ever claimed to answer "who is this?"

Authorization answers the second, separate question: "may THIS caller do
THIS particular thing?" Two questions, two checks, two failure modes, and
mixing them up is one of the most common security bugs there is:
  - UNAUTHENTICATED (level 09, HTTP's 401): we do not know you. Retrying with
    a credential could work.
  - FORBIDDEN (this level, HTTP's 403): we know exactly who you are, and the
    answer is still no. Retrying changes nothing.
Telling a caller "forbidden" when you meant "unauthenticated" sends them off
to debug the wrong thing; the reverse leaks that the resource exists.

The check itself is boring on purpose - a role comparison. What matters is
WHERE it lives: inside the field's resolver, right before the effect, after
authentication has already put the identity in the context. Not in the
client, not in the middleware, not in the gateway.

You will learn
  * the difference between authentication and authorization, in code
  * `extensions.code = "FORBIDDEN"` as the 403-equivalent, distinct from 401
  * a role check guarding one destructive mutation, with the other fields of
    the same schema untouched
  * that the deny path must not perform (or half-perform) the effect
  * that the error message names what is needed without leaking data

Run it   python 10_authorization_role_based_access.py
"""
import json
import logging
from typing import Callable

import strawberry
from graphql import GraphQLError

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}

REPORTS: dict[str, str] = {"r1": "Q1 uptime", "r2": "Q2 uptime"}

Request = dict
Response = dict
Execute = Callable[[Request], Response]


# ---- the two checks, side by side, so the difference is impossible to miss --
def authenticate(info: strawberry.Info) -> dict:
    """Level 09, unchanged: who is this?"""
    user = info.context.get("user")
    if user is None:
        raise GraphQLError("not authenticated", extensions={"code": "UNAUTHENTICATED"})
    return user


def require_role(info: strawberry.Info, role: str) -> dict:
    """Level 10: authentication FIRST (you cannot authorize an unknown
    caller), then the permission itself."""
    user = authenticate(info)
    if user["role"] != role:
        raise GraphQLError(
            f"forbidden: this operation requires the '{role}' role",
            extensions={"code": "FORBIDDEN", "requiredRole": role},
        )
    return user


@strawberry.type
class Query:
    @strawberry.field
    def reports(self) -> list[str]:
        return list(REPORTS.values())

    @strawberry.field
    def me(self, info: strawberry.Info) -> str | None:
        user = authenticate(info)
        return f"{user['user']} ({user['role']})"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_report(self, info: strawberry.Info, title: str) -> str | None:
        # Authenticated, but no role needed: any known caller may add one.
        authenticate(info)
        new_id = f"r{len(REPORTS) + 1}"
        REPORTS[new_id] = title
        return new_id

    @strawberry.mutation
    def delete_report(self, info: strawberry.Info, id: strawberry.ID) -> bool | None:
        # The check comes BEFORE the effect. Nothing is read, deleted, or even
        # confirmed to exist until the caller has been cleared.
        require_role(info, "admin")
        return REPORTS.pop(str(id), None) is not None


schema = strawberry.Schema(Query, Mutation)


def with_authentication(next_execute: Execute) -> Execute:
    def wrapped(request: Request) -> Response:
        header = request.get("headers", {}).get("Authorization", "")
        user = TOKENS.get(header.removeprefix("Bearer ")) if header.startswith("Bearer ") else None
        request["context"] = {"user": user}
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


def run(title: str, query: str, token: str | None = None, variables: dict | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    print(f"\n# {title}")
    print(f"as       : {token or '<anonymous>'}")
    print(f"query    : {' '.join(query.split())}")
    response = execute({"query": query, "variables": variables, "headers": headers})
    print(f"response : {json.dumps(response)}")
    return response


DELETE = "mutation Delete($id: ID!) { deleteReport(id: $id) }"

if __name__ == "__main__":
    res = run("1. anonymous, a public read: fine", "{ reports }")
    assert res["data"] == {"reports": ["Q1 uptime", "Q2 uptime"]}

    # Failure mode A: we do not know you. 401-equivalent.
    res = run("2. anonymous, deleting: UNAUTHENTICATED - we do not know you", DELETE, variables={"id": "r1"})
    assert res["data"] == {"deleteReport": None}
    assert res["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED"
    assert REPORTS.get("r1") == "Q1 uptime", "nothing was deleted"

    # Failure mode B: we know you perfectly well. 403-equivalent.
    res = run("3. bob (viewer), deleting: FORBIDDEN - we know you, and it is still no",
              DELETE, token="bob-token", variables={"id": "r1"})
    assert res["data"] == {"deleteReport": None}
    assert res["errors"][0]["extensions"]["code"] == "FORBIDDEN"
    assert res["errors"][0]["extensions"]["requiredRole"] == "admin"
    assert res["errors"][0]["message"] == "forbidden: this operation requires the 'admin' role"
    assert REPORTS.get("r1") == "Q1 uptime", "the deny path must not perform the effect"
    print("   -> a DIFFERENT code and a different message from case 2, on purpose:")
    print("      bob retrying with a new token forever would never help him")

    # Bob is not powerless - he is a known caller, just not an admin. The
    # permission is per operation, not per user.
    res = run("4. bob, adding a report: allowed - authenticated is enough here",
              'mutation { addReport(title: "Q3 uptime") }', token="bob-token")
    assert res["data"]["addReport"] == "r3" and "errors" not in res

    res = run("5. alice (admin), deleting: allowed", DELETE, token="alice-token", variables={"id": "r1"})
    assert res["data"] == {"deleteReport": True} and "errors" not in res
    assert "r1" not in REPORTS, "this time it really was deleted"

    # Same caller, same role, same code path - the id simply did not exist.
    # Note this is NOT an authorization failure, and must not look like one.
    res = run("6. alice, deleting something that is not there: false, not an error",
              DELETE, token="alice-token", variables={"id": "nope"})
    assert res["data"] == {"deleteReport": False} and "errors" not in res

    res = run("7. the state afterwards", "{ reports }")
    assert res["data"] == {"reports": ["Q2 uptime", "Q3 uptime"]}

    print("\nOK")
