"""
================================================================================
SOLUTION · LLD 017 · Text Editor with Undo / Redo                  [Tier 2]
================================================================================

THE CORE IDEA
--------------
Two independent designs hide inside "design a text editor":

    1. THE BUFFER — how text is stored so edits at the cursor are cheap.
       A Python str is immutable: typing one character into the middle of a
       200 KB document copies 200 KB. A GAP BUFFER keeps a hole at the cursor:
       typing fills the hole in O(1); moving the cursor far moves the hole
       (O(distance)); the hole doubles when full. Editors like Emacs use it;
       ropes / piece tables are the alternatives for huge files (demo 1).

    2. UNDO / REDO — the COMMAND pattern. Every edit is an object that knows
       how to execute() and undo() itself and stores only what it changed
       (the inserted text, or the text it deleted). Two stacks:
            new command -> push on undo stack, CLEAR redo stack
            undo        -> pop undo, cmd.undo(),  push on redo
            redo        -> pop redo, cmd.execute(), push on undo
       Storing a full snapshot per step (Memento) is simpler but costs O(n)
       memory per keystroke (demo 2).

What makes it feel like a real editor:
    * COALESCING: typing "hello world" key by key is two undo steps
      ("hello ", "world"), not eleven. Consecutive contiguous inserts merge
      unless a new word starts, the cursor moved, or too much time passed.
      Consecutive backspaces merge the same way.
    * COMPOSITE commands: typing over a selection is delete + insert, undone
      as ONE step.
    * Cursor and selection restored on undo/redo.
    * Bounded history (oldest steps dropped).


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. type(text), backspace(n), delete_forward(n), move(pos), select(start, end).
  2. Typing with a selection replaces it; backspace with a selection deletes it.
  3. copy() / cut() / paste() with an internal clipboard.
  4. undo() / redo() -> bool; redo cleared by any new edit.
  5. Word-level coalescing of typing and of backspacing within 1 second.
  6. History limit.
  Out of scope: rendering, line wrapping, multiple cursors, collaborative
  editing (see follow-ups), file I/O, syntax highlighting.


================================================================================
ENTITIES AND INVARIANTS
================================================================================
    GapBuffer        buf, gap_start, gap_end
                     INVARIANT: text == buf[:gap_start] + buf[gap_end:]
    Command          execute(buf) / undo(buf); cursor_before / cursor_after
       InsertText    pos, text
       DeleteText    pos, length, removed (captured on first execute)
       Composite     [commands] executed in order, undone in reverse
    History          undo deque(maxlen), redo list
                     INVARIANT: applying undo() k times then redo() k times
                     returns the exact same text and cursor
    Editor           facade: buffer, cursor, selection, clipboard, history, clock


================================================================================
GAP BUFFER TRACE · "helo", cursor between l and o, type "l"
================================================================================
    buf: [h][e][l][ _ ][ _ ][ _ ][o]      gap_start=3, gap_end=6
    insert "l" at 3 (gap already there): buf[3] = 'l'; gap_start = 4
    buf: [h][e][l][l][ _ ][ _ ][o]        text = "hell" + "o" = "hello"
    move cursor to 1: shift "ll" to the right end of the gap
    buf: [h][e][ _ ][ _ ][l][l][o]        gap_start=2... (wait: gap is at 1)
    precisely: move_gap(1) copies buf[1:4] ("ell") to buf[3:6]:
    buf: [h][ _ ][ _ ][e][l][l][o]        gap_start=1, gap_end=3


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
    Buffer        insert at cursor   move cursor    notes
    str           O(n)               O(1)           simplest; fine for small text
    gap buffer    O(1) amortised     O(distance)    great for one cursor
    rope          O(log n)           O(1)           huge files, cheap substrings
    piece table   O(pieces)          O(1)           VS Code; undo-friendly

  * Commands store deltas, not snapshots. Memento is acceptable for small
    documents or for coarse checkpoints.
  * Merge logic lives on the command (`merge(next)`), so History stays generic.
  * The editor never mutates the buffer except through commands — otherwise
    undo silently breaks.
  * Collaborative editing needs operations that can be TRANSFORMED against
    concurrent ones (OT) or a CRDT; plain undo stacks are per-user and must
    transform too.


================================================================================
COMPLEXITY
================================================================================
    type / backspace at cursor       O(k) for k characters (+ gap move)
    undo / redo                      O(size of the change)
    memory per history step          O(size of the change)


================================================================================
EDGE CASES
================================================================================
  * Backspace at position 0 / delete_forward at the end -> nothing, no history entry.
  * Undo with empty history -> False.
  * New edit after undo -> redo stack cleared.
  * Typing over a selection -> one undo step restores the selection's text.
  * Paste with empty clipboard -> nothing.
  * History limit exceeded -> oldest steps dropped; undo stops there.
  * Out-of-range move/select -> ValueError.


================================================================================
COMMON MISTAKES
================================================================================
  1. Snapshot the whole document on every keystroke.
  2. Forgetting to clear redo on a new edit.
  3. Undo implemented by "inverse operation" computed later (the deleted text
     is already gone) — capture it at execute time.
  4. Each character an undo step.
  5. Replace = two separate undo steps.
  6. Cursor not restored, so the user loses their place.
  7. Editor methods mutating the buffer directly, bypassing commands.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Multiple cursors -> commands carry a list of ranges; apply right-to-left.
  * Collaborative editing -> OT or CRDT (SystemDesign/problems/024).
  * Very large files -> piece table over a read-only original + add buffer.
  * Find / replace all -> one Composite command.
  * Persistent undo across restarts -> serialise commands (they're data).
  * Line index for "go to line" -> maintain newline positions (Fenwick tree).


================================================================================
RELATED
================================================================================
  SoftwareDesign/04_design_patterns_in_practice.md  §8 Command, Memento
  PyDSA/25_design  design browser history (two stacks)
  lld/006_kv_store_transactions (undo log)
"""

