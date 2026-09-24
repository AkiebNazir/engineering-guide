"""
FOUNDATION LEVEL 04 - Nested object types: resolvers calling resolvers
=========================================================================
Every field so far returned a scalar - a leaf. The moment a field returns an
OBJECT type, the client must say which of that object's fields it wants, and
the response grows a level deeper. This is where GraphQL stops looking like a
function call and starts looking like a graph: one query walks from a report,
to its owner, to that owner's team, in one round trip.

THE ONE IDEA TO TAKE AWAY - the resolver chain:
  A resolver's return value becomes the SOURCE (the `self`) of the resolvers
  one level down. `report` returns a Report object; the `owner` field's
  resolver then runs with that Report as `self`, and returns a User; the
  `team` resolver runs with that User as `self`. Nobody passes anything
  explicitly. Each resolver only knows about its own parent.

  That also means depth costs work: a nested field's resolver runs once per
  parent object. Three reports, each with an owner, is 1 + 3 resolver calls -
  and if each owner hit a database that would be the famous N+1 problem
  (solved with dataloaders in ../labs/, deliberately out of scope here).

You will learn
  * how to define an object type and return it from a field
  * that selecting an object requires selecting fields INSIDE it
  * the resolver chain: parent return value -> child resolver's `self`
  * that a field with no explicit resolver just reads the same-named
    attribute off its parent (the "default resolver")
  * that nested fields can take arguments too, at any depth

Run it   python 04_nested_object_types.py
"""
import json
import logging

import strawberry

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

TEAMS = {"t1": {"name": "platform", "region": "eu-west"}}
USERS = {"u1": {"name": "Ada", "email": "ada@example.com", "team_id": "t1"}}
REPORTS = [
    {"id": "r1", "title": "Q1 uptime", "owner_id": "u1"},
    {"id": "r2", "title": "Q2 uptime", "owner_id": "u1"},
]

calls = {"owner": 0, "team": 0}


@strawberry.type
class Team:
    # No @strawberry.field decorator and no function body: these are plain
    # fields, served by the DEFAULT resolver - "read the attribute of the
    # same name off the parent object". Most fields in real schemas are this.
    name: str
    region: str


@strawberry.type
class User:
    name: str
    email: str
    team_id: strawberry.Private[str]  # internal: part of our data, NOT part of the contract

    @strawberry.field
    def team(self) -> Team:
        # `self` here is the User object that the `owner` resolver returned.
        calls["team"] += 1
        row = TEAMS[self.team_id]
        return Team(name=row["name"], region=row["region"])


@strawberry.type
class Report:
    id: strawberry.ID
    title: str
    owner_id: strawberry.Private[str]

    @strawberry.field
    def owner(self) -> User:
        # `self` is the Report object that the `report`/`reports` resolver
        # returned. This resolver runs ONCE PER REPORT in the parent list.
        calls["owner"] += 1
        row = USERS[self.owner_id]
        return User(name=row["name"], email=row["email"], team_id=row["team_id"])

    @strawberry.field
    def summary(self, max_length: int = 10) -> str:
        # Nested fields take arguments exactly like top-level ones do.
        return self.title[:max_length]


def to_report(row: dict) -> Report:
    return Report(id=strawberry.ID(row["id"]), title=row["title"], owner_id=row["owner_id"])


@strawberry.type
class Query:
    @strawberry.field
    def reports(self) -> list[Report]:
        return [to_report(r) for r in REPORTS]

    @strawberry.field
    def report(self, id: strawberry.ID) -> Report | None:
        row = next((r for r in REPORTS if r["id"] == str(id)), None)
        return to_report(row) if row else None


schema = strawberry.Schema(Query)


def run(title: str, query: str, variables: dict | None = None):
    result = schema.execute_sync(query, variable_values=variables)
    payload = {"data": result.data}
    if result.errors:
        payload["errors"] = [{"message": e.message} for e in result.errors]
    print(f"\n# {title}")
    print(f"query    : {' '.join(query.split())}")
    print(f"response : {json.dumps(payload)}")
    return result


if __name__ == "__main__":
    print("=== the schema, as SDL: three object types, wired together ===")
    print(schema.as_str())

    # Asking for an object WITHOUT choosing fields inside it is meaningless,
    # so the schema rejects it. GraphQL has no "give me the whole object".
    r = run("1. selecting an object with no sub-selection is an error", '{ report(id: "r1") }')
    assert r.data is None and "must have a selection of subfields" in r.errors[0].message

    r = run("2. one level deep: only the report's own fields", '{ report(id: "r1") { id title } }')
    assert r.data == {"report": {"id": "r1", "title": "Q1 uptime"}}
    assert calls["owner"] == 0, "owner was not requested, so its resolver did not run"

    r = run("3. two levels: the owner resolver runs with the Report as its parent",
            '{ report(id: "r1") { title owner { name email } } }')
    assert r.data["report"]["owner"]["name"] == "Ada"
    print("resolver calls:", calls)
    assert calls["owner"] == 1 and calls["team"] == 0

    r = run("4. three levels: report -> owner -> team, one round trip",
            '{ report(id: "r1") { title owner { name team { name region } } } }')
    assert r.data["report"]["owner"]["team"] == {"name": "platform", "region": "eu-west"}
    print("resolver calls:", calls)
    assert calls["team"] == 1
    print("   -> in REST this is three requests (/reports/r1, /users/u1, /teams/t1)")

    # The chain repeats per parent: 2 reports -> the owner resolver runs twice.
    before = calls["owner"]
    r = run("5. a LIST of objects: the child resolver runs once per parent",
            "{ reports { title owner { name } } }")
    assert len(r.data["reports"]) == 2
    print(f"owner resolver calls for 2 reports: {calls['owner'] - before}")
    assert calls["owner"] - before == 2
    print("   -> 1 + N resolver calls. With a database behind `owner` that is the N+1 problem (see ../labs/)")

    r = run("6. a nested field taking its own argument",
            '{ report(id: "r2") { summary(maxLength: 2) } }')
    assert r.data == {"report": {"summary": "Q2"}}

    print("\nOK")
