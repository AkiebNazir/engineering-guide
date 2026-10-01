"""
LAB 07 (advanced) - Federation: three subgraphs, a router, composition and a query plan
=======================================================================================
Federation lets several teams each own PART of one graph. Every team runs a normal GraphQL server
(a SUBGRAPH) that adds a few federation conventions; a ROUTER composes their schemas into one
SUPERGRAPH, and splits every client query into fetches against the subgraphs that own each field.

    client --one query--> ROUTER --fetch 1--> products  (Product @key(upc): name, price; topProducts)
                            |    --fetch 2--> reviews   (Product.reviews, Review, Review.author -> User stub)
                            |    --fetch 3--> accounts  (User @key(id): username)
                            +--> merges the three answers into the one response the client asked for

You will learn
  * ENTITIES: a type with @key(fields: "upc") can be extended by other subgraphs. The key is the
    foreign key between services; a subgraph that only knows the key holds a "stub" of it
  * the two federation fields every subgraph serves (strawberry.federation does it for you):
      _service { sdl }                         -> the router reads each subgraph's schema
      _entities(representations: [_Any!]!)     -> "here are N {__typename, upc} keys, give me
                                                  these fields for each" = resolve_reference
  * COMPOSITION: merge the SDLs, know which subgraph owns each Type.field, and FAIL the build when
    two subgraphs both define a non-key field without @shareable (a real composition error)
  * QUERY PLANNING: walk the client's selection; fields owned by the current subgraph stay in its
    fetch; fields owned elsewhere become a dependent _entities fetch, and the router adds the key
    fields it needs (upc, __typename) to the parent fetch
  * BATCHING across services for free: 5 products x 2 reviews each still costs 3 subgraph calls,
    one per plan node, not 1 + 5 + 10 (the N+1 problem of lab 03, one level up)
  * the router strips the helper keys it added, so the client sees exactly what it selected

This is a teaching router: no fragments, aliases or variables in client queries, and a sequence
plan only. Real routers (Apollo Router, Cosmo Router, Hive Gateway, Grafbase) handle all of it,
plus parallel fetches, @requires/@provides, and @override for moving a field between teams.

Needs   pip install strawberry-graphql
Run it  python 07_federation_subgraphs_and_router.py
"""
import json
import logging
import threading
import urllib.request
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import strawberry
from graphql import FieldNode, parse, print_ast
from graphql.language import ObjectTypeDefinitionNode, ObjectTypeExtensionNode

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)

# ======================================================================= subgraphs ===
# ---------- products team
PRODUCTS = {f"p{i}": {"upc": f"p{i}", "name": f"Product {i}", "price": 1000 + i} for i in range(1, 6)}


@strawberry.federation.type(keys=["upc"])
class Product:
    upc: str
    name: str
    price: int

    @classmethod
    def resolve_reference(cls, upc: str) -> "Product":
        return Product(**PRODUCTS[upc])


@strawberry.type
class ProductsQuery:
    @strawberry.field
    def top_products(self, first: int = 5) -> list[Product]:
        return [Product(**r) for r in list(PRODUCTS.values())[:first]]


products_schema = strawberry.federation.Schema(query=ProductsQuery)

# ---------- reviews team: extends Product with `reviews`, references User by key only
REVIEWS = [{"id": f"r{n}", "upc": f"p{(n % 5) + 1}", "body": f"review {n}", "author": f"u{(n % 3) + 1}"}
           for n in range(10)]


@strawberry.federation.type(keys=["id"])
class UserStub:                       # reviews only KNOWS a user's id; accounts owns the rest
    id: strawberry.ID


UserStub.__strawberry_definition__.name = "User"


@strawberry.type
class Review:
    id: strawberry.ID
    body: str
    author: UserStub


@strawberry.federation.type(keys=["upc"])
class ReviewedProduct:
    upc: str

    @strawberry.field
    def reviews(self) -> list[Review]:
        return [Review(id=r["id"], body=r["body"], author=UserStub(id=r["author"]))
                for r in REVIEWS if r["upc"] == self.upc]

    @classmethod
    def resolve_reference(cls, upc: str) -> "ReviewedProduct":
        return ReviewedProduct(upc=upc)


ReviewedProduct.__strawberry_definition__.name = "Product"


@strawberry.type
class ReviewsQuery:
    @strawberry.field
    def review_count(self) -> int:
        return len(REVIEWS)


reviews_schema = strawberry.federation.Schema(query=ReviewsQuery, types=[ReviewedProduct])

# ---------- accounts team
USERS = {f"u{i}": f"user-{i}" for i in range(1, 4)}


@strawberry.federation.type(keys=["id"])
class User:
    id: strawberry.ID
    username: str

    @classmethod
    def resolve_reference(cls, id: strawberry.ID) -> "User":
        return User(id=id, username=USERS[id])


