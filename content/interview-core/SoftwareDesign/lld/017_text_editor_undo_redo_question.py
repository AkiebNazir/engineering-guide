"""
================================================================================
LLD 017 · Text Editor with Undo / Redo                             [Tier 2]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement the core of a text editor: a buffer that makes typing at
the cursor cheap, selection and clipboard, and undo/redo that behaves the way
people expect from a real editor.

These are the agreed requirements.

REQUIREMENTS
------------
  1. GapBuffer(text="", gap=64): insert(pos, text); delete(pos, length) -> the
     removed text; text() -> str; len(buffer). Positions outside 0..len raise
     ValueError. Typing at the cursor must not copy the whole document.
  2. Editor(text="", clock=time.monotonic, history_limit=1000) with
     attributes text (read-only), cursor (int), selection ((start, end) or None)
     and undo_depth (int).
  3. move(pos) and select(start, end) — out-of-range positions raise
     ValueError; select puts the cursor at the end of the selection.
  4. type(text): inserts at the cursor, or REPLACES the selection.
     backspace(n=1) / delete_forward(n=1): delete before / after the cursor, or
     delete the selection. Nothing to delete -> no change and no history entry.
  5. copy() / cut() -> the copied text; paste() inserts the clipboard.
  6. undo() / redo() -> bool (False when there is nothing to do). Any new edit
     clears the redo history. Undo and redo restore the cursor.
  7. Coalescing: consecutive typing merges into one undo step per word
     ("hello world" typed key by key is two steps: "hello " and "world").
     Consecutive backspaces merge into one step. A merge never happens across
     a pause longer than 1 second (use the injected clock), a cursor move, a
     selection, undo/redo, or a paste.
  8. Typing over a selection is ONE undo step.
  9. Only the most recent history_limit steps can be undone.

  Out of scope: rendering, line wrapping, multiple cursors, collaborative
  editing, files, syntax highlighting.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * How is the text stored? What does inserting one character cost in a
    200 KB document?
  * Snapshots (Memento) or commands for undo? What does each cost in memory?
  * Where does a delete command get the text it needs to undo itself?
  * Where does merging logic live so the history stays generic?
  * Can anything change the buffer without going through the history?

FOLLOW-UPS TO PREPARE
---------------------
  multiple cursors · find/replace all as one step · very large files (piece
  table / rope) · persistent undo · collaborative editing (OT / CRDT).

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Everything inside the classes is yours to design. Add any helper classes you
want. Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

import time
from typing import Callable

Clock = Callable[[], float]


class GapBuffer:
    def __init__(self, text: str = "", gap: int = 64) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def __len__(self) -> int: raise NotImplementedError
    def insert(self, pos: int, text: str) -> None: raise NotImplementedError
    def delete(self, pos: int, length: int) -> str: raise NotImplementedError
    def text(self) -> str: raise NotImplementedError


class Editor:
    MERGE_WINDOW_S = 1.0

    def __init__(self, text: str = "", clock: Clock = time.monotonic, history_limit: int = 1000) -> None:
        # YOUR CODE HERE
        self.cursor = len(text)
        self.selection: tuple[int, int] | None = None
        raise NotImplementedError

    @property
    def text(self) -> str: raise NotImplementedError

    @property
    def undo_depth(self) -> int: raise NotImplementedError

    def move(self, pos: int) -> None: raise NotImplementedError
    def select(self, start: int, end: int) -> None: raise NotImplementedError
    def type(self, text: str) -> None: raise NotImplementedError
    def backspace(self, n: int = 1) -> None: raise NotImplementedError
    def delete_forward(self, n: int = 1) -> None: raise NotImplementedError
    def copy(self) -> str: raise NotImplementedError
    def cut(self) -> str: raise NotImplementedError
    def paste(self) -> None: raise NotImplementedError
    def undo(self) -> bool: raise NotImplementedError
    def redo(self) -> bool: raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _type_keys(ed: Editor, clock: FakeClock, text: str, dt: float = 0.1) -> None:
    for ch in text:
        clock.t += dt
        ed.type(ch)


def run_tests() -> bool:
    all_ok = True
    print("--- gap buffer ---")
    gb = GapBuffer("helo", gap=2)
    gb.insert(3, "l")
    gb.insert(0, ">> ")
    gb.insert(len(gb), "!!!!")                                  # forces the gap to grow
    removed = gb.delete(0, 3)
    all_ok &= _check("inserts anywhere, grows, deletes and returns removed text",
                     gb.text() == "hello!!!!" and removed == ">> " and len(gb) == 9)
    try:
        gb.insert(99, "x")
        ok = False
    except ValueError:
        ok = True
    all_ok &= _check("out-of-range insert rejected", ok)

    print("\n--- word-level coalescing ---")
    clock = FakeClock()
    ed = Editor(clock=clock)
    _type_keys(ed, clock, "hello world")
    all_ok &= _check("11 keystrokes -> 2 undo steps", ed.text == "hello world" and ed.undo_depth == 2)
    ed.undo()
    all_ok &= _check("undo removes 'world', cursor after 'hello '", ed.text == "hello " and ed.cursor == 6)
    ed.undo()
    all_ok &= _check("undo removes 'hello '", ed.text == "" and not ed.undo())
    ed.redo(); ed.redo()
    all_ok &= _check("redo twice restores, cursor at end", ed.text == "hello world" and ed.cursor == 11)
    all_ok &= _check("nothing more to redo", not ed.redo())

    clock = FakeClock()
    ed = Editor(clock=clock)
    _type_keys(ed, clock, "ab")
    clock.t += 5                                                # pause longer than the merge window
    _type_keys(ed, clock, "cd")
    ed.move(0)
    _type_keys(ed, clock, "X")
    all_ok &= _check("a pause and a cursor move each start a new undo step", ed.undo_depth == 3)

    print("\n--- backspace, redo invalidation, cursor restore ---")
    clock = FakeClock()
    ed = Editor("hello world", clock=clock)
    for _ in range(5):
        clock.t += 0.1
        ed.backspace()
    all_ok &= _check("5 backspaces merge into one step", ed.text == "hello " and ed.undo_depth == 1)
    ed.undo()
    all_ok &= _check("undo restores the word and the cursor", ed.text == "hello world" and ed.cursor == 11)
    ed.move(0)
    ed.backspace()
    all_ok &= _check("backspace at 0 does nothing and records nothing", ed.text == "hello world" and ed.undo_depth == 0)
    ed.type("Oh, ")
    all_ok &= _check("new edit clears redo", not ed.redo())

    print("\n--- selection, replace, clipboard ---")
    clock = FakeClock()
    ed = Editor("the quick fox", clock=clock)
    ed.select(4, 9)
    ed.type("slow")
    all_ok &= _check("typing over a selection replaces it", ed.text == "the slow fox" and ed.cursor == 8)
    ed.undo()
    all_ok &= _check("...and ONE undo restores the original", ed.text == "the quick fox" and ed.undo_depth == 0)
    ed.select(0, 3)
    cut = ed.cut()
    ed.move(len(ed.text))
    ed.type(" ")
    ed.paste()
    all_ok &= _check("cut + paste moves text", cut == "the" and ed.text == " quick fox the")
    for _ in range(3):
        ed.undo()
    all_ok &= _check("three undos (paste, space, cut) restore the original", ed.text == "the quick fox")
    ed.move(len(ed.text))
    ed.delete_forward()
    all_ok &= _check("delete_forward at the end does nothing", ed.text == "the quick fox")

    print("\n--- history limit ---")
    clock = FakeClock()
    ed = Editor(clock=clock, history_limit=3)
    for word in ("a ", "b ", "c ", "d ", "e "):
        clock.t += 10
        ed.type(word)
    undone = 0
    while ed.undo():
        undone += 1
    all_ok &= _check("only the last 3 steps can be undone", undone == 3 and ed.text == "a b ")
    return all_ok
# ================================================================= END TESTS ==


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
