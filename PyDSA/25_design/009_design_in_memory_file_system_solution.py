"""
================================================================================
SOLUTION · LeetCode 588 · Design In-Memory File System                    [Hard]
https://leetcode.com/problems/design-in-memory-file-system/
================================================================================

THE CORE IDEA
--------------
A TREE where every node is EITHER a directory (holds a `children: dict[str,
Node]`) OR a file (holds `content: str`), never both — the same
"dict-of-named-children" shape as a Trie (topic 13), with one added
distinction a Trie never needs: a node's PAYLOAD TYPE (directory vs. file)
determines what operations are even valid on it (`ls` on a file behaves
differently than `ls` on a directory; you cannot `mkdir` where a file
already exists).

All four operations reduce to the same walk: split the path on '/',
descend one named-child lookup per segment. `mkdir`/`addContentToFile`
CREATE missing directory nodes along the way (the "-p" behavior);
`ls`/`readContentFromFile` walk WITHOUT creating anything, since the
problem guarantees valid paths for reads.


================================================================================
APPROACH 1 · Flat dict of full-path-string -> node (alternative, priced,
not coded)
================================================================================
Instead of a tree, key a single dict directly by the FULL path string
(`"/a/b/c" -> Node`). `mkdir("/a/b/c")` would insert three dict entries
(one per prefix). `ls("/a/b")` would need to SCAN every key in the dict
checking "does this key start with `/a/b/` and have exactly one more
segment" to find immediate children — O(total paths) per `ls` call
instead of O(this directory's own children count).

    mkdir / addContentToFile / readContentFromFile:  O(path length),
                                                       same as the tree.
    ls:                                                O(total number of
                                                       paths in the whole
                                                       filesystem) — must
                                                       scan every key to
                                                       find this one
                                                       directory's
                                                       immediate children.

Simpler to write (no node class, no tree walk) but strictly worse for
`ls`, which is exactly the operation a tree is built to make cheap — not
coded as the primary answer for that reason, though it would pass given
this problem's tiny constraints (`<= 300` total calls).


================================================================================
APPROACH 2 · Tree of directory/file nodes ✅ (the answer)
================================================================================
    class _Node:
        def __init__(self):
            self.children = {}     # name -> _Node, present only for directories
            self.content = None    # str, present only for files (None = directory)
            self.is_file = False

    class FileSystem:
        def __init__(self):
            self.root = _Node()

        def _segments(self, path):
            return [s for s in path.split('/') if s]   # drop the leading '' from split

        def _walk(self, path, create_dirs=False):
            node = self.root
            for seg in self._segments(path):
                if seg not in node.children:
                    if not create_dirs:
                        return None
                    new_dir = _Node()
                    node.children[seg] = new_dir
                node = node.children[seg]
            return node

        def ls(self, path):
            node = self._walk(path)
            if node.is_file:
                return [path.rsplit('/', 1)[-1]]
            return sorted(node.children.keys())

        def mkdir(self, path):
            self._walk(path, create_dirs=True)

        def addContentToFile(self, filePath, content):
            segs = self._segments(filePath)
            parent = self._walk('/' + '/'.join(segs[:-1]), create_dirs=True) if len(segs) > 1 else self.root
            name = segs[-1]
            if name not in parent.children:
                parent.children[name] = _Node()
                parent.children[name].is_file = True
                parent.children[name].content = ""
            parent.children[name].content += content

        def readContentFromFile(self, filePath):
            return self._walk(filePath).content

`_walk` is the single shared traversal both create-capable and
read-only callers use — the ONLY difference between `mkdir`'s walk and
`ls`'s walk is the `create_dirs` flag.

    Time: mkdir/addContentToFile/readContentFromFile O(path depth); ls
          O(path depth + children·log children) for the sort.
    Space: O(total path characters + total file content).


================================================================================
STEP BY STEP TRACE
================================================================================
    init                    root: {children: {}}

    ls("/")                  walk("/") -> segments=[] -> node=root.
                              root.is_file=False -> sorted(root.children.keys())=[]
                              returns []

    mkdir("/a/b/c")           walk("/a/b/c", create_dirs=True):
                              seg "a": not in root.children -> create dir node "a"
                              seg "b": not in a.children -> create dir node "b"
                              seg "c": not in b.children -> create dir node "c"
                              root -> a -> b -> c   (all directories, empty children)

    addContentToFile(
      "/a/b/c/d", "hello")    segs=["a","b","c","d"]. parent = walk("/a/b/c",
                              create_dirs=True) -> the "c" node (already exists).
                              "d" not in c.children -> create FILE node "d",
                              content="". Then content += "hello" -> "hello".

    ls("/")                   root.children = {"a": <dir>} -> sorted -> ["a"]
                              returns ["a"]

    readContentFromFile(
      "/a/b/c/d")             walk("/a/b/c/d") -> the "d" file node.
                              returns "hello"

    ASCII of the tree after all operations above:

        root
         └── a/                (directory)
              └── b/            (directory)
                   └── c/        (directory)
                        └── d     (FILE, content="hello")


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          mkdir/add/read      ls                        Space
    ---------------------------------  -------------------  ------------------------  -----
    Flat dict, full-path keys         O(path length)       O(total paths in system)  O(total path chars)
    Tree of nodes ✅                  O(path depth)         O(depth + children log)   O(total path chars + content)
    Mutates input? n/a — design problem in every row (the filesystem itself IS the mutable state).


================================================================================
EDGE CASES
================================================================================
    ls("/") on an empty filesystem    Must return `[]`, not error — root
                                       exists from construction with no
                                       children yet.
    ls on a FILE path (not a
      directory)                      Must return a ONE-element list of
                                       just the file's own basename, not
                                       its content and not treat it like
                                       an (empty) directory listing.
    mkdir on a path that partially
      already exists                  Must create only the MISSING
                                       segments, reusing existing
                                       directory nodes for the rest — not
                                       error, not overwrite.
    addContentToFile on an EXISTING
      file                            Must APPEND, never overwrite/reset
                                       the existing content.
    addContentToFile creating deep
      missing parent directories       Same "-p" behavior as mkdir,
                                       reused via the same `_walk(...,
                                       create_dirs=True)` helper.
    Multiple children under the
      same directory, ls must SORT     `ls` on a directory with children
                                       ["banana", "apple"] must return
                                       ["apple", "banana"] — lexicographic,
                                       not insertion order.
    filePath at the TOP level (no
      intermediate directories, e.g.
      "/file.txt")                    `segs[:-1]` is empty -> parent is
                                       root directly, not an error from
                                       walking an empty path string.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting to filter the EMPTY leading segment from
   `"/a/b/c".split('/')` (`['', 'a', 'b', 'c']`) — walking that empty
   string as if it were a real child name either crashes or silently
   creates a bogus node named `""`.

2. `ls` on a file path treating it like an (empty) directory — returning
   `[]` instead of `[filename]`, because the `is_file` flag wasn't
   checked before falling through to the "list children" branch.

3. `addContentToFile` OVERWRITING content instead of appending on repeat
   calls to the SAME file — the spec is explicit that a second call
   appends to what's already there.

4. Computing the file's PARENT path incorrectly for `addContentToFile`
   (off-by-one in `segs[:-1]` vs `segs[:-2]`, or mishandling the
   single-segment case like `/file.txt` where there IS no intermediate
   directory) — walks to the wrong node or crashes on a top-level file.

5. Sharing ONE node class field ambiguously between "directory" and
   "file" (e.g. using `children = None` to mean "this is a file" instead
   of an explicit `is_file` flag) — works until a refactor accidentally
   leaves `children = {}` (empty dict, not None) on a freshly-created file
   node, which then silently behaves like an empty directory in `ls`.

6. Not sorting `ls`'s directory listing — LeetCode's expected output is
   explicitly lexicographically sorted; returning children in
   insertion/dict order (which happens to often "look" sorted on small
   test cases) fails larger hidden tests.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How would you support `rm` (delete a file or an empty/non-empty
   directory)?
A: Walk to the PARENT of the target (same `_walk` minus the last
   segment), then `del parent.children[last_segment]` — for a
   non-empty directory, Python's garbage collector reclaims the entire
   detached subtree automatically once nothing references it, so no
   explicit recursive deletion is needed (though an interviewer may want
   you to say this explicitly rather than assume it).

Q: How would you support `mv` (rename/move a file or directory)?
A: Detach the source node from its current parent's `children` dict,
   then attach it under the destination parent's `children` dict with
   the destination's name — walking to both parents first (creating the
   destination's intermediate directories if needed, mirroring
   `addContentToFile`'s pattern).

Q: How would this scale to a REAL, disk-backed or distributed filesystem
   (not everything fits in memory)?
A: The tree-of-nodes shape generalizes directly to an on-disk structure —
   each directory node becomes an index/inode listing child names and
   pointers (block addresses or, in a distributed system, which server
   owns that subtree) instead of in-memory object references; the
   traversal ALGORITHM (`_walk`, one lookup per path segment) is
   unchanged, only what a "lookup" costs changes (a disk seek, or a
   network hop, instead of a dict access).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 208  Implement Trie (Prefix Tree) (topic 13)        — identical dict-of-children node shape
    LC 642  Design Search Autocomplete System (this topic, 010) — trie storing SENTENCES with counts
    LC 366/1145  N-ary tree problems                        — same "children dict/list per node" recursion
    Topic 13 · Trie (Prefix Tree)                            — every "one node per path segment" technique here
================================================================================
"""

