"""
LEVEL 05 (advanced) - namedtuple: field access, ._asdict(), ._replace(), immutability
=========================================================================================
You will learn
  * creating a namedtuple type and constructing instances positionally or by keyword
  * accessing fields by name (self-documenting) instead of by numeric index
  * ._asdict() for a dict view, and ._replace() to get a "changed copy" of an immutable value

Run: python level_05_namedtuple_pattern.py
"""
from collections import namedtuple

Employee = namedtuple("Employee", ["name", "role", "salary"])

if __name__ == "__main__":
    # ---- construction: positional or keyword, both work -------------------
    alice = Employee("Alice", "Engineer", 95000)
    bob = Employee(name="Bob", role="Manager", salary=110000)

    # ---- field access by NAME, not by opaque index -------------------------
    assert alice.name == "Alice"
    assert alice.role == "Engineer"
    # it's still a real tuple underneath -- index access also works
    assert alice[0] == "Alice" and alice[2] == 95000
    assert tuple(alice) == ("Alice", "Engineer", 95000)

    # ---- ._asdict(): a dict view of the fields -----------------------------
    as_dict = alice._asdict()
    assert as_dict == {"name": "Alice", "role": "Engineer", "salary": 95000}
    assert list(as_dict.keys()) == ["name", "role", "salary"]   # field order preserved

    # ---- ._replace(): immutability means "changes" are new instances ------
    promoted = alice._replace(role="Senior Engineer", salary=115000)
    assert promoted.role == "Senior Engineer"
    assert alice.role == "Engineer"          # the original is untouched
    assert promoted is not alice             # a genuinely different object

    # ---- ._fields: introspect the schema itself ----------------------------
    assert Employee._fields == ("name", "role", "salary")

    # namedtuples compare by VALUE, like regular tuples
    assert Employee("Alice", "Engineer", 95000) == alice
    assert bob != alice

    print("OK")
