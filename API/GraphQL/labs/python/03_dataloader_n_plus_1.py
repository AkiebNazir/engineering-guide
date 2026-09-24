"""
LAB 03 (advanced) - The N+1 problem and DataLoader
==================================================
You will learn
  * WHY GraphQL creates N+1 queries: each Post.author resolver runs once per post, independently
  * how a DataLoader fixes it: collect every .load(key) made in one event-loop tick,
    call ONE batch function, hand each caller its own result
  * the two rules:  (1) the batch function returns results in the SAME ORDER as the keys
                    (2) build loaders PER REQUEST - a global loader would cache one user's data for another
  * a free bonus: duplicate keys in a request hit the database once (per-request cache)

    naive:        posts query (1)  +  author query per post (N)        = 1 + N round trips
    with loader:  posts query (1)  +  ONE  "WHERE id IN (...)"  query  = 2 round trips

Needs   pip install strawberry-graphql
Run it  python 03_dataloader_n_plus_1.py
"""
import asyncio
import logging

import strawberry
from strawberry.dataloader import DataLoader

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

AUTHOR_TABLE = {i: {"id": i, "name": f"author-{i}"} for i in range(1, 6)}          # 5 distinct authors
POST_TABLE = [{"id": n, "title": f"post-{n}", "author_id": (n % 5) + 1} for n in range(1, 51)]   # 50 posts
sql_log: list[str] = []          # every "database round trip" is recorded here


# ---------------------------------------------------------------- fake DB ---
async def db_get_author(author_id: int) -> dict:
    sql_log.append(f"SELECT * FROM authors WHERE id = {author_id}")
    return AUTHOR_TABLE[author_id]


async def db_get_authors(ids: list[int]) -> list[dict]:
    sql_log.append(f"SELECT * FROM authors WHERE id IN {tuple(sorted(set(ids)))}")
    return [AUTHOR_TABLE[i] for i in set(ids)]


# ---------------------------------------------------------------- schema ----
@strawberry.type
class Author:
    id: int
    name: str


async def load_authors(keys: list[int]) -> list[Author]:
    """Batch function. `keys` may contain duplicates; return ONE result PER KEY, in the SAME ORDER."""
    rows = await db_get_authors(keys)
    by_id = {r["id"]: Author(**r) for r in rows}
    return [by_id[k] for k in keys]


@strawberry.type
class NaivePost:
    id: int
    title: str
    author_id: strawberry.Private[int]

    @strawberry.field
    async def author(self) -> Author:
        return Author(**await db_get_author(self.author_id))            # 1 query per post!


@strawberry.type
class BatchedPost:
    id: int
    title: str
    author_id: strawberry.Private[int]

    @strawberry.field
    async def author(self, info: strawberry.Info) -> Author:
        return await info.context["author_loader"].load(self.author_id)   # queued, resolved in one batch


@strawberry.type
class Query:
    @strawberry.field
    async def naive_posts(self) -> list[NaivePost]:
        sql_log.append("SELECT * FROM posts LIMIT 50")
        return [NaivePost(id=p["id"], title=p["title"], author_id=p["author_id"]) for p in POST_TABLE]

    @strawberry.field
    async def batched_posts(self) -> list[BatchedPost]:
        sql_log.append("SELECT * FROM posts LIMIT 50")
        return [BatchedPost(id=p["id"], title=p["title"], author_id=p["author_id"]) for p in POST_TABLE]


schema = strawberry.Schema(Query)


async def main():
    q = "{ %s { title author { name } } }"

    sql_log.clear()
    r = await schema.execute(q % "naivePosts")
    print(f"NAIVE   : {len(sql_log):>2} database round trips for 50 posts  (1 + N)")
    naive_count = len(sql_log)
    assert not r.errors and naive_count == 51

    sql_log.clear()
    ctx = {"author_loader": DataLoader(load_fn=load_authors)}          # NEW loader for THIS request
    r = await schema.execute(q % "batchedPosts", context_value=ctx)
    print(f"DATALOADER: {len(sql_log):>2} database round trips for 50 posts")
    for line in sql_log:
        print("     ", line)
    assert not r.errors and len(sql_log) == 2, sql_log
    assert r.data["batchedPosts"][0]["author"]["name"] == "author-2"      # results reached the right posts

    print("\n-- rule 2: a loader shared across requests caches across requests --")
    name_of_post_5 = lambda res: [p["author"]["name"] for p in res.data["batchedPosts"] if p["title"] == "post-5"][0]
    shared = DataLoader(load_fn=load_authors)                          # post-5 is written by author 1
    r1 = await schema.execute(q % "batchedPosts", context_value={"author_loader": shared})
    AUTHOR_TABLE[1] = {"id": 1, "name": "RENAMED"}                     # data changes between two requests...
    r2 = await schema.execute(q % "batchedPosts", context_value={"author_loader": shared})
    r3 = await schema.execute(q % "batchedPosts", context_value={"author_loader": DataLoader(load_fn=load_authors)})
    print(f"request 1 (shared loader): {name_of_post_5(r1)}")
    print(f"request 2 (shared loader): {name_of_post_5(r2)}   <- STALE, served from the old request's cache")
    print(f"request 3 (fresh loader) : {name_of_post_5(r3)}")
    assert name_of_post_5(r2) == "author-1" and name_of_post_5(r3) == "RENAMED"
    print("   => always create the DataLoader inside the per-request context (in real apps stale = someone else's data).")
    print("\nOK")


asyncio.run(main())