import random
import string
import time


class _Node:
    __slots__ = ("children", "content", "is_file")

    def __init__(self):
        self.children: dict[str, "_Node"] = {}
        self.content = None
        self.is_file = False


class FileSystem:
    """Tree of directory/file nodes, one dict-of-named-children per
    directory. See THE CORE IDEA above."""

    def __init__(self):
        self.root = _Node()

    def _segments(self, path: str) -> list[str]:
        return [s for s in path.split("/") if s]

    def _walk(self, path: str, create_dirs: bool = False):
        node = self.root
        for seg in self._segments(path):
            if seg not in node.children:
                if not create_dirs:
                    return None
                node.children[seg] = _Node()
            node = node.children[seg]
        return node

    def ls(self, path: str) -> list[str]:
        node = self._walk(path)
        if node.is_file:
            return [path.rsplit("/", 1)[-1]]
        return sorted(node.children.keys())

    def mkdir(self, path: str) -> None:
        self._walk(path, create_dirs=True)

    def addContentToFile(self, filePath: str, content: str) -> None:
        segs = self._segments(filePath)
        parent_path = "/" + "/".join(segs[:-1])
        parent = self._walk(parent_path, create_dirs=True)
        name = segs[-1]
        if name not in parent.children:
            file_node = _Node()
            file_node.is_file = True
            file_node.content = ""
            parent.children[name] = file_node
        parent.children[name].content += content

    def readContentFromFile(self, filePath: str) -> str:
        return self._walk(filePath).content