from __future__ import annotations

import random
import sys
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Protocol

Clock = Callable[[], float]


# ----------------------------------------------------------------------------
# Gap buffer
# ----------------------------------------------------------------------------
class GapBuffer:
    def __init__(self, text: str = "", gap: int = 64) -> None:
        self._buf: list[str | None] = list(text) + [None] * gap
        self._gap_start = len(text)
        self._gap_end = len(self._buf)

    def __len__(self) -> int:
        return len(self._buf) - (self._gap_end - self._gap_start)

    def _move_gap(self, pos: int) -> None:
        if pos < self._gap_start:
            n = self._gap_start - pos
            self._buf[self._gap_end - n:self._gap_end] = self._buf[pos:self._gap_start]
            self._gap_start, self._gap_end = pos, self._gap_end - n
        elif pos > self._gap_start:
            n = pos - self._gap_start
            self._buf[self._gap_start:pos] = self._buf[self._gap_end:self._gap_end + n]
            self._gap_start, self._gap_end = pos, self._gap_end + n

    def _ensure_gap(self, need: int) -> None:
        size = self._gap_end - self._gap_start
        if size >= need:
            return
        extra = max(need - size, len(self._buf))                  # double
        self._buf[self._gap_end:self._gap_end] = [None] * extra
        self._gap_end += extra

    def insert(self, pos: int, text: str) -> None:
        if not 0 <= pos <= len(self):
            raise ValueError(f"insert position {pos} outside 0..{len(self)}")
        self._move_gap(pos)
        self._ensure_gap(len(text))
        self._buf[self._gap_start:self._gap_start + len(text)] = text
        self._gap_start += len(text)

    def delete(self, pos: int, length: int) -> str:
        if length < 0 or not 0 <= pos <= pos + length <= len(self):
            raise ValueError(f"delete [{pos}, {pos + length}) outside 0..{len(self)}")
        self._move_gap(pos)
        removed = "".join(self._buf[self._gap_end:self._gap_end + length])
        self._gap_end += length
        return removed

    def slice(self, start: int, end: int) -> str:
        return self.text()[start:end]

    def text(self) -> str:
        return "".join(self._buf[:self._gap_start]) + "".join(self._buf[self._gap_end:])


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------
class Command(Protocol):
    cursor_before: int
    cursor_after: int

    def execute(self, buf: GapBuffer) -> None: ...
    def undo(self, buf: GapBuffer) -> None: ...
    def merge(self, other: Command, now: float) -> bool: ...


class InsertText:
    def __init__(self, pos: int, text: str, at: float) -> None:
        self.pos, self.text, self.at = pos, text, at
        self.cursor_before, self.cursor_after = pos, pos + len(text)

    def execute(self, buf):
        buf.insert(self.pos, self.text)

    def undo(self, buf):
        buf.delete(self.pos, len(self.text))

    def merge(self, other, now):
        """Absorb `other` (already executed) if it continues this word."""
        if not isinstance(other, InsertText) or other.pos != self.pos + len(self.text):
            return False
        if now - self.at > Editor.MERGE_WINDOW_S:
            return False
        if self.text[-1:].isspace() and not other.text[:1].isspace():
            return False                                          # a new word begins
        self.text += other.text
        self.cursor_after, self.at = other.cursor_after, now
        return True


