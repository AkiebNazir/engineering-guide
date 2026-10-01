"""
LAB 04 (advanced) - Authentication and authorization in GraphQL, over real HTTP
================================================================================
You will learn
  * GraphQL usually has ONE endpoint (POST /graphql), so authorization cannot live in the URL:
    it must live in RESOLVERS - per field, per object
  * context: authenticate ONCE per request from the HTTP header, share the user with every resolver
  * permission classes:  @strawberry.field(permission_classes=[IsAuthenticated])
  * field-level rules: `email` is visible to the user themselves and to admins only
  * object-level rules (BOLA): "can THIS caller read THIS invoice?"
  * hiding internals: MaskErrors turns unexpected exceptions into a generic message
  * shrinking the attack surface: DisableIntrospection for private production APIs
  * remember: failures come back as HTTP 200 + `errors`; read `extensions.code`, not the message

Needs   pip install "strawberry-graphql[fastapi]" fastapi httpx
Run it  python 04_auth_permissions_and_masking.py
"""
import logging
import typing

import strawberry
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from graphql import GraphQLError
from strawberry.extensions import DisableIntrospection, MaskErrors
from strawberry.fastapi import GraphQLRouter
from strawberry.permission import BasePermission

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

TOKENS = {"tok-alice": {"id": 1, "role": "user"}, "tok-bob": {"id": 2, "role": "user"}, "tok-root": {"id": 99, "role": "admin"}}
USERS = {1: {"id": 1, "name": "Alice", "email": "alice@x.io"}, 2: {"id": 2, "name": "Bob", "email": "bob@x.io"}}
INVOICES = {100: {"id": 100, "owner_id": 1, "total": 250}, 200: {"id": 200, "owner_id": 2, "total": 900}}


def coded(message: str, code: str) -> GraphQLError:
    return GraphQLError(message, extensions={"code": code})       # clients switch on the code


# ------------------------------------------------------------- permissions --
class IsAuthenticated(BasePermission):
    message = "authentication required"

    def has_permission(self, source: typing.Any, info: strawberry.Info, **kwargs) -> bool:
        return info.context["user"] is not None

    def on_unauthorized(self):
        raise coded(self.message, "UNAUTHENTICATED")


class IsAdmin(BasePermission):
    message = "admin only"

    def has_permission(self, source, info: strawberry.Info, **kwargs) -> bool:
        user = info.context["user"]
        return bool(user and user["role"] == "admin")

    def on_unauthorized(self):
        raise coded(self.message, "FORBIDDEN")


# ------------------------------------------------------------------ schema --
@strawberry.type
class User:
    id: int
    name: str
    _email: strawberry.Private[str]

    @strawberry.field
    def email(self, info: strawberry.Info) -> str | None:
        viewer = info.context["user"]                             # FIELD-level rule
        if viewer and (viewer["id"] == self.id or viewer["role"] == "admin"):
            return self._email
        return None                                              # hidden, not an error


@strawberry.type
class Invoice:
    id: int
    total: int


@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: int) -> User | None:                       # public profile
        u = USERS.get(id)
        return User(id=u["id"], name=u["name"], _email=u["email"]) if u else None

    @strawberry.field(permission_classes=[IsAuthenticated])
    def invoice(self, id: int, info: strawberry.Info) -> Invoice | None:
        row, viewer = INVOICES.get(id), info.context["user"]
        if not row or (row["owner_id"] != viewer["id"] and viewer["role"] != "admin"):
            return None                                          # OBJECT-level rule; same answer for "missing" and "not yours"
        return Invoice(id=row["id"], total=row["total"])

    @strawberry.field(permission_classes=[IsAdmin])
    def all_invoice_totals(self) -> int:
        return sum(i["total"] for i in INVOICES.values())

    @strawberry.field
    def broken(self) -> str:
        raise RuntimeError("psycopg2.OperationalError: password authentication failed for user 'app' at 10.0.3.7")


async def get_context(request: Request):
    token = request.headers.get("authorization", "").removeprefix("Bearer ")
    return {"user": TOKENS.get(token)}                            # authenticate ONCE per request


def build_app(production: bool) -> FastAPI:
    extensions = [MaskErrors(should_mask_error=lambda e: e.original_error is not None and not isinstance(e.original_error, GraphQLError))]
    if production:
        extensions.append(DisableIntrospection())
    schema = strawberry.Schema(Query, extensions=extensions)
    app = FastAPI()
    app.include_router(GraphQLRouter(schema, context_getter=get_context), prefix="/graphql")
    return app


def gql(client, query, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = client.post("/graphql", json={"query": query}, headers=headers)
    body = r.json()
    codes = [e.get("extensions", {}).get("code") or e["message"] for e in body.get("errors", [])]
    print(f"HTTP {r.status_code} data={body.get('data')}  errors={codes or None}")
    return r.status_code, body


if __name__ == "__main__":
    c = TestClient(build_app(production=True))

    print("-- anonymous --")
    _, b = gql(c, "{ invoice(id: 100) { total } }")
    assert b["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED"          # HTTP is 200 even so

    print("-- authenticated, own object --")
    _, b = gql(c, "{ invoice(id: 100) { total } }", "tok-alice")
    assert b["data"]["invoice"]["total"] == 250

    print("-- authenticated, SOMEONE ELSE'S object (BOLA) --")
    _, b = gql(c, "{ invoice(id: 200) { total } }", "tok-alice")
    assert b["data"]["invoice"] is None

    print("-- field-level: who sees Bob's email? --")
    for who, tok in [("anonymous", None), ("alice", "tok-alice"), ("bob", "tok-bob"), ("admin", "tok-root")]:
        print(f"  {who:<9}", end=" ")
        _, b = gql(c, "{ user(id: 2) { name email } }", tok)
    _, anon = gql(c, "{ user(id: 2) { email } }")
    _, admin = gql(c, "{ user(id: 2) { email } }", "tok-root")
    assert anon["data"]["user"]["email"] is None and admin["data"]["user"]["email"] == "bob@x.io"

    print("-- role check --")
    _, b = gql(c, "{ allInvoiceTotals }", "tok-alice")
    assert b["errors"][0]["extensions"]["code"] == "FORBIDDEN"
    _, b = gql(c, "{ allInvoiceTotals }", "tok-root")
    assert b["data"]["allInvoiceTotals"] == 1150

    print("-- unexpected exception: internals are masked --")
    _, b = gql(c, "{ broken }", "tok-alice")
    assert "psycopg2" not in str(b) and "10.0.3.7" not in str(b)

    print("-- introspection disabled in production --")
    _, b = gql(c, "{ __schema { types { name } } }", "tok-alice")
    assert b["errors"] and "introspection" in b["errors"][0]["message"].lower()

    dev = TestClient(build_app(production=False))
    _, b = gql(dev, "{ __schema { queryType { name } } }")
    assert b["data"]["__schema"]["queryType"]["name"] == "Query"
    print("OK")
