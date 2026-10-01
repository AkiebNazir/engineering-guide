"""
================================================================================
LLD 010 · Unix `find` / File Search                                [Tier 1]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design an API like Unix `find` over an in-memory file tree, built so that new
search criteria can be added without modifying existing code.

The interviewer says: "Design the find command. I want files over 5 MB, or
all XML files — and next week someone will add a new filter." Then, near the
end: "Now accept the real command-line syntax."

REQUIREMENTS
------------
  1. Tree
       File(name, size, modified=0.0)      Directory(name, modified=0.0)
       Directory.add(node) -> node         (FindError if the name exists)
       node.path -> "/a/b/c" ("/" for the root); node.is_dir
       FileSystem(): .root, mkdir(path) (creates parents; returns Directory),
       add_file(path, size, modified=0.0) -> File, get(path) -> Node.
       FindError for missing paths or paths that go through a file.
  2. Specifications (frozen dataclasses — equal ASTs must compare equal):
       Name(pattern, ignore_case=False)   glob on the node name
       Ext(extension)                      files only
       TypeIs("f" | "d")
       SizeGt(n), SizeLt(n), SizeEq(n)     files only (directories never match)
       ModifiedAfter(t)                    modified > t
       Empty()                             directory with no children, or 0-byte file
       Where(predicate, label="where")
       And(left, right), Or(left, right), Not(inner)
     Every spec has matches(node) -> bool, and `a & b`, `a | b`, `~a` build
     And/Or/Not. Helpers: name, iname, ext, is_file, is_dir, size_gt, size_lt,
     modified_after, empty.
  3. find(start, spec=<match all>, max_depth=None, prune=None) -> a LAZY
     iterator. Pre-order; children visited in sorted name order; the start node
     is yielded if it matches; max_depth=0 means only the start node.
     Directories (other than start) matching `prune` are neither yielded nor
     entered. Must handle trees deeper than Python's recursion limit.
  4. parse(tokens) -> Spec for find-style arguments:
       -name PAT   -iname PAT   -type f|d   -size [+|-]N[c|k|M|G]   -empty
       ! / -not    -a / -and (also implicit)    -o / -or    ( ... )
     Precedence: ! tightest, then AND, then OR. "+N" -> SizeGt, "-N" ->
     SizeLt, "N" -> SizeEq; k=1024, M=1024^2, G=1024^3. Syntax errors -> FindError.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * How does a new filter get added without touching existing classes?
  * Why an AST of specs rather than lambdas?
  * Recursion vs explicit stack; list vs generator.
  * Operator precedence in the parser.

FOLLOW-UPS TO PREPARE
---------------------
  real filesystem with symlink loops · parallel search · indexing for repeated
  queries · -exec actions · top-k largest files.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator


class FindError(Exception): ...


class Node:
    def __init__(self, name: str, modified: float = 0.0) -> None:
        self.name = name
        self.modified = modified
        self.parent: Directory | None = None

    @property
    def path(self) -> str:
        raise NotImplementedError

    @property
    def is_dir(self) -> bool:
        return False


class File(Node):
    def __init__(self, name: str, size: int, modified: float = 0.0) -> None:
        super().__init__(name, modified)
        self.size = size


class Directory(Node):
    def __init__(self, name: str, modified: float = 0.0) -> None:
        super().__init__(name, modified)
        self.children: dict[str, Node] = {}

    @property
    def is_dir(self) -> bool:
        return True

    def add(self, node: Node) -> Node:
        raise NotImplementedError


class FileSystem:
    def __init__(self) -> None:
        self.root = Directory("")

    def get(self, path: str) -> Node: raise NotImplementedError
    def mkdir(self, path: str) -> Directory: raise NotImplementedError
    def add_file(self, path: str, size: int, modified: float = 0.0) -> File: raise NotImplementedError


class Spec:
    def matches(self, node: Node) -> bool: raise NotImplementedError
    def __and__(self, other: Spec) -> Spec: raise NotImplementedError
    def __or__(self, other: Spec) -> Spec: raise NotImplementedError
    def __invert__(self) -> Spec: raise NotImplementedError


@dataclass(frozen=True)
class And(Spec):
    left: Spec
    right: Spec


@dataclass(frozen=True)
class Or(Spec):
    left: Spec
    right: Spec


@dataclass(frozen=True)
class Not(Spec):
    inner: Spec


@dataclass(frozen=True)
class Name(Spec):
    pattern: str
    ignore_case: bool = False


@dataclass(frozen=True)
class Ext(Spec):
    extension: str


@dataclass(frozen=True)
class TypeIs(Spec):
    kind: str


@dataclass(frozen=True)
class SizeGt(Spec):
    bytes_: int


@dataclass(frozen=True)
class SizeLt(Spec):
    bytes_: int


@dataclass(frozen=True)
class SizeEq(Spec):
    bytes_: int


@dataclass(frozen=True)
class ModifiedAfter(Spec):
    timestamp: float


@dataclass(frozen=True)
class Empty(Spec):
    pass


@dataclass(frozen=True)
class Where(Spec):
    predicate: Callable[[Node], bool]
    label: str = "where"


def name(pattern: str) -> Spec: return Name(pattern)
def iname(pattern: str) -> Spec: return Name(pattern, ignore_case=True)
def ext(extension: str) -> Spec: return Ext(extension)
def is_file() -> Spec: return TypeIs("f")
def is_dir() -> Spec: return TypeIs("d")
def size_gt(n: int) -> Spec: return SizeGt(n)
def size_lt(n: int) -> Spec: return SizeLt(n)
def modified_after(t: float) -> Spec: return ModifiedAfter(t)
def empty() -> Spec: return Empty()


def find(start: Node, spec: Spec | None = None, max_depth: int | None = None,
         prune: Spec | None = None) -> Iterator[Node]:
    raise NotImplementedError


def parse(tokens: list[str]) -> Spec:
    raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _raises(exc, fn) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def _sample() -> FileSystem:
    fs = FileSystem()
    fs.add_file("/src/app.py", 1200, modified=50)
    fs.add_file("/src/util.py", 0, modified=10)
    fs.add_file("/src/test_app.py", 800, modified=60)
    fs.add_file("/src/README.MD", 300, modified=20)
    fs.add_file("/data/big.csv", 5 * 1024 * 1024, modified=100)
    fs.add_file("/data/archive/old.csv", 2048, modified=1)
    fs.mkdir("/empty_dir")
    fs.add_file("/node_modules/lib/index.js", 100, modified=30)
    return fs


def _paths(nodes) -> list[str]:
    return [n.path for n in nodes]


def run_tests() -> bool:
    all_ok = True
    fs = _sample()
    print("--- composite tree ---")
    all_ok &= _check("paths resolve", fs.get("/data/archive/old.csv").size == 2048
                     and fs.get("/data/archive").path == "/data/archive")
    all_ok &= _check("duplicate file rejected", _raises(FindError, lambda: fs.add_file("/src/app.py", 1)))
    all_ok &= _check("path through a file rejected", _raises(FindError, lambda: fs.add_file("/src/app.py/x", 1)))
    all_ok &= _check("missing path", _raises(FindError, lambda: fs.get("/nope")))

    print("\n--- specifications ---")
    py_not_tests = ext(".py") & ~name("test_*")
    all_ok &= _check("python files that aren't tests, pre-order, sorted by name",
                     _paths(find(fs.root, py_not_tests)) == ["/src/app.py", "/src/util.py"])
    big_or_old = is_file() & (size_gt(1024 * 1024) | ~modified_after(5))
    all_ok &= _check("files over 1 MB OR modified at/before t=5",
                     _paths(find(fs.root, big_or_old)) == ["/data/archive/old.csv", "/data/big.csv"])
    all_ok &= _check("iname is case-insensitive, name is not",
                     _paths(find(fs.root, iname("readme.md"))) == ["/src/README.MD"]
                     and list(find(fs.root, name("readme.md"))) == [])
    all_ok &= _check("empty matches the empty dir and the zero-byte file",
                     _paths(find(fs.root, empty())) == ["/empty_dir", "/src/util.py"])
    all_ok &= _check("custom predicate via Where",
                     _paths(find(fs.root, Where(lambda n: n.name.startswith("in"), "starts-in")))
                     == ["/node_modules/lib/index.js"])
    all_ok &= _check("specs are data: equal ASTs compare equal",
                     (ext(".py") & ~name("t*")) == And(Ext(".py"), Not(Name("t*"))))

    print("\n--- traversal options ---")
    all_ok &= _check("start node included when it matches; max_depth=1",
                     _paths(find(fs.get("/data"), is_dir(), max_depth=1)) == ["/data", "/data/archive"])
    all_ok &= _check("max_depth=0 -> only the start", _paths(find(fs.root, max_depth=0)) == ["/"])
    all_ok &= _check("prune skips node_modules entirely",
                     "/node_modules/lib/index.js" not in _paths(find(fs.root, prune=name("node_modules")))
                     and len(list(find(fs.root, prune=name("node_modules")))) == 11)
    gen = find(fs.root, is_file())
    all_ok &= _check("find is lazy (a generator)", next(gen).path == "/data/archive/old.csv")

    print("\n--- parser (interpreter) ---")
    all_ok &= _check("OR binds looser than implicit AND; ! binds tightest",
                     parse(["-name", "*.py", "-o", "-type", "d", "!", "-empty"])
                     == Or(Name("*.py"), And(TypeIs("d"), Not(Empty()))))
    all_ok &= _check("parentheses override precedence",
                     parse(["(", "-name", "*.py", "-o", "-type", "d", ")", "-a", "!", "-empty"])
                     == And(Or(Name("*.py"), TypeIs("d")), Not(Empty())))
    all_ok &= _check("-size +1M / -2k / 300 exact",
                     parse(["-size", "+1M"]) == SizeGt(1024 ** 2) and parse(["-size", "-2k"]) == SizeLt(2048)
                     and parse(["-size", "300"]) == SizeEq(300))
    all_ok &= _check("parsed query runs: python files or non-empty dirs, excluding node_modules",
                     _paths(find(fs.root, parse(["-name", "*.py", "-o", "-type", "d", "!", "-empty"]),
                                 prune=name("node_modules")))
                     == ["/", "/data", "/data/archive", "/src", "/src/app.py", "/src/test_app.py", "/src/util.py"])
    for bad in (["(", "-name", "x"], ["-name"], ["-bogus"], ["-type", "x"], ["-size", "+zz"], ["-name", "a", ")"]):
        all_ok &= _check(f"parse error: {' '.join(bad)}", _raises(FindError, lambda b=bad: parse(b)))
    return all_ok
# ================================================================= END TESTS ==


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