class DeleteText:
    def __init__(self, pos: int, length: int, cursor_before: int, at: float) -> None:
        self.pos, self.length, self.at = pos, length, at
        self.removed = ""
        self.cursor_before, self.cursor_after = cursor_before, pos

    def execute(self, buf):
        self.removed = buf.delete(self.pos, self.length)

    def undo(self, buf):
        buf.insert(self.pos, self.removed)

    def merge(self, other, now):
        """Consecutive backspaces: `other` deleted the text just before ours."""
        if not isinstance(other, DeleteText) or other.pos + other.length != self.pos:
            return False
        if now - self.at > Editor.MERGE_WINDOW_S:
            return False
        self.pos, self.length = other.pos, self.length + other.length
        self.removed = other.removed + self.removed
        self.cursor_after, self.at = other.cursor_after, now
        return True


class Composite:
    def __init__(self, commands: list[Command]) -> None:
        self.commands = commands
        self.cursor_before = commands[0].cursor_before
        self.cursor_after = commands[-1].cursor_after

    def execute(self, buf):
        for c in self.commands:
            c.execute(buf)

    def undo(self, buf):
        for c in reversed(self.commands):
            c.undo(buf)

    def merge(self, other, now):
        return False


# ----------------------------------------------------------------------------
# History and editor
# ----------------------------------------------------------------------------
class History:
    def __init__(self, limit: int) -> None:
        self.undo_stack: deque[Command] = deque(maxlen=limit)
        self.redo_stack: list[Command] = []
        self.allow_merge = True

    def record(self, cmd: Command, now: float) -> None:
        self.redo_stack.clear()
        if self.allow_merge and self.undo_stack and self.undo_stack[-1].merge(cmd, now):
            return
        self.undo_stack.append(cmd)
        self.allow_merge = True


class Editor:
    MERGE_WINDOW_S = 1.0

    def __init__(self, text: str = "", clock: Clock = time.monotonic, history_limit: int = 1000) -> None:
        self._buf = GapBuffer(text)
        self._clock = clock
        self._history = History(history_limit)
        self.cursor = len(text)
        self.selection: tuple[int, int] | None = None
        self._clipboard = ""

    # -- navigation --------------------------------------------------------------------
    @property
    def text(self) -> str:
        return self._buf.text()

    def move(self, pos: int) -> None:
        self._check(pos)
        self.cursor, self.selection = pos, None
        self._history.allow_merge = False

    def select(self, start: int, end: int) -> None:
        self._check(start)
        self._check(end)
        start, end = min(start, end), max(start, end)
        self.selection = (start, end) if start != end else None
        self.cursor = end
        self._history.allow_merge = False

    # -- editing -----------------------------------------------------------------------
    def type(self, text: str) -> None:
        if not text:
            return
        now = self._clock()
        cmds: list[Command] = []
        pos = self.cursor
        if self.selection:
            start, end = self.selection
            cmds.append(DeleteText(start, end - start, self.cursor, now))
            pos = start
        cmds.append(InsertText(pos, text, now))
        self._run(cmds[0] if len(cmds) == 1 else Composite(cmds), now)

    def backspace(self, n: int = 1) -> None:
        if self.selection:
            return self._delete_selection()
        n = min(n, self.cursor)
        if n > 0:
            now = self._clock()
            self._run(DeleteText(self.cursor - n, n, self.cursor, now), now)

    def delete_forward(self, n: int = 1) -> None:
        if self.selection:
            return self._delete_selection()
        n = min(n, len(self._buf) - self.cursor)
        if n > 0:
            now = self._clock()
            cmd = DeleteText(self.cursor, n, self.cursor, now)
            self._history.allow_merge = False                       # forward deletes don't merge with backspaces
            self._run(cmd, now)

    def copy(self) -> str:
        if self.selection:
            self._clipboard = self._buf.slice(*self.selection)
        return self._clipboard

    def cut(self) -> str:
        copied = self.copy()
        if self.selection:
            self._delete_selection()
        return copied

    def paste(self) -> None:
        if self._clipboard:
            self._history.allow_merge = False
            self.type(self._clipboard)
            self._history.allow_merge = False

    # -- history -----------------------------------------------------------------------
    def undo(self) -> bool:
        if not self._history.undo_stack:
            return False
        cmd = self._history.undo_stack.pop()
        cmd.undo(self._buf)
        self._history.redo_stack.append(cmd)
        self.cursor, self.selection = cmd.cursor_before, None
        self._history.allow_merge = False
        return True

    def redo(self) -> bool:
        if not self._history.redo_stack:
            return False
        cmd = self._history.redo_stack.pop()
        cmd.execute(self._buf)
        self._history.undo_stack.append(cmd)
        self.cursor, self.selection = cmd.cursor_after, None
        self._history.allow_merge = False
        return True

    @property
    def undo_depth(self) -> int:
        return len(self._history.undo_stack)

    # -- internals ---------------------------------------------------------------------
    def _run(self, cmd: Command, now: float) -> None:
        cmd.execute(self._buf)
        self._history.record(cmd, now)
        self.cursor, self.selection = cmd.cursor_after, None

    def _delete_selection(self) -> None:
        start, end = self.selection
        now = self._clock()
        self._history.allow_merge = False
        self._run(DeleteText(start, end - start, self.cursor, now), now)
        self._history.allow_merge = False

    def _check(self, pos: int) -> None:
        if not 0 <= pos <= len(self._buf):
            raise ValueError(f"position {pos} outside 0..{len(self._buf)}")


