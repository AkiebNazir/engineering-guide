"""
================================================================================
LeetCode 588 · Design In-Memory File System                               [Hard]
https://leetcode.com/problems/design-in-memory-file-system/
Topic: 25 · Design
================================================================================

PROBLEM
-------
Design an in-memory file system to simulate a directory tree structure.

Implement the `FileSystem` class:

    FileSystem()                         Initializes the object (root "/").
    ls(path) -> list[str]                If `path` is a FILE, returns a
                                          list containing just its own
                                          name. If `path` is a DIRECTORY,
                                          returns the names of its
                                          contents (files AND
                                          subdirectories), SORTED
                                          lexicographically.
    mkdir(path) -> None                  Creates a new directory. `path`
                                          may include multiple levels that
                                          don't exist yet — create ALL of
                                          them (like `mkdir -p`).
    addContentToFile(filePath,
                      content) -> None   If `filePath` does not exist,
                                          create the file (creating any
                                          missing parent directories too),
                                          then APPEND `content`. If it
                                          already exists, append to its
                                          EXISTING content.
    readContentFromFile(filePath)
                      -> str             Returns the content of `filePath`.


EXAMPLES
--------
Example 1:
    Input:
        ["FileSystem", "ls", "mkdir", "addContentToFile", "ls",
         "readContentFromFile"]
        [[], ["/"], ["/a/b/c"], ["/a/b/c/d", "hello"], ["/"],
         ["/a/b/c/d"]]
    Output:
        [null, [], null, null, ["a"], "hello"]

    Explanation:
        fs = FileSystem()
        fs.ls("/")                              # [] (root is empty)
        fs.mkdir("/a/b/c")                       # creates a, a/b, a/b/c
        fs.addContentToFile("/a/b/c/d", "hello") # creates file d under c
        fs.ls("/")                               # ["a"] (only top-level entry)
        fs.readContentFromFile("/a/b/c/d")       # "hello"


CONSTRAINTS
-----------
    1 <= path.length, filePath.length <= 100
    `path` and `filePath` are absolute paths that begin with '/' and do
    NOT end with '/' (except "/" itself), made up of English letters,
    digits, '/', and no `.`/`..` segments.
    1 <= content.length <= 50
    At most 300 calls total will be made to ls, mkdir, addContentToFile,
    and readContentFromFile.
    You can assume all directory names and file names consist of English
    letters and digits, and that a valid path is always passed for
    mkdir/addContentToFile/readContentFromFile (parent exists or is
    creatable, file exists for reads).


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is a design problem around a TREE, one level of nesting per '/' path
segment — the same "each node has a dict of named children" shape as a
Trie (topic 13), except each node ALSO needs to distinguish "I am a
directory" (children dict populated, no content) from "I am a file"
(content string, no children) — a Trie's nodes never carry payload
distinct from "is this a complete word," while a filesystem node must
hold either a directory's children OR a file's content, never both
simultaneously in a well-formed tree.


WHAT TO THINK ABOUT
--------------------
1. `path.split('/')` on an absolute path like `/a/b/c` gives `['', 'a',
   'b', 'c']` — the leading empty string (from splitting before the first
   '/') must be skipped when walking segments.

2. `mkdir` must create EVERY missing intermediate directory along the
   path, not just the final segment — walk segment by segment, creating a
   new directory node at each step that doesn't already exist.

3. `addContentToFile` does double duty: create-if-missing (including
   missing parent directories, same walk as `mkdir`) for the LAST
   segment specifically as a FILE node, then append content — vs.
   append-if-existing when the file is already there.

4. `ls` behaves differently for a file vs. a directory: a file path
   returns a ONE-ELEMENT list of just its own basename; a directory path
   returns the SORTED list of its immediate children's names (not a
   recursive listing).


PROGRESSIVE HINTS
------------------
Hint 1: One node type, holding EITHER a `children: dict[str, Node]` (if
        it's a directory) OR a `content: str` (if it's a file) — never
        both. Same shape as a Trie node, plus a file/directory
        distinction.

Hint 2: Write one internal helper, `_walk(path)`, that splits the path on
        '/' and walks from root, following (or creating, for
        mkdir/addContentToFile) each named child — `ls`,
        `readContentFromFile` walk WITHOUT creating; `mkdir`,
        `addContentToFile` walk WITH creating missing directories along
        the way.

Hint 3: `addContentToFile`'s LAST segment is special: it's the one that
        becomes (or already is) a FILE, not a directory — walk to its
        PARENT directory (creating intermediate dirs as needed), then
        create-or-find the file node as that parent's child.


COMPLEXITY TARGET
------------------
    mkdir / addContentToFile / readContentFromFile:  O(path depth)
    ls:                                                O(path depth +
                                                        children count log
                                                        children count) —
                                                        the sort dominates
                                                        for a directory
    Space: O(total characters across all created paths + file contents)
================================================================================
"""


class FileSystem:
    def __init__(self):
        # YOUR CODE HERE
        pass

    def ls(self, path: str) -> list[str]:
        # YOUR CODE HERE
        pass

    def mkdir(self, path: str) -> None:
        # YOUR CODE HERE
        pass

    def addContentToFile(self, filePath: str, content: str) -> None:
        # YOUR CODE HERE
        pass

    def readContentFromFile(self, filePath: str) -> str:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 009_design_in_memory_file_system_question.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    fs = FileSystem()
    ops = [
        (fs.ls("/"), []),
        (fs.mkdir("/a/b/c"), None),
        (fs.addContentToFile("/a/b/c/d", "hello"), None),
        (fs.ls("/"), ["a"]),
        (fs.readContentFromFile("/a/b/c/d"), "hello"),
    ]
    for got, want in ops:
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  got={got}  want={want}")

    # ls on a FILE path returns just its own name, not its content or a
    # directory-style listing.
    fs2 = FileSystem()
    fs2.addContentToFile("/x/y.txt", "abc")
    ok = fs2.ls("/x/y.txt") == ["y.txt"]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  ls() on a file path returns [filename]")

    # addContentToFile called twice appends, doesn't overwrite.
    fs2.addContentToFile("/x/y.txt", "def")
    ok = fs2.readContentFromFile("/x/y.txt") == "abcdef"
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  addContentToFile appends to existing content")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
