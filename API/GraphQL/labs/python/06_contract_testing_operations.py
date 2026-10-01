"""
LAB 06 (advanced) - Contract testing for GraphQL: registered operations, usage-aware schema checks
=================================================================================================
REST contract testing (REST lab 06) records "GET /orders/42 returns a body shaped like this".
GraphQL makes that easier, because every client already WRITES its contract down: the operation
document it sends names every field it reads. So the contract for a GraphQL API is
"the set of operations each client version sends, plus the response shape it relies on".

    web@3.4 ---register operations---> REGISTRY <---schema check--- products-api CI (proposed SDL)
    ios@7.1 ---register operations--->    |                               |
                                          +---- verify: run every op on the real server

You will learn
  * a pure SCHEMA DIFF (graphql-core's find_breaking_changes, the same idea as `buf breaking`)
    over-blocks and under-explains: removing a field NOBODY queries is "breaking" but harmless
  * a USAGE-AWARE check (what Apollo GraphOS / Hive / Inigo call operation checks): map each
    breaking change to a schema coordinate (Type.field) and block only if a live client uses it,
    and NAME that client
  * VALIDATING every registered operation against the proposed schema catches removed fields and
    newly-required arguments, but NOT an output field turning nullable - you need both checks
  * DANGEROUS changes (a new enum value) do not break validation but can crash exhaustive switches
  * PROVIDER VERIFICATION: replay every registered operation against the REAL server (in-process)
    and type-match the response - catches behaviour changes the schema cannot express
  * the deprecate -> watch usage -> remove workflow, driven by the registry, not by guessing

Needs   pip install strawberry-graphql   (graphql-core comes with it)
Run it  python 06_contract_testing_operations.py
"""
import logging
import re
from enum import Enum
from dataclasses import dataclass, field

import strawberry
from graphql import (TypeInfo, TypeInfoVisitor, Visitor, build_schema, find_breaking_changes,
                     find_dangerous_changes, parse, validate, visit)

logging.getLogger("strawberry.execution").setLevel(logging.CRITICAL)   # errors are printed by the demo

# ======================================================================= the schema ===
V1_SDL = """
enum Status { ACTIVE DISCONTINUED }

type Product {
  id: ID!
  name: String!
  price: Int!
  description: String!
  status: Status!
  weightGrams: Int
}

type Query {
  product(id: ID!): Product
  products(first: Int! = 10): [Product!]!
}
"""

# ============================================================ the real provider (v1) ===
PRODUCTS = {
    "1": {"id": "1", "name": "Kettle", "price": 3999, "description": "1.7 l, steel", "status": "ACTIVE", "weight": 1200},
    "2": {"id": "2", "name": "Toaster", "price": 2999, "description": "2 slots", "status": "DISCONTINUED", "weight": None},
}


@strawberry.enum
class Status(Enum):
    ACTIVE = "ACTIVE"
    DISCONTINUED = "DISCONTINUED"


@strawberry.type
class Product:
    id: strawberry.ID
    name: str
    price: int
    description: str
    status: Status
    weight_grams: int | None


def to_product(row) -> Product:
    return Product(id=strawberry.ID(row["id"]), name=row["name"], price=row["price"],
                   description=row["description"], status=Status(row["status"]), weight_grams=row["weight"])


def make_provider(missing_raises: bool = False) -> strawberry.Schema:
    """missing_raises=True is 'v1.1': a refactor that turns 'not found' from null into an error."""
    @strawberry.type
    class Query:
        @strawberry.field
        def product(self, id: strawberry.ID) -> Product | None:
            if id not in PRODUCTS:
                if missing_raises:
                    raise ValueError(f"product {id} not found")
                return None
            return to_product(PRODUCTS[id])

        @strawberry.field
        def products(self, first: int = 10) -> list[Product]:
            return [to_product(r) for r in list(PRODUCTS.values())[:first]]
    return strawberry.Schema(query=Query)


# ==================================================================== the registry ===
@dataclass
class Operation:
    client: str                 # "web@3.4"
    name: str
    document: str
    variables: dict = field(default_factory=dict)
    expected: dict | None = None   # an EXAMPLE response; matched by type, not by value
    exhaustive_enums: bool = False  # the client has a `switch` with no default branch