# ------------------------------------------------------------------------
# Alternatives / oracles.
# ------------------------------------------------------------------------
class FileSystemFlatDict:
    """Approach 1: single dict keyed by full path string. O(total paths)
    per ls (must scan every key). Used as a correctness oracle."""

    def __init__(self):
        self.paths: dict[str, str] = {"/": None}  # path -> content (None = directory)

    def _parent(self, path: str) -> str:
        if path == "/":
            return None
        parent = path.rsplit("/", 1)[0]
        return parent if parent else "/"

    def ls(self, path: str) -> list[str]:
        if self.paths.get(path) is not None:  # it's a file
            return [path.rsplit("/", 1)[-1]]
        prefix = path if path.endswith("/") else path + "/"
        children = set()
        for p in self.paths:
            if p != path and p.startswith(prefix):
                rest = p[len(prefix):]
                children.add(rest.split("/", 1)[0])
        return sorted(children)

    def mkdir(self, path: str) -> None:
        parts = [p for p in path.split("/") if p]
        cur = ""
        for part in parts:
            cur += "/" + part
            if cur not in self.paths:
                self.paths[cur] = None

    def addContentToFile(self, filePath: str, content: str) -> None:
        parent = self._parent(filePath)
        if parent is not None:
            self.mkdir(parent)
        if filePath not in self.paths or self.paths[filePath] is None:
            self.paths[filePath] = ""
        self.paths[filePath] += content

    def readContentFromFile(self, filePath: str) -> str:
        return self.paths[filePath]