# ===================================================================== TESTS ==
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


class SnapshotEditor:
    """Memento approach: store the full text before every edit."""

    def __init__(self) -> None:
        self.text = ""
        self.undo_stack: list[str] = []
        self.redo_stack: list[str] = []

    def apply(self, new_text: str) -> None:
        self.undo_stack.append(self.text)
        self.redo_stack.clear()
        self.text = new_text

    def undo(self) -> None:
        if self.undo_stack:
            self.redo_stack.append(self.text)
            self.text = self.undo_stack.pop()

    def redo(self) -> None:
        if self.redo_stack:
            self.undo_stack.append(self.text)
            self.text = self.redo_stack.pop()


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: type 20,000 characters into the middle of a 200 KB document ---")
    base = "x" * 200_000
    keys = "lorem ipsum " * 1667
    keys = keys[:20_000]
    timings = {}
    s = base
    mid = len(s) // 2
    start = time.perf_counter()
    for i, ch in enumerate(keys):
        s = s[:mid + i] + ch + s[mid + i:]
    timings["str rebuild"] = time.perf_counter() - start
    lst = list(base)
    start = time.perf_counter()
    for i, ch in enumerate(keys):
        lst.insert(mid + i, ch)
    timings["list.insert"] = time.perf_counter() - start
    gb = GapBuffer(base)
    start = time.perf_counter()
    for i, ch in enumerate(keys):
        gb.insert(mid + i, ch)
    timings["gap buffer"] = time.perf_counter() - start
    for name, sec in timings.items():
        print(f"      {name:<12}: {sec * 1000:8.1f} ms")
    all_ok &= _check("all three produce the same text", s == "".join(lst) == gb.text())
    all_ok &= _check("gap buffer beats rebuilding the string", timings["gap buffer"] < timings["str rebuild"])
    print("      (rebuilding the string and list.insert both shift everything after the cursor on"
          " every key: O(n) per key. The gap buffer is O(1) amortised per key.)")

    print("\n--- DEMO 2: 3,000 small random edits to a 5,000-char document, vs a snapshot-per-step oracle ---")
    rng = random.Random(17)
    clock = FakeClock()
    doc = "".join(rng.choice("abcdefgh \n") for _ in range(5_000))
    ed = Editor(doc, clock=clock, history_limit=10_000)
    oracle = SnapshotEditor()
    oracle.text = doc
    mismatches = 0
    for _ in range(3000):
        clock.t += 5                                           # no merging: one step per edit
        op = rng.random()
        if op < 0.45:
            pos = rng.randint(0, len(ed.text))
            chunk = "".join(rng.choice("abc \n") for _ in range(rng.randint(1, 30)))
            ed.move(pos)
            ed.type(chunk)
            oracle.apply(oracle.text[:pos] + chunk + oracle.text[pos:])
        elif op < 0.7 and ed.text:
            a = rng.randint(0, len(ed.text) - 1)
            b = min(len(ed.text), a + rng.randint(1, 30))           # small deletions, like real editing
            ed.select(a, b)
            ed.backspace()
            oracle.apply(oracle.text[:a] + oracle.text[b:])
        elif op < 0.85:
            ed.undo()
            oracle.undo()
        else:
            ed.redo()
            oracle.redo()
        mismatches += ed.text != oracle.text
    cmd_bytes = sum(len(getattr(c, "text", "")) + len(getattr(c, "removed", ""))
                    + sum(len(getattr(x, "text", "")) + len(getattr(x, "removed", "")) for x in getattr(c, "commands", []))
                    for c in list(ed._history.undo_stack) + ed._history.redo_stack)
    snap_bytes = sum(len(t) for t in oracle.undo_stack + oracle.redo_stack)
    print(f"      history memory: commands {cmd_bytes:,} chars vs snapshots {snap_bytes:,} chars "
          f"({snap_bytes / max(cmd_bytes, 1):.0f}x) for a {len(ed.text):,}-char document")
    all_ok &= _check(f"command-based editor matches the snapshot oracle after every step ({mismatches} mismatches)",
                     mismatches == 0)
    all_ok &= _check("commands use far less history memory", cmd_bytes * 10 < snap_bytes)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
