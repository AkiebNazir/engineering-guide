"""
================================================================================
SOLUTION · LLD 010 · Unix `find` / File Search                     [Tier 1]
================================================================================

THE CORE IDEA
--------------
"Design find" (an Amazon favourite) tests whether new search criteria can be
added without editing existing code. Three patterns, each doing one job:

    1. COMPOSITE      File and Directory share a Node interface; a directory
                      holds nodes. Traversal doesn't care which is which.
    2. SPECIFICATION  every criterion is a small object with matches(node);
                      And / Or / Not combine them. The combination is a TREE OF
                      DATA (an AST), not opaque lambdas, so it can be printed,
                      optimised, or translated (to SQL, to an index query).
                      Python operators make it read well:
                          is_file() & (ext(".py") | size_gt(1_000_000)) & ~name("test_*")
    3. ITERATOR       find() is a generator with an explicit stack: it yields
                      the first match immediately, uses O(depth) memory, never
                      hits Python's recursion limit, and can PRUNE subtrees
                      (node_modules, .git) without visiting them.

The follow-up that separates candidates: "now accept the real command line,
`-name '*.py' -o ( -type d ! -empty )`". That's the INTERPRETER pattern — a
recursive-descent parser that produces the same Spec AST. Precedence: `!`
binds tightest, then implicit/explicit AND, then OR.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. In-memory tree: FileSystem.mkdir(path) (creates parents), add_file(path,
     size, modified), get(path). Paths are "/"-separated from the root.
  2. Criteria: name glob (case-sensitive and not), extension, type file/dir,
     size greater/less than, modified after, empty, custom predicate.
  3. Combine with AND, OR, NOT, arbitrarily nested.
  4. find(start, spec, max_depth=None, prune=None) -> lazy iterator, pre-order,
     children in name order, start node included if it matches.
  5. prune: directories matching it are neither yielded nor entered.
  6. parse(args) turns find-style CLI tokens into a Spec.
  Out of scope: real disk I/O, symlinks, permissions, -exec.


================================================================================
ENTITIES AND INVARIANTS
================================================================================
    Node (abstract)      name, parent, path
    File                 size, modified
    Directory            children {name: Node}
                         INVARIANT: names unique within a directory; a node has
                         exactly one parent (no cycles)
    FileSystem           root + path resolution
    Spec (abstract)      matches(node) -> bool; &, |, ~ build And/Or/Not
       Name, Ext, TypeIs, SizeGt, SizeLt, ModifiedAfter, Empty, Where
       And, Or, Not      composite specs (the AST)
    find()               generator (Iterator pattern)
    Parser               tokens -> Spec (Interpreter pattern)


================================================================================
CLASS DIAGRAM
================================================================================
          «abstract» Node ◀──────────────── children ──┐
          ├─ name, parent, path                         │
          ▲                  ▲                          │
         File           Directory ◆─────────────────────┘      (Composite)

          «abstract» Spec  matches(node)
          ▲ Name ▲ Ext ▲ TypeIs ▲ SizeGt ▲ SizeLt ▲ ModifiedAfter ▲ Empty ▲ Where
          ▲ And(left, right) ▲ Or(left, right) ▲ Not(inner)     (Specification + Composite)


================================================================================
PARSER · grammar and a trace
================================================================================
    or_expr   := and_expr ( ("-o" | "-or") and_expr )*
    and_expr  := unary ( ["-a" | "-and"] unary )*          implicit AND
    unary     := ("!" | "-not") unary | primary
    primary   := "(" or_expr ")" | "-name" PAT | "-iname" PAT | "-type" (f|d)
               | "-size" [+|-]N[k|M|G] | "-empty"

    tokens:  -name '*.py' -o -type d ! -empty
    or_expr
      and_expr -> Name('*.py')
      "-o"
      and_expr -> TypeIs(d)  AND  unary("!" -> Not(Empty))
    result:  Or(Name('*.py'), And(TypeIs('d'), Not(Empty())))
    (NOT "(name OR type d) AND NOT empty" — precedence matters; tested below.)


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Specs are frozen dataclasses: comparable in tests (parse(...) == expected),
    printable, hashable. Closures would work but can't be inspected.
  * find() is a generator: callers can stop after the first N results; memory
    O(depth + widest directory) instead of O(results).
  * Explicit stack instead of recursion: a 5,000-deep tree works (demo 2).
  * Prune is separate from the match spec because "don't descend" and "don't
    report" are different questions (unix find conflates them confusingly).
  * AND/OR short-circuit, so put cheap criteria first; an optimiser could reorder
    by cost because the AST is data.


================================================================================
COMPLEXITY
================================================================================
    find          O(V * s) time for V visited nodes, s = spec size;  O(depth) stack
    parse         O(tokens)
    mkdir/add     O(path length)


================================================================================
EDGE CASES
================================================================================
  * Start node itself matches (find . -type d prints ".").
  * max_depth=0 -> only the start node.
  * Glob with no wildcard is an exact name match; -iname ignores case.
  * Empty directory vs zero-byte file: both "empty".
  * Parser: unbalanced "(", missing argument, unknown flag -> FindError.
  * Adding a file where a file already exists / path through a file -> FindError.


================================================================================
COMMON MISTAKES
================================================================================
  1. One `search(name=None, ext=None, min_size=None, ...)` with a growing
     parameter list and if-chains (not open for extension).
  2. Filters as subclasses of each other (SizeAndNameFilter...).
  3. Recursive traversal returning a full list.
  4. Only AND supported; OR/NOT bolted on later with special cases.
  5. Getting OR/AND precedence wrong in the parser.
  6. File and Directory with no common type, so traversal branches everywhere.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Real filesystem   -> Node adapter over os.scandir (lazy children);
                         symlink loop detection via (st_dev, st_ino) visited set.
  * Parallel search   -> worker pool over directory queue; results channel.
  * Huge trees, repeated queries -> index (name trigram, size B-tree) and
                         translate the Spec AST into index lookups.
  * -exec / actions   -> Visitor/Command applied to each match.
  * Sorting, limit    -> itertools.islice over the generator; heap for top-k.


================================================================================
RELATED
================================================================================
  SoftwareDesign/04_design_patterns_in_practice.md  §12 Composite, §14 Iterator,
                                                    §15 Specification
  PyDSA 25_design  in-memory file system (path resolution)
  lld/007_logging_framework (filters as small composable objects)
"""