# ==============================================================================
# TESTS — run:  python 009_design_in_memory_file_system_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    # ------------------------------------------------------------------
    # Correctness: LeetCode's canonical example, cross-checked against
    # the flat-dict oracle.
    # ------------------------------------------------------------------
    print("--- correctness: tree vs flat-dict oracle ---")
    for name, cls in (("tree      ", FileSystem), ("flat-dict ", FileSystemFlatDict)):
        fs = cls()
        results = [fs.ls("/")]
        fs.mkdir("/a/b/c")
        results.append(None)
        fs.addContentToFile("/a/b/c/d", "hello")
        results.append(None)
        results.append(fs.ls("/"))
        results.append(fs.readContentFromFile("/a/b/c/d"))
        wants = [[], None, None, ["a"], "hello"]
        ok = results == wants
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  results={results}  (want {wants})")

    # ------------------------------------------------------------------
    # ls on a file path vs. a directory path.
    # ------------------------------------------------------------------
    print("\n--- ls() on a file returns [filename], not a directory-style listing ---")
    fs2 = FileSystem()
    fs2.addContentToFile("/x/y.txt", "abc")
    ok = fs2.ls("/x/y.txt") == ["y.txt"]
    ok &= fs2.ls("/x") == ["y.txt"]  # directory listing of x's one child
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  file path -> [own name]; directory path -> sorted children")

    # ------------------------------------------------------------------
    # addContentToFile appends, doesn't overwrite.
    # ------------------------------------------------------------------
    print("\n--- addContentToFile appends across repeated calls ---")
    fs2.addContentToFile("/x/y.txt", "def")
    ok = fs2.readContentFromFile("/x/y.txt") == "abcdef"
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  repeated addContentToFile appends: {fs2.readContentFromFile('/x/y.txt')!r}")

    # ------------------------------------------------------------------
    # ls sorts children lexicographically, not by insertion order.
    # ------------------------------------------------------------------
    print("\n--- ls() sorts children lexicographically ---")
    fs3 = FileSystem()
    fs3.mkdir("/banana")
    fs3.mkdir("/apple")
    fs3.mkdir("/cherry")
    ok = fs3.ls("/") == ["apple", "banana", "cherry"]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  ls('/') sorted: {fs3.ls('/')}")

    # ------------------------------------------------------------------
    # mkdir reuses existing intermediate directories, doesn't error or
    # duplicate.
    # ------------------------------------------------------------------
    print("\n--- mkdir on a partially-existing path reuses existing dirs ---")
    fs4 = FileSystem()
    fs4.mkdir("/a/b")
    fs4.mkdir("/a/c")  # "a" already exists, only "c" is new
    ok = fs4.ls("/a") == ["b", "c"]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  ls('/a') after two mkdirs sharing prefix 'a': {fs4.ls('/a')}")

    # ------------------------------------------------------------------
    # Top-level file (no intermediate directories).
    # ------------------------------------------------------------------
    print("\n--- top-level file, no intermediate directories ---")
    fs5 = FileSystem()
    fs5.addContentToFile("/note.txt", "hi")
    ok = fs5.ls("/") == ["note.txt"] and fs5.readContentFromFile("/note.txt") == "hi"
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  top-level file created and read correctly")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the flat-dict oracle.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check vs flat-dict oracle (150 ops, small path universe) ---")
    rng = random.Random(51)
    names = list(string.ascii_lowercase[:6])

    def random_path(depth_range=(1, 3)):
        depth = rng.randint(*depth_range)
        return "/" + "/".join(rng.choice(names) for _ in range(depth))

    ours = FileSystem()
    oracle = FileSystemFlatDict()
    mismatch = False
    created_files = set()

    # LeetCode guarantees valid operations: never add content to an existing
    # DIRECTORY path, and never create anything underneath a FILE. The random
    # generator must respect that too, or it tests inputs the problem rules out.
    def has_file_ancestor(p):
        parts = [s for s in p.split("/") if s]
        return any("/" + "/".join(parts[:k]) in created_files for k in range(1, len(parts)))

    def is_existing_dir(p):
        return p in oracle.paths and oracle.paths[p] is None

    for _ in range(150):
        op = rng.choice(["mkdir", "add", "read", "ls"])
        if op == "mkdir":
            p = random_path()
            if p in created_files or has_file_ancestor(p):
                continue
            ours.mkdir(p)
            oracle.mkdir(p)
        elif op == "add":
            p = random_path()
            if is_existing_dir(p) or has_file_ancestor(p):
                continue
            content = rng.choice(string.ascii_letters)
            ours.addContentToFile(p, content)
            oracle.addContentToFile(p, content)
            created_files.add(p)
        elif op == "read" and created_files:
            p = rng.choice(list(created_files))
            r1, r2 = ours.readContentFromFile(p), oracle.readContentFromFile(p)
            if r1 != r2:
                mismatch = True
        elif op == "ls":
            p = rng.choice(["/"] + [random_path((1, 2))])
            try:
                r1 = ours.ls(p)
            except Exception:
                r1 = None
            try:
                r2 = oracle.ls(p)
            except Exception:
                r2 = None
            if r1 is not None and r2 is not None and r1 != r2:
                mismatch = True
    all_ok &= not mismatch
    print(f"{'PASS' if not mismatch else 'FAIL'}  150 randomized ops, tree matches flat-dict oracle")

    # ------------------------------------------------------------------
    # BENCHMARK — ls() on a deep, wide filesystem: tree (O(depth +
    # children)) vs flat-dict (O(total paths)). REAL measured numbers.
    # ------------------------------------------------------------------
    print("\n--- benchmark: ls('/root') on a filesystem with N total files elsewhere ---")
    for n_files in (500, 2000, 6000):
        tree = FileSystem()
        flat = FileSystemFlatDict()
        tree.mkdir("/root")
        flat.mkdir("/root")
        tree.addContentToFile("/root/target.txt", "x")
        flat.addContentToFile("/root/target.txt", "x")
        for i in range(n_files):
            p = f"/other{i}/file{i}.txt"
            tree.addContentToFile(p, "y")
            flat.addContentToFile(p, "y")

        t0 = time.perf_counter()
        for _ in range(200):
            tree.ls("/root")
        t1 = time.perf_counter()
        tree_ms = (t1 - t0) * 1000

        t0 = time.perf_counter()
        for _ in range(200):
            flat.ls("/root")
        t1 = time.perf_counter()
        flat_ms = (t1 - t0) * 1000

        speedup = flat_ms / tree_ms if tree_ms > 0 else float("inf")
        print(f"  total files~{n_files:>5}   tree: {tree_ms:>8.2f}ms   flat-dict: {flat_ms:>8.2f}ms   {speedup:>6.1f}x faster (tree)")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
