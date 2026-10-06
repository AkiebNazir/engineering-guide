"""
FOUNDATION LEVEL 01 - Many fields, and the scalar types they come in
========================================================================
Level 00 had one field of one type. A real Query object is a menu: several
fields, each with its own type and its own resolver. This level adds that
menu, and shows the single most surprising thing about GraphQL for anyone
coming from REST: the CLIENT decides which items to order, and only those
resolvers run. There is no "the /status response", there is only "whatever
you asked for this time".

GraphQL's built-in scalars are the leaf values - the points where the
response stops nesting: Int, Float, String, Boolean, ID. Everything else
(objects, lists, enums, custom scalars) is built out of them.

You will learn
  * a Query type is just a bag of independent fields, each with a resolver
  * the response mirrors the query: ask for two fields, get exactly two keys
  * resolvers for fields you did NOT ask for never run (watch the counters) -
    this is why one GraphQL endpoint can replace a dozen REST endpoints
  * the five built-in scalars (Int, Float, String, Boolean, ID) and what `!`
    means: `String!` promises "never null", `String` allows null
  * lists: `[String!]!` is "a non-null list of non-null strings"

Run it   python 01_multiple_fields_and_scalar_types.py
"""
import json
import logging

import strawberry

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

calls = {"name": 0, "version": 0, "uptime": 0, "healthy": 0, "node_id": 0, "regions": 0, "motd": 0}


@strawberry.type
class Query:
    # -> str          becomes  String!   (non-null: this field promises a value)
    @strawberry.field
    def name(self) -> str:
        calls["name"] += 1
        return "foundation-service"

    # -> int          becomes  Int!      (a 32-bit signed integer, by spec)
    @strawberry.field
    def version(self) -> int:
        calls["version"] += 1
        return 3

    # -> float        becomes  Float!
    @strawberry.field
    def uptime(self) -> float:
        calls["uptime"] += 1
        return 12.5

    # -> bool         becomes  Boolean!
    @strawberry.field
    def healthy(self) -> bool:
        calls["healthy"] += 1
        return True

    # strawberry.ID   becomes  ID!  - an opaque identifier. Serialized as a
    # string, but the point is "do not do arithmetic on this", not its shape.
    @strawberry.field
    def node_id(self) -> strawberry.ID:
        calls["node_id"] += 1
        return strawberry.ID("node-7")

    # -> list[str]    becomes  [String!]!  - a non-null list of non-null strings
    @strawberry.field
    def regions(self) -> list[str]:
        calls["regions"] += 1
        return ["eu-west", "us-east"]

    # -> str | None   becomes  String     - NULLABLE: a legitimate value here
    # is "there isn't one", with no error at all.
    @strawberry.field
    def motd(self) -> str | None:
        calls["motd"] += 1
        return None


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
    print("=== the schema, as SDL: seven fields, seven types ===")
    print(schema.as_str())

    # Ask for two fields out of seven. Only two resolvers run. In REST you
    # would have had to design an endpoint for exactly this combination (or
    # send all seven and let the client throw six away).
    r = run("1. ask for two fields - get exactly two keys back", "{ name version }")
    assert r.data == {"name": "foundation-service", "version": 3}
    print("resolver calls:", {k: v for k, v in calls.items() if v})
    assert calls["uptime"] == 0 and calls["regions"] == 0, "unrequested resolvers must not run"

    # A different client wants a different slice. Same schema, same endpoint,
    # no new server code - that is the whole selling point.
    r = run("2. a different client wants a different slice", "{ healthy regions nodeId }")
    assert r.data == {"healthy": True, "regions": ["eu-west", "us-east"], "nodeId": "node-7"}
    # Note `nodeId`: Python's snake_case node_id is exposed camelCase, which is
    # the GraphQL naming convention. The schema (SDL above) is the truth.

    # Types are real: the engine serializes each leaf according to the schema,
    # so an Int! field is a JSON number and never the string "3".
    r = run("3. types are enforced on the way out", "{ version uptime healthy }")
    assert r.data["version"] == 3 and isinstance(r.data["version"], int)
    assert r.data["uptime"] == 12.5 and isinstance(r.data["uptime"], float)
    assert r.data["healthy"] is True

    # A nullable field returning None is a SUCCESS, not a failure. Compare
    # level 06, where a nullable field fails for real.
    r = run("4. a nullable field with nothing to say -> null, and no error", "{ motd }")
    assert r.data == {"motd": None} and not r.errors
    print("   -> `String` may be null; `String!` may not. That difference drives level 06.")

    # Everything at once, to show all seven resolvers finally running.
    r = run("5. the whole menu", "{ name version uptime healthy nodeId regions motd }")
    assert len(r.data) == 7
    print("resolver calls:", calls)
    assert all(v >= 1 for v in calls.values())

    print("\nOK")