from __future__ import annotations

import fnmatch
import time
from dataclasses import dataclass
from typing import Callable, Iterator


class FindError(Exception): ...


# ----------------------------------------------------------------------------
# Composite: the file tree
# ----------------------------------------------------------------------------
class Node:
    def __init__(self, name: str, modified: float = 0.0) -> None:
        self.name = name
        self.modified = modified
        self.parent: Directory | None = None

    @property
    def path(self) -> str:
        parts, node = [], self
        while node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))

    @property
    def is_dir(self) -> bool:
        return False


class File(Node):
    def __init__(self, name: str, size: int, modified: float = 0.0) -> None:
        super().__init__(name, modified)
        if size < 0:
            raise FindError("negative size")
        self.size = size


class Directory(Node):
    def __init__(self, name: str, modified: float = 0.0) -> None:
        super().__init__(name, modified)
        self.children: dict[str, Node] = {}

    @property
    def is_dir(self) -> bool:
        return True

    @property
    def size(self) -> int:
        return 0

    def add(self, node: Node) -> Node:
        if node.name in self.children:
            raise FindError(f"{self.path.rstrip('/')}/{node.name} already exists")
        node.parent = self
        self.children[node.name] = node
        return node


class FileSystem:
    def __init__(self) -> None:
        self.root = Directory("")

    def get(self, path: str) -> Node:
        node: Node = self.root
        for part in _parts(path):
            if not isinstance(node, Directory) or part not in node.children:
                raise FindError(f"no such path: {path}")
            node = node.children[part]
        return node

    def mkdir(self, path: str) -> Directory:
        node: Node = self.root
        for part in _parts(path):
            if not isinstance(node, Directory):
                raise FindError(f"{node.path} is a file")
            node = node.children.get(part) or node.add(Directory(part))
        if not isinstance(node, Directory):
            raise FindError(f"{path} is a file")
        return node

    def add_file(self, path: str, size: int, modified: float = 0.0) -> File:
        parent_path, _, name = path.rstrip("/").rpartition("/")
        return self.mkdir(parent_path).add(File(name, size, modified))


def _parts(path: str) -> list[str]:
    return [p for p in path.split("/") if p]


# ----------------------------------------------------------------------------
# Specification: criteria as an AST
# ----------------------------------------------------------------------------
class Spec:
    def matches(self, node: Node) -> bool:
        raise NotImplementedError

    def __and__(self, other: Spec) -> Spec:
        return And(self, other)

    def __or__(self, other: Spec) -> Spec:
        return Or(self, other)

    def __invert__(self) -> Spec:
        return Not(self)