REGISTRY: list[Operation] = [
    Operation("web@3.4", "ProductPage", """
        query ProductPage($id: ID!) { product(id: $id) { id name price description } }""",
              {"id": "1"}, {"data": {"product": {"id": "9", "name": "x", "price": 1, "description": "d"}}}),
    Operation("web@3.4", "MissingProduct", """
        query MissingProduct($id: ID!) { product(id: $id) { id } }""",
              {"id": "nope"}, {"data": {"product": None}}),
    Operation("ios@7.1", "Catalogue", """
        query Catalogue { products { id name description status } }""",
              {}, {"data": {"products": [{"id": "9", "name": "x", "description": "d", "status": "ACTIVE"}]}},
              exhaustive_enums=True),
]


# ============================================================== analysing operations ===
def coordinates(schema, document: str) -> set[str]:
    """Every schema coordinate (Type.field) an operation touches, resolved through TypeInfo so
    fragments and aliases are handled: `p: product { ... }` still counts as Query.product."""
    used: set[str] = set()
    type_info = TypeInfo(schema)

    class Collect(Visitor):
        def enter_field(self, node, *_):
            parent = type_info.get_parent_type()
            if parent is not None:
                used.add(f"{parent.name}.{node.name.value}")

    visit(parse(document), TypeInfoVisitor(type_info, Collect()))
    return used


COORD_RE = re.compile(r"^(\w+)\.(\w+)")        # "Product.price was removed." -> Product.price


def check(proposed_sdl: str, registry: list[Operation], base_sdl: str = V1_SDL) -> tuple[bool, list[str]]:
    """The CI gate a provider runs on every schema change. base_sdl = what is in production now."""
    old, new = build_schema(base_sdl), build_schema(proposed_sdl)
    lines, ok = [], True
    usage = [(op, coordinates(old, op.document)) for op in registry]

    for ch in find_breaking_changes(old, new):
        m = COORD_RE.match(ch.description)
        coord = f"{m.group(1)}.{m.group(2)}" if m else ch.description
        users = sorted({op.client + " " + op.name for op, used in usage if coord in used})
        if users:
            ok = False
            lines.append(f"BREAKING {ch.type.name:22s} {ch.description}  used by: {', '.join(users)}")
        else:
            lines.append(f"unused   {ch.type.name:22s} {ch.description}  (no registered operation reads it)")

    for ch in find_dangerous_changes(old, new):
        enum_change = ch.type.name == "VALUE_ADDED_TO_ENUM"
        affected = [op.client for op in registry if op.exhaustive_enums] if enum_change else []
        lines.append(f"warning  {ch.type.name:22s} {ch.description}"
                     + (f"  exhaustive switch in: {', '.join(affected)}" if affected else ""))

    for op in registry:                               # the second, independent check
        errors = validate(new, parse(op.document))
        if errors:
            ok = False
            lines.append(f"INVALID  {op.client} {op.name}: {errors[0].message}")
    return ok, lines


# ============================================================ provider verification ===
def kind(v) -> str:
    return {bool: "boolean", int: "number", float: "number", str: "string", list: "array",
            dict: "object", type(None): "null"}[type(v)]


