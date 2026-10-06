"""
LEVEL 05 (core) - functools.singledispatch: type-based dispatch
===================================================================
You will learn
  * how @singledispatch turns one generic function into a dispatcher that
    picks an implementation based on the type of its first argument
  * registering specializations with @<generic>.register(SomeType)
  * that singledispatch respects the MRO: a subclass without its own
    registration falls back to its parent's implementation
  * this replaces a chain of `if isinstance(x, ...)` checks with a table
    the interpreter looks up for you

Run: python level_05_singledispatch.py
"""
from functools import singledispatch


class Shape:
    pass


class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius


class Square(Shape):
    def __init__(self, side: float):
        self.side = side


class UnitSquare(Square):
    """A Square subclass that registers no specialization of its own."""

    def __init__(self):
        super().__init__(side=1.0)


@singledispatch
def describe(value) -> str:
    """The generic / fallback implementation, used for any unregistered type."""
    return f"unknown value: {value!r}"


@describe.register
def _(value: int) -> str:
    return f"an int: {value}"


@describe.register
def _(value: str) -> str:
    return f"a string of length {len(value)}"


@describe.register
def _(value: Circle) -> str:
    area = 3.14159 * value.radius ** 2
    return f"a circle with area {area:.2f}"


@describe.register
def _(value: Square) -> str:
    return f"a square with area {value.side ** 2}"


def main() -> None:
    # --- dispatch by the concrete type of the first argument --------------
    assert describe(42) == "an int: 42"
    assert describe("hi") == "a string of length 2"
    assert describe(Circle(2)) == "a circle with area 12.57"
    assert describe(Square(3)) == "a square with area 9"

    # --- an unregistered type falls back to the generic implementation ----
    assert describe(3.14) == "unknown value: 3.14"
    assert describe([1, 2]) == "unknown value: [1, 2]"

    # --- MRO fallback: UnitSquare has no registration of its own, but it
    # IS-A Square, so singledispatch walks the MRO and finds Square's impl.
    assert describe(UnitSquare()) == "a square with area 1.0"

    # --- the registry is inspectable: real types map to real functions ----
    assert int in describe.registry
    assert str in describe.registry
    assert Circle in describe.registry
    # UnitSquare was never registered directly -- confirming the MRO point.
    assert UnitSquare not in describe.registry

    print("OK")


if __name__ == "__main__":
    main()