@dataclass(frozen=True)
class And(Spec):
    left: Spec
    right: Spec

    def matches(self, node):
        return self.left.matches(node) and self.right.matches(node)


@dataclass(frozen=True)
class Or(Spec):
    left: Spec
    right: Spec

    def matches(self, node):
        return self.left.matches(node) or self.right.matches(node)


@dataclass(frozen=True)
class Not(Spec):
    inner: Spec

    def matches(self, node):
        return not self.inner.matches(node)


@dataclass(frozen=True)
class Always(Spec):
    def matches(self, node):
        return True


@dataclass(frozen=True)
class Name(Spec):
    pattern: str
    ignore_case: bool = False

    def matches(self, node):
        if self.ignore_case:
            return fnmatch.fnmatchcase(node.name.lower(), self.pattern.lower())
        return fnmatch.fnmatchcase(node.name, self.pattern)


@dataclass(frozen=True)
class Ext(Spec):
    extension: str

    def matches(self, node):
        return not node.is_dir and node.name.endswith(self.extension)


@dataclass(frozen=True)
class TypeIs(Spec):
    kind: str                     # "f" or "d"

    def matches(self, node):
        return node.is_dir == (self.kind == "d")


@dataclass(frozen=True)
class SizeGt(Spec):
    bytes_: int

    def matches(self, node):
        return not node.is_dir and node.size > self.bytes_


@dataclass(frozen=True)
class SizeLt(Spec):
    bytes_: int

    def matches(self, node):
        return not node.is_dir and node.size < self.bytes_


@dataclass(frozen=True)
class SizeEq(Spec):
    bytes_: int

    def matches(self, node):
        return not node.is_dir and node.size == self.bytes_


@dataclass(frozen=True)
class ModifiedAfter(Spec):
    timestamp: float

    def matches(self, node):
        return node.modified > self.timestamp


@dataclass(frozen=True)
class Empty(Spec):
    def matches(self, node):
        return not node.children if isinstance(node, Directory) else node.size == 0


@dataclass(frozen=True)
class Where(Spec):
    predicate: Callable[[Node], bool]
    label: str = "where"

    def matches(self, node):
        return bool(self.predicate(node))


ALL = Always()


def name(pattern: str) -> Spec: return Name(pattern)
def iname(pattern: str) -> Spec: return Name(pattern, ignore_case=True)
def ext(extension: str) -> Spec: return Ext(extension)
def is_file() -> Spec: return TypeIs("f")
def is_dir() -> Spec: return TypeIs("d")
def size_gt(n: int) -> Spec: return SizeGt(n)
def size_lt(n: int) -> Spec: return SizeLt(n)
def modified_after(t: float) -> Spec: return ModifiedAfter(t)
def empty() -> Spec: return Empty()


# ----------------------------------------------------------------------------
# Iterator: lazy, iterative, prunable traversal
# ----------------------------------------------------------------------------
def find(start: Node, spec: Spec = ALL, max_depth: int | None = None,
         prune: Spec | None = None) -> Iterator[Node]:
    stack: list[tuple[Node, int]] = [(start, 0)]
    while stack:
        node, depth = stack.pop()
        if node.is_dir and prune is not None and node is not start and prune.matches(node):
            continue
        if spec.matches(node):
            yield node
        if isinstance(node, Directory) and (max_depth is None or depth < max_depth):
            for child_name in sorted(node.children, reverse=True):
                stack.append((node.children[child_name], depth + 1))


# ----------------------------------------------------------------------------
# Interpreter: find-style CLI tokens -> Spec
# ----------------------------------------------------------------------------
_UNITS = {"": 1, "c": 1, "k": 1024, "M": 1024 ** 2, "G": 1024 ** 3}


def parse(tokens: list[str]) -> Spec:
    if not tokens:
        return ALL
    parser = _Parser(tokens)
    spec = parser.or_expr()
    if parser.peek() is not None:
        raise FindError(f"unexpected {parser.peek()!r}")
    return spec