@strawberry.type
class AccountsQuery:
    @strawberry.field
    def me(self) -> User:
        return User(id=strawberry.ID("u1"), username=USERS["u1"])


accounts_schema = strawberry.federation.Schema(query=AccountsQuery)


# ============================================================ subgraphs over HTTP ===
CALLS: list[tuple[str, int]] = []          # (subgraph, number of representations or 0)


def serve(name: str, schema) -> str:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            reps = (body.get("variables") or {}).get("representations")
            if "_service" not in body["query"]:
                CALLS.append((name, len(reps) if reps else 0))
            r = schema.execute_sync(body["query"], variable_values=body.get("variables"))
            out = json.dumps({"data": r.data, **({"errors": [e.message for e in r.errors]} if r.errors else {})}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *_):
            pass
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_port}/graphql"


def post(url: str, query: str, variables=None) -> dict:
    req = urllib.request.Request(url, json.dumps({"query": query, "variables": variables}).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        out = json.loads(r.read())
    assert "errors" not in out, out
    return out["data"]


# ==================================================================== composition ===
class CompositionError(Exception):
    pass


@dataclass
class Supergraph:
    owner: dict = field(default_factory=dict)       # (Type, field) -> subgraph
    ftype: dict = field(default_factory=dict)       # (Type, field) -> named return type
    keys: dict = field(default_factory=dict)        # (Type, subgraph) -> ["upc"]
    urls: dict = field(default_factory=dict)


def named(t) -> str:
    while hasattr(t, "type"):
        t = t.type
    return t.name.value


def compose(sdls: dict[str, str], urls: dict[str, str]) -> Supergraph:
    sg = Supergraph(urls=urls)
    for sub, sdl in sdls.items():
        for d in parse(sdl).definitions:
            if not isinstance(d, (ObjectTypeDefinitionNode, ObjectTypeExtensionNode)) or d.name.value.startswith("_"):
                continue
            t = d.name.value
            key_fields = [a.value.value.split() for dr in d.directives or [] if dr.name.value == "key"
                          for a in dr.arguments if a.name.value == "fields"]
            if key_fields:
                sg.keys[(t, sub)] = key_fields[0]
            for f in d.fields or []:
                name = f.name.value
                if name.startswith("_"):
                    continue
                sg.ftype[(t, name)] = named(f.type)
                is_key = any(name in k for (tt, _), k in sg.keys.items() if tt == t)
                shareable = any(dr.name.value == "shareable" for dr in f.directives or [])
                prev = sg.owner.get((t, name))
                if prev and prev != sub and not is_key and not shareable:
                    raise CompositionError(f"{t}.{name} is defined in both '{prev}' and '{sub}'; "
                                           f"mark it @shareable in both, or remove one")
                sg.owner.setdefault((t, name), sub)
    return sg


# ======================================================================= planning ===
@dataclass
class Fetch:
    subgraph: str
    type: str | None                   # None = a root query fetch; otherwise an _entities fetch
    path: list[str]                    # where in the response the entities live
    selection: str
    children: list["Fetch"] = field(default_factory=list)


def plan_selection(sg: Supergraph, sel_set, type_name: str, sub: str, path: list[str]):
    parts, deps, remote = [], [], {}
    for f in sel_set.selections:
        assert isinstance(f, FieldNode), "teaching router: fields only"
        name = f.name.value
        owner = sg.owner[(type_name, name)]
        local = owner == sub or name in sg.keys.get((type_name, sub), [])
        if not local:
            remote.setdefault(owner, []).append(f)
            continue
        args = f"({', '.join(print_ast(a) for a in f.arguments)})" if f.arguments else ""
        if f.selection_set:
            text, sub_deps = plan_selection(sg, f.selection_set, sg.ftype[(type_name, name)], sub, path + [name])
            parts.append(f"{name}{args} {{ {text} }}")
            deps += sub_deps
        else:
            parts.append(name + args)
    for owner, fields in remote.items():
        # the router needs the key to address this object in the other subgraph
        for k in ["__typename"] + sg.keys[(type_name, sub)]:
            if k not in parts:
                parts.append(k)
        fake = type("S", (), {"selections": fields})
        text, sub_deps = plan_selection(sg, fake, type_name, owner, path)
        deps.append(Fetch(owner, type_name, path, text, sub_deps))
    return " ".join(parts), deps


def plan(sg: Supergraph, query: str) -> list[Fetch]:
    op = parse(query).definitions[0]
    by_owner = {}
    for f in op.selection_set.selections:
        by_owner.setdefault(sg.owner[("Query", f.name.value)], []).append(f)
    fetches = []
    for sub, fields in by_owner.items():
        text, deps = plan_selection(sg, type("S", (), {"selections": fields}), "Query", sub, [])
        fetches.append(Fetch(sub, None, [], text, deps))
    return fetches


def show_plan(fetches, depth=0):
    for f in fetches:
        where = "Query" if f.type is None else f"_entities {f.type} at {'.'.join(f.path) or '(root)'}"
        print(f"   {'    ' * depth}{'then ' if depth else ''}Fetch({f.subgraph}) {where}: {{ {f.selection} }}")
        show_plan(f.children, depth + 1)


# ====================================================================== execution ===
def objects_at(data, path):
    """All objects reached by following `path`, flattening lists on the way."""
    level = [data]
    for key in path:
        nxt = []
        for obj in level:
            v = obj.get(key) if isinstance(obj, dict) else None
            nxt += v if isinstance(v, list) else ([v] if v is not None else [])
        level = nxt
    return [o for o in level if isinstance(o, dict)]


def run(sg: Supergraph, fetches, data):
    for f in fetches:
        if f.type is None:
            data.update(post(sg.urls[f.subgraph], "{ " + f.selection + " }"))
        else:
            targets = objects_at(data, f.path)
            key = sg.keys[(f.type, f.subgraph)]
            reps = [{"__typename": f.type, **{k: o[k] for k in key}} for o in targets]
            # one call for ALL objects at this path: the batching that kills N+1 across services
            q = ("query($representations: [_Any!]!) { _entities(representations: $representations) "
                 f"{{ ... on {f.type} {{ {f.selection} }} }} }}")
            got = post(sg.urls[f.subgraph], q, {"representations": reps})["_entities"]
            for target, extra in zip(targets, got):
                target.update(extra)
        run(sg, f.children, data)


def project(value, sel_set):
    """Give the client exactly what it selected: drop the __typename/key fields the router added."""
    if isinstance(value, list):
        return [project(v, sel_set) for v in value]
    if not isinstance(value, dict) or sel_set is None:
        return value
    return {f.name.value: project(value.get(f.name.value), f.selection_set) for f in sel_set.selections}


def execute(sg, query):
    data = {}
    run(sg, plan(sg, query), data)
    return project(data, parse(query).definitions[0].selection_set)


# =========================================================================== demo ===
def demo():
    urls = {"products": serve("products", products_schema), "reviews": serve("reviews", reviews_schema),
            "accounts": serve("accounts", accounts_schema)}

    print("== 1. each subgraph publishes its SDL via _service ==")
    sdls = {name: post(u, "{ _service { sdl } }")["_service"]["sdl"] for name, u in urls.items()}
    for name, sdl in sdls.items():
        keyed = [l.strip() for l in sdl.splitlines() if "@key" in l and l.startswith("type")]
        print(f"   {name:9s} {keyed}")
    assert 'type Product @key(fields: "upc")' in sdls["reviews"]

    print("\n== 2. composition: who owns each field of the supergraph ==")
    sg = compose(sdls, urls)
    for (t, f), sub in sorted(sg.owner.items()):
        print(f"   {t + '.' + f:22s} -> {sub}")
    assert sg.owner[("Product", "reviews")] == "reviews" and sg.owner[("User", "username")] == "accounts"

    print("\n   a fourth team tries to add Product.name too, without @shareable:")
    try:
        compose({**sdls, "inventory": 'type Product @key(fields: "upc") { upc: String! name: String! }'}, urls)
        raise AssertionError("composition should have failed")
    except CompositionError as e:
        print(f"   composition FAILED: {e}")

    query = "{ topProducts(first: 5) { name price reviews { body author { username } } } }"
    print(f"\n== 3. the query plan for\n   {query}")
    fetches = plan(sg, query)
    show_plan(fetches)
    assert fetches[0].subgraph == "products" and "upc" in fetches[0].selection
    assert fetches[0].children[0].subgraph == "reviews" and fetches[0].children[0].children[0].subgraph == "accounts"

    print("\n== 4. execute it ==")
    CALLS.clear()
    result = execute(sg, query)
    print("   " + json.dumps(result["topProducts"][0]))
    for sub, n in CALLS:
        print(f"   call -> {sub:9s} {'_entities x ' + str(n) if n else 'root query'}")
    first = result["topProducts"][0]
    assert set(first) == {"name", "price", "reviews"}, "helper keys stripped"
    assert first["reviews"][0]["author"]["username"].startswith("user-")
    n_reviews = sum(len(p["reviews"]) for p in result["topProducts"])
    assert [c[0] for c in CALLS] == ["products", "reviews", "accounts"] and CALLS[2][1] == n_reviews
    print(f"   {len(result['topProducts'])} products, {n_reviews} reviews, {n_reviews} authors -> "
          f"{len(CALLS)} subgraph calls (naive per-object fetching: {1 + 5 + n_reviews})")

    print("\n== 5. a query that touches one subgraph costs one fetch ==")
    CALLS.clear()
    out = execute(sg, "{ me { username } }")
    print(f"   {out}  calls={CALLS}")
    assert out == {"me": {"username": "user-1"}} and len(CALLS) == 1
    print("\nOK")


if __name__ == "__main__":
    demo()
