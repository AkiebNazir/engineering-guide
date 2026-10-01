"""
LAB 02 (basic) - Mutations, input types and "expected errors as data"
=====================================================================
You will learn
  * a Mutation is a write; it takes an `input` object and returns the new state in the same round trip
  * input types (`@strawberry.input`) are for arguments only; output types are for responses
  * two ways to report failure:
        - exceptions  -> the `errors` array   (bugs, auth failures, infrastructure)
        - a UNION     -> `data`               (EXPECTED business failures: duplicate email, invalid input)
    The union makes the failure part of the schema, so clients must handle it (type-safe).
  * execution order: top-level mutation fields run one AFTER another, in the order written

Needs   pip install strawberry-graphql
Run it  python 02_mutations_and_input_validation.py
"""
import json
import logging
from typing import Annotated

import strawberry

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

USERS: dict[int, dict] = {}
LOG: list[str] = []


@strawberry.type
class User:
    id: int
    name: str
    email: str


@strawberry.type
class ValidationError:            # an EXPECTED failure, modelled as a type
    field: str
    message: str


@strawberry.type
class EmailTaken:
    email: str


CreateUserResult = Annotated[User | ValidationError | EmailTaken, strawberry.union("CreateUserResult")]


@strawberry.input
class CreateUserInput:
    name: str
    email: str


@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> list[User]:
        return [User(**u) for u in USERS.values()]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, input: CreateUserInput) -> CreateUserResult:
        if "@" not in input.email:
            return ValidationError(field="email", message="must contain @")
        if any(u["email"] == input.email for u in USERS.values()):
            return EmailTaken(email=input.email)
        uid = len(USERS) + 1
        USERS[uid] = {"id": uid, "name": input.name, "email": input.email}
        LOG.append(f"create_user({input.name})")
        return User(**USERS[uid])

    @strawberry.mutation
    def rename_user(self, id: int, name: str) -> User | None:
        if id not in USERS:
            return None
        USERS[id]["name"] = name
        LOG.append(f"rename_user({id}, {name})")
        return User(**USERS[id])


schema = strawberry.Schema(Query, mutation=Mutation)

CREATE = """
mutation Create($input: CreateUserInput!) {
  createUser(input: $input) {
    __typename
    ... on User            { id name email }
    ... on ValidationError { field message }
    ... on EmailTaken      { email }
  }
}"""


def run(label, query, variables=None):
    r = schema.execute_sync(query, variable_values=variables)
    print(f"{label:<28}->", json.dumps(r.data), "| errors:", [e.message for e in r.errors] if r.errors else None)
    return r


if __name__ == "__main__":
    r = run("create (ok)", CREATE, {"input": {"name": "Ana", "email": "ana@x.io"}})
    assert r.data["createUser"]["__typename"] == "User"

    r = run("create (bad email)", CREATE, {"input": {"name": "Bob", "email": "bob"}})
    assert r.data["createUser"] == {"__typename": "ValidationError", "field": "email", "message": "must contain @"}
    assert not r.errors, "expected failures are DATA, not `errors`"

    r = run("create (duplicate)", CREATE, {"input": {"name": "Ana2", "email": "ana@x.io"}})
    assert r.data["createUser"]["__typename"] == "EmailTaken"

    r = run("missing required input", CREATE, {"input": {"name": "no email"}})
    assert r.errors and "email" in r.errors[0].message           # the schema itself rejects it

    print("\n-- mutation fields run SERIALLY, in document order --")
    LOG.clear()
    r = run("two writes, one request", """mutation {
        a: createUser(input: {name: "Cy", email: "cy@x.io"}) { ... on User { id } }
        b: renameUser(id: 2, name: "Cyrus") { name }
    }""")
    print("execution log:", LOG)
    assert LOG == ["create_user(Cy)", "rename_user(2, Cyrus)"]     # b could only work because a ran first
    assert r.data["b"]["name"] == "Cyrus"

    r = run("rename unknown id", 'mutation { renameUser(id: 99, name: "x") { name } }')
    assert r.data == {"renameUser": None}
    print("\nOK")