class _Parser:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens, self.i = tokens, 0

    def peek(self) -> str | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self, what: str = "an argument") -> str:
        tok = self.peek()
        if tok is None:
            raise FindError(f"expected {what} at end of expression")
        self.i += 1
        return tok

    def or_expr(self) -> Spec:
        left = self.and_expr()
        while self.peek() in ("-o", "-or"):
            self.take()
            left = Or(left, self.and_expr())
        return left

    def and_expr(self) -> Spec:
        left = self.unary()
        while True:
            tok = self.peek()
            if tok in ("-a", "-and"):
                self.take()
            elif tok is None or tok in (")", "-o", "-or"):
                return left
            left = And(left, self.unary())

    def unary(self) -> Spec:
        if self.peek() in ("!", "-not"):
            self.take()
            return Not(self.unary())
        return self.primary()

    def primary(self) -> Spec:
        tok = self.take("an expression")
        if tok == "(":
            inner = self.or_expr()
            if self.take("')'") != ")":
                raise FindError("expected ')'")
            return inner
        if tok == "-name":
            return Name(self.take("a pattern after -name"))
        if tok == "-iname":
            return Name(self.take("a pattern after -iname"), ignore_case=True)
        if tok == "-type":
            kind = self.take("f or d after -type")
            if kind not in ("f", "d"):
                raise FindError(f"-type {kind}: expected f or d")
            return TypeIs(kind)
        if tok == "-size":
            return self._size(self.take("a size after -size"))
        if tok == "-empty":
            return Empty()
        raise FindError(f"unknown predicate {tok!r}")

    @staticmethod
    def _size(arg: str) -> Spec:
        sign = arg[0] if arg[:1] in ("+", "-") else ""
        body = arg[1:] if sign else arg
        unit = body[-1] if body[-1:] in ("c", "k", "M", "G") else ""
        digits = body[:-1] if unit else body
        if not digits.isdigit():
            raise FindError(f"bad size {arg!r}")
        n = int(digits) * _UNITS[unit]
        return SizeGt(n) if sign == "+" else SizeLt(n) if sign == "-" else SizeEq(n)


# ===================================================================== TESTS ==
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


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: first match from a 300,000-file tree: lazy vs build-a-list ---")
    fs = FileSystem()
    for d in range(300):
        folder = fs.mkdir(f"/d{d:03}")
        for f in range(1000):
            folder.add(File(f"f{f:04}.log", f))
    spec = name("*.log") & size_gt(10)

    def eager(node: Node) -> list[Node]:
        out = [node] if spec.matches(node) else []
        if isinstance(node, Directory):
            for child in sorted(node.children):
                out.extend(eager(node.children[child]))
        return out

    start = time.perf_counter()
    first_lazy = next(find(fs.root, spec))
    lazy_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    first_eager = eager(fs.root)[0]
    eager_ms = (time.perf_counter() - start) * 1000
    print(f"      generator: {lazy_ms:.2f} ms to first result; full list: {eager_ms:.0f} ms")
    all_ok &= _check("same first result, generator orders of magnitude sooner",
                     first_lazy is first_eager and lazy_ms * 50 < eager_ms)

    print("\n--- DEMO 2: a 5,000-level deep directory chain ---")
    fs = FileSystem()
    node = fs.root
    for i in range(5000):
        node = node.add(Directory(f"n{i}"))
    node.add(File("needle.txt", 1))

    def recursive_find(n: Node, spec: Spec) -> list[Node]:
        found = [n] if spec.matches(n) else []
        if isinstance(n, Directory):
            for child in n.children.values():
                found.extend(recursive_find(child, spec))
        return found

    try:
        recursive_find(fs.root, name("needle.txt"))
        recursion = "worked"
    except RecursionError:
        recursion = "RecursionError"
    hits = list(find(fs.root, name("needle.txt")))
    print(f"      recursive traversal: {recursion}; explicit stack: found {len(hits)} at depth 5001")
    all_ok &= _check("iterative find survives depth that breaks recursion",
                     recursion == "RecursionError" and len(hits) == 1)

    print("\n--- DEMO 3: pruning node_modules ---")
    fs = FileSystem()
    for i in range(50):
        fs.add_file(f"/app/src/m{i}.py", 10)
    for i in range(200):
        for j in range(100):
            fs.add_file(f"/app/node_modules/pkg{i}/f{j}.js", 10)
    visited = {"n": 0}
    counting = Where(lambda n: visited.__setitem__("n", visited["n"] + 1) or n.name.endswith(".py"), "count")
    list(find(fs.root, counting))
    no_prune = visited["n"]
    visited["n"] = 0
    result = list(find(fs.root, counting, prune=name("node_modules")))
    print(f"      nodes examined: {no_prune} without prune, {visited['n']} with prune "
          f"({len(result)} .py files either way)")
    all_ok &= _check("prune avoids ~99% of the work", visited["n"] * 50 < no_prune and len(result) == 50)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