def type_match(expected, actual, path="$") -> list[str]:
    """Pact-style: same keys and same JSON kinds; values may differ. Extra keys are fine."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected object, got {kind(actual)}"]
        errs = []
        for k, v in expected.items():
            if k not in actual:
                errs.append(f"{path}.{k}: missing")
            else:
                errs += type_match(v, actual[k], f"{path}.{k}")
        return errs
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{path}: expected array, got {kind(actual)}"]
        return [e for i, a in enumerate(actual) for e in type_match(expected[0], a, f"{path}[{i}]")] if expected else []
    return [] if kind(expected) == kind(actual) else [f"{path}: expected {kind(expected)}, got {kind(actual)}"]


def verify(provider: strawberry.Schema, registry: list[Operation]) -> dict[str, list[str]]:
    out = {}
    for op in registry:
        result = provider.execute_sync(op.document, variable_values=op.variables)
        actual = {"data": result.data}
        errs = [f"$.errors: {e.message}" for e in (result.errors or [])]
        out[f"{op.client} {op.name}"] = errs + type_match(op.expected, actual)
    return out


# ============================================================================ demo ===
def show(title, proposed):
    ok, lines = check(proposed, REGISTRY)
    print(f"\n-- {title} --")
    for line in lines or ["no changes that affect clients"]:
        print("   " + line)
    print(f"   => {'SHIP' if ok else 'BLOCKED'}")
    return ok, lines


def demo():
    print("== 0. the real server's schema IS the registered schema ==")
    provider = make_provider()
    served = build_schema(str(provider))
    drift = find_breaking_changes(build_schema(V1_SDL), served) + find_breaking_changes(served, build_schema(V1_SDL))
    print(f"   strawberry printed {len(str(provider).splitlines())} SDL lines; drift vs V1_SDL: {drift or 'none'}")
    assert not drift

    print("\n== 1. what each registered operation actually uses ==")
    for op in REGISTRY:
        print(f"   {op.client:8s} {op.name:15s} {sorted(coordinates(build_schema(V1_SDL), op.document))}")

    print("\n== 2. proposed schema changes, checked against real usage ==")
    ok, _ = show("A. add priceMoney, deprecate price (expand step)", V1_SDL.replace(
        "  price: Int!", '  price: Int! @deprecated(reason: "use priceMoney")\n  priceMoney: Money!')
        + "type Money { amount: Int!  currency: String! }")
    assert ok

    ok, lines = show("B. remove Product.price", V1_SDL.replace("  price: Int!\n", ""))
    assert not ok and any("web@3.4 ProductPage" in l and l.startswith("BREAKING") for l in lines)

    ok, lines = show("C. remove Product.weightGrams (a diff tool calls this breaking)",
                     V1_SDL.replace("  weightGrams: Int\n", ""))
    assert ok and lines[0].startswith("unused")
    print("   a plain `schema diff` gate would have blocked this for no one.")

    ok, lines = show("D. products(first: Int!) loses its default", V1_SDL.replace("first: Int! = 10", "first: Int!"))
    assert not ok and any(l.startswith("INVALID  ios@7.1 Catalogue") for l in lines)

    ok, lines = show("E. description becomes nullable (String! -> String)",
                     V1_SDL.replace("description: String!", "description: String"))
    assert not ok and not any(l.startswith("INVALID") for l in lines)
    print("   every operation still VALIDATES - only the usage-aware diff catches this one.")
    print("   (a Swift/Kotlin client generated from String! would crash on the first null)")

    ok, lines = show("F. add Status.ARCHIVED", V1_SDL.replace("DISCONTINUED }", "DISCONTINUED ARCHIVED }"))
    assert ok and any(l.startswith("warning") and "ios@7.1" in l for l in lines)

    print("\n== 3. provider verification: replay every operation on the real server ==")
    for name, errs in verify(provider, REGISTRY).items():
        print(f"   v1.0 {name:25s} {'PASS' if not errs else 'FAIL ' + '; '.join(errs)}")
        assert not errs
    results = verify(make_provider(missing_raises=True), REGISTRY)
    for name, errs in results.items():
        print(f"   v1.1 {name:25s} {'PASS' if not errs else 'FAIL ' + '; '.join(errs)}")
    assert results["web@3.4 MissingProduct"] and not results["web@3.4 ProductPage"]
    print("   v1.1 has the same SDL (every schema check passes) but turned 'not found' into an")
    print("   error. Only replaying the consumer's operation shows that the web app's 404 page broke.")

    print("\n== 4. deprecate -> watch usage -> remove ==")
    web35 = Operation("web@3.5", "ProductPage", """
        query ProductPage($id: ID!) { product(id: $id) { id name priceMoney { amount currency } description } }""")
    expanded = V1_SDL.replace("  price: Int!", '  price: Int! @deprecated(reason: "use priceMoney")\n  priceMoney: Money!') \
        + "type Money { amount: Int!  currency: String! }"
    contracted = expanded.replace('  price: Int! @deprecated(reason: "use priceMoney")\n', "")
    # web@3.4 is retired from the registry once analytics shows no traffic from it
    live = [op for op in REGISTRY if op.client != "web@3.4"] + [web35]
    ok_before, _ = check(contracted, REGISTRY + [web35], base_sdl=expanded)
    ok_after, _ = check(contracted, live, base_sdl=expanded)
    print(f"   remove price while web@3.4 is live? {'yes' if ok_before else 'NO'}")
    print(f"   remove price after web@3.4 retired? {'yes' if ok_after else 'NO'}")
    assert not ok_before and ok_after
    print("\nOK")


if __name__ == "__main__":
    demo()
