"""
FOUNDATION LEVEL 05 - Mutations: changing something, and refusing bad input
==============================================================================
Everything so far only READ. A mutation is how a client changes state. In
REST the verb carried that meaning (GET vs POST/PUT/DELETE, level 06 of
REST/Foundation). GraphQL has no verbs: every request is one HTTP POST, and
what makes an operation a write is that it lives on the `Mutation` type
instead of `Query`. That is a CONVENTION the engine enforces in exactly one
way - mutation fields run one after another, in the order written, while
query fields may run in parallel.

Two kinds of validation show up here, and telling them apart is the point:
  1. SCHEMA validation - "title is required, and must be a String". The
     engine does this against your input type, before your resolver runs.
     You write zero code for it.
  2. BUSINESS validation - "title must not be blank, and must be under 40
     characters". No type system can express that, so your resolver does it
     and returns an error itself.

You will learn
  * how to declare a Mutation type and an `input` type for its argument
  * why writes take a single `input:` object rather than ten loose arguments
  * that missing/wrong-typed input fields are rejected by the schema for free
  * that your own rules live in the resolver, and how to fail clearly from there
  * that a mutation returns a normal object type, so the client can select
    fields off the thing it just created - no second round trip

Run it   python 05_mutations_and_input_validation.py
"""
import json
import logging

import strawberry

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

POSTS: dict[str, dict] = {}
next_id = {"n": 1}


@strawberry.type
class Post:
    id: strawberry.ID
    title: str
    body: str | None


# An `input` type is a separate kind of type from an object type: it can only
# contain scalars and other inputs, never fields with resolvers. Grouping the
# write's fields into one input object means adding a field later does not
# change the mutation's signature for existing clients.
@strawberry.input
class NewPost:
    title: str               # required: title: String!
    body: str | None = None  # optional: body: String = null


@strawberry.type
class Query:
    @strawberry.field
    def posts(self) -> list[Post]:
        return [Post(id=strawberry.ID(p["id"]), title=p["title"], body=p["body"]) for p in POSTS.values()]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_post(self, input: NewPost) -> Post:
        # By this line the engine has already guaranteed: `input` exists,
        # `input.title` is present, and it is a str. Everything below is a
        # rule the TYPE SYSTEM CANNOT EXPRESS, so it has to live here.
        title = input.title.strip()
        if not title:
            # Raising from a resolver is how you report a business rule
            # failure. It lands in `errors[]` with this field's path.
            raise ValueError("title must not be blank")
        if len(title) > 40:
            raise ValueError("title must be 40 characters or fewer")

        post_id = f"p{next_id['n']}"
        next_id["n"] += 1
        POSTS[post_id] = {"id": post_id, "title": title, "body": input.body}
        # Returning the created object lets the client select fields off it in
        # the same request - REST's "201 + Location, now go GET it" in one step.
        return Post(id=strawberry.ID(post_id), title=title, body=input.body)

    @strawberry.mutation
    def delete_post(self, id: strawberry.ID) -> bool:
        return POSTS.pop(str(id), None) is not None


schema = strawberry.Schema(Query, Mutation)


def run(title: str, query: str, variables: dict | None = None):
    result = schema.execute_sync(query, variable_values=variables)
    payload = {"data": result.data}
    if result.errors:
        payload["errors"] = [{"message": e.message, "path": e.path} for e in result.errors]
    print(f"\n# {title}")
    print(f"query    : {' '.join(query.split())}")
    if variables:
        print(f"variables: {json.dumps(variables)}")
    print(f"response : {json.dumps(payload)}")
    return result


CREATE = """
mutation Create($input: NewPost!) {
  createPost(input: $input) { id title body }
}
"""

if __name__ == "__main__":
    print("=== the schema, as SDL: note `input NewPost` is its own kind of type ===")
    print(schema.as_str())

    r = run("1. a write that succeeds, selecting fields off the new object",
            CREATE, {"input": {"title": "Hello GraphQL", "body": "first post"}})
    assert r.data["createPost"]["title"] == "Hello GraphQL"
    assert r.data["createPost"]["id"] == "p1"

    r = run("2. it really changed state: query it back", "{ posts { id title } }")
    assert r.data == {"posts": [{"id": "p1", "title": "Hello GraphQL"}]}

    # Kind 1: the schema rejects it. Our resolver never ran.
    before = len(POSTS)
    r = run("3. required input field missing -> SCHEMA validation, resolver never runs",
            CREATE, {"input": {"body": "no title here"}})
    assert r.data is None
    assert "Field 'title' of required type 'String!' was not provided" in r.errors[0].message
    assert len(POSTS) == before, "nothing was created"

    r = run("4. input field of the wrong type -> same mechanism, same free rejection",
            CREATE, {"input": {"title": 7}})
    assert r.data is None and "String cannot represent a non string value" in r.errors[0].message
    assert len(POSTS) == before

    # Kind 2: schema-valid, but against OUR rules. The resolver must say so.
    r = run("5. schema-valid but blank -> BUSINESS validation, from inside the resolver",
            CREATE, {"input": {"title": "   "}})
    assert r.data is None  # createPost is Post! (non-null), so the null wipes `data` - see level 06
    assert r.errors[0].message == "title must not be blank"
    assert r.errors[0].path == ["createPost"], "the error names the field that failed"
    assert len(POSTS) == before, "nothing was created"
    print("   -> the type system can say 'a String is required'; only you can say 'not whitespace'")

    r = run("6. the other business rule", CREATE, {"input": {"title": "x" * 41}})
    assert r.errors[0].message == "title must be 40 characters or fewer"

    # Mutation fields are executed SERIALLY, top to bottom - the reason writes
    # live on their own type at all. Here the delete is guaranteed to happen
    # after the create, so `remaining` is observed afterwards.
    r = run("7. two writes in one request run in order, top to bottom",
            """mutation {
                 a: createPost(input: {title: "second"}) { id }
                 removed: deletePost(id: "p1")
               }""")
    assert r.data["a"]["id"] == "p2" and r.data["removed"] is True

    r = run("8. the state after both writes", "{ posts { id title } }")
    assert r.data == {"posts": [{"id": "p2", "title": "second"}]}

    print("\nOK")
