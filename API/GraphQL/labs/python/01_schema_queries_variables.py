"""
LAB 01 (basic) - Your first GraphQL schema: types, queries, arguments, variables
================================================================================
You will learn
  * the schema is the contract:  types + fields + arguments  (printed below as SDL)
  * a query returns EXACTLY the fields you ask for - the response mirrors the query
  * resolvers only run for fields that were requested (see the counter)
  * variables ($id) instead of string-building queries; aliases; fragments; @include
  * errors are field-level: partial data + an `errors` array, and HTTP would still be 200
  * introspection: the API describes itself

Needs   pip install strawberry-graphql
Run it  python 01_schema_queries_variables.py
"""
import json
import logging

import strawberry

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)   # keep the demo output readable

AUTHORS = {1: "Ana", 2: "Ben"}
POSTS = [
    {"id": 10, "title": "Hello GraphQL", "author_id": 1, "tags": ["intro"]},
    {"id": 11, "title": "Schemas", "author_id": 2, "tags": ["types", "sdl"]},
    {"id": 12, "title": "Resolvers", "author_id": 1, "tags": []},
]
resolver_calls = {"author": 0}


@strawberry.type
class Author:
    id: int
    name: str


@strawberry.type
class Post:
    id: int
    title: str
    tags: list[str]
    author_id: strawberry.Private[int]          # internal column, not part of the API

    @strawberry.field
    def author(self) -> Author:                 # resolver: only runs if the client selects `author`
        resolver_calls["author"] += 1
        return Author(id=self.author_id, name=AUTHORS[self.author_id])


def to_post(row: dict) -> Post:
    return Post(id=row["id"], title=row["title"], tags=row["tags"], author_id=row["author_id"])


@strawberry.type
class Query:
    @strawberry.field
    def posts(self, tag: str | None = None) -> list[Post]:
        return [to_post(p) for p in POSTS if tag is None or tag in p["tags"]]

    @strawberry.field
    def post(self, id: int) -> Post | None:      # nullable: unknown id -> null, not an error
        row = next((p for p in POSTS if p["id"] == id), None)
        return to_post(row) if row else None

    @strawberry.field
    def flaky(self) -> str | None:              # nullable: a failure becomes null + an entry in `errors`
        raise RuntimeError("database is down")

    @strawberry.field
    def strict(self) -> str:                    # non-null: a failure cannot be null, so it nulls the PARENT
        raise RuntimeError("database is down")


schema = strawberry.Schema(Query)


def run(title: str, query: str, variables: dict | None = None):
    result = schema.execute_sync(query, variable_values=variables)
    print(f"\n# {title}\n{query.strip()}")
    if variables:
        print("variables:", variables)
    print("->", json.dumps({"data": result.data, **({"errors": [e.message for e in result.errors]} if result.errors else {})}))
    return result


if __name__ == "__main__":
    print("=== the schema, as SDL (this IS the contract) ===")
    print(schema.as_str())

    r = run("1. ask for two fields only - nothing more comes back", "{ posts { id title } }")
    assert r.data == {"posts": [{"id": 10, "title": "Hello GraphQL"}, {"id": 11, "title": "Schemas"}, {"id": 12, "title": "Resolvers"}]}
    assert resolver_calls["author"] == 0, "author resolver must NOT run when author was not requested"
    print("author resolver calls so far:", resolver_calls["author"])

    r = run("2. nested selection follows the relationship", "{ posts(tag: \"types\") { title author { name } } }")
    assert r.data["posts"][0]["author"]["name"] == "Ben"
    print("author resolver calls now:", resolver_calls["author"])

    r = run("3. variables + alias + fragment + directive",
            """query Compare($a: Int!, $b: Int!, $withAuthor: Boolean!) {
                 first:  post(id: $a) { ...card }
                 second: post(id: $b) { ...card }
               }
               fragment card on Post { title author @include(if: $withAuthor) { name } }""",
            {"a": 10, "b": 11, "withAuthor": False})
    assert "author" not in r.data["first"]

    r = run("4. unknown id is null (nullable field), not an error", "{ post(id: 999) { title } }")
    assert r.data == {"post": None} and not r.errors

    r = run("5. validation error: caught BEFORE any resolver runs", "{ posts { id nope } }")
    assert r.data is None and "Cannot query field 'nope'" in r.errors[0].message

    r = run("6a. resolver error on a NULLABLE field: partial data survives", "{ flaky  posts { id } }")
    assert r.data["flaky"] is None and len(r.data["posts"]) == 3 and r.errors

    r = run("6b. resolver error on a NON-NULL field: the null bubbles up and wipes `data`", "{ strict  posts { id } }")
    assert r.data is None and r.errors
    print("   -> `!` is a promise. Only promise what cannot fail, or one bad field blanks the response.")

    r = run("7. introspection: the API describes itself", '{ __type(name: "Post") { fields { name type { name kind } } } }')
    assert {f["name"] for f in r.data["__type"]["fields"]} == {"id", "title", "tags", "author"}
    print("\nOK")
