# Memory Management & Garbage Collection — Stack, Heap, and Who Frees What

Every value your program creates occupies memory, and every byte of it has to be given
back at some point — or the program grows until the operating system kills it. How
memory is handed out and taken back is one of the deepest design decisions in a
language: it decides whether you can have use-after-free bugs, whether your service
pauses, how much RAM it needs, and why the same algorithm is 20× faster in one
language than another. This chapter starts from first principles — what a process's
memory looks like, what the stack and the heap are, and the three ways memory can be
freed — then goes as deep as interviews and production debugging go: how allocators
fight fragmentation, how reference counting and tracing collectors work (you'll build
both), why concurrent collectors need write barriers, how Go's `GOGC` and `GOMEMLIMIT`
trade memory for CPU, what escape analysis decides, and how to find a leak in a
garbage-collected language. Every number was measured on a 4-core Linux VM (Python
3.11, Go 1.24, glibc) by the program shown beside it. Corrections of common myths are
marked **Precision note**. A breakdown of what Junior through Staff+ engineers are
expected to know closes the chapter, just before the interview checklist.

## Foundations — Where Does Memory Come From, and Where Does It Go?

### Why Memory Management Exists

A program asks for memory constantly: a new string, a list that grows, a request object,
a node in a tree. Physical RAM is finite and shared, so memory that is no longer needed
must be returned and reused. The hard part is the word **"needed"**: the program knows
when it *creates* a value, but the moment a value becomes useless — when nothing will
ever read it again — is spread across the whole program. Get that moment wrong in one
direction and you have a **leak** (memory kept forever); in the other, a
**use-after-free** (memory reused while something still points at it), which corrupts
data and is one of the most exploited classes of security bug.

Every language picks an answer to "who decides when to free?":

| Strategy | Who frees | Languages | Cost you pay |
|---|---|---|---|
| **Manual** | The programmer calls `free` / `delete` | C, C++ (raw) | Leaks, double frees and use-after-free are your bugs |
| **Ownership / RAII** | The compiler inserts the free where the owner goes out of scope | Rust, C++ smart pointers | You must satisfy ownership rules at compile time |
| **Reference counting** | The runtime frees when a counter hits zero | CPython, Swift, Objective-C, C++ `shared_ptr` | A counter update on every copy; cycles need extra help |
| **Tracing garbage collection** | The runtime periodically finds everything reachable and frees the rest | Go, Java, C#, JavaScript, (CPython for cycles) | CPU for the collector, extra memory headroom, possible pauses |

### What a Process's Memory Looks Like

Recall from [Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md) §5 that every process sees its own
**virtual address space**. The OS lays it out in regions, each with its own purpose and
permissions:

```arch
%% caption: A process's address space, high addresses at the top: code and globals are fixed at start-up, the heap grows up, the stack grows down, and big allocations and libraries are mapped in between.
grid 200x80
node text "Code (.text)" at 0,5 shape=card color=orange icon=code sub="read + execute; your compiled functions"
node rodata "Read-only data" at 0,4 shape=card color=amber icon=doc sub="string literals, constants"
node data "Globals (.data, .bss)" at 0,3 shape=card color=blue icon=memory sub="initialised and zeroed globals"
node heap "Heap" at 0,2 shape=card color=green icon=layers sub="malloc / new; grows upward"
node mmap "Memory-mapped region" at 0,1 shape=card color=teal icon=storage sub="big allocations, shared libraries"
node stack "Stack" at 0,0 shape=card color=purple icon=layers sub="one frame per call; grows downward"
node hi "high addresses" at 1,0 shape=text
node lo "low addresses" at 1,5 shape=text
stack .. hi
text .. lo
```

You can watch this layout in a running program. This C program prints where each kind
of value lives and looks each address up in its own `/proc/self/maps`:

```c
// Where things live in a running process: print addresses, then find each
// one in this process's own memory map (/proc/self/maps).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int initialized = 42;        // .data
int zeroed;                  // .bss
const char *msg = "hello";   // the string literal lives in read-only data

static const char *region(void *p) {
    static char name[300];
    unsigned long a = (unsigned long)p, lo, hi;
    char line[512], perms[8];
    FILE *f = fopen("/proc/self/maps", "r");
    strcpy(name, "?");
    while (fgets(line, sizeof line, f)) {
        char path[256] = "[anonymous mmap]";
        sscanf(line, "%lx-%lx %7s %*s %*s %*s %255s", &lo, &hi, perms, path);
        if (lo <= a && a < hi) { snprintf(name, sizeof name, "%s %s", perms, strrchr(path, '/') ? strrchr(path, '/') + 1 : path); break; }
    }
    fclose(f);
    return name;
}

int main(void) {
    int local = 7;
    void *small = malloc(64);
    void *large = malloc(64 << 20);          // 64 MB: glibc uses mmap above 128 KB
    struct { const char *what; void *p; } rows[] = {
        {"main (code)", (void *)main}, {"string literal", (void *)msg},
        {"initialized global", &initialized}, {"zeroed global", &zeroed},
        {"malloc(64)", small}, {"malloc(64 MB)", large}, {"local variable", &local},
    };
    for (int i = 0; i < 7; i++)
        printf("%#014lx  %-20s -> %s\n", (unsigned long)rows[i].p, rows[i].what, region(rows[i].p));
    free(small); free(large);
    return 0;
}
```

```text
$ gcc -O0 -no-pie -Wall -o layout layout.c && ./layout
0x00000040153c  main (code)          -> r-xp layout
0x000000402004  string literal       -> r--p layout
0x000000404060  initialized global   -> rw-p layout
0x0000004040a0  zeroed global        -> rw-p layout
0x0000372e42a0  malloc(64)           -> rw-p [heap]
0x7fbf04bff010  malloc(64 MB)        -> rw-p [anonymous mmap]
0x7ffee79d6f58  local variable       -> rw-p [stack]
```

Every row is a different lifetime policy: code and globals live as long as the process;
heap and mmap memory lives until someone frees it; a local variable lives exactly as
long as its function call. Note the permissions too: code is `r-x` (executable, not
writable), which is why injected data can't simply be run as code.

### Stack vs. Heap — the Distinction This Chapter Assumes

- **The stack** holds one **frame** per active function call: its parameters, local
  variables, saved registers and return address. Calling a function pushes a frame
  (move one register, the *stack pointer*); returning pops it. Allocation and freeing
  are a single instruction each, the memory is always hot in cache, and the lifetime is
  automatic — which is exactly its limitation: **a value on the stack dies when its
  function returns.**
- **The heap** holds everything whose lifetime isn't tied to one call: an object
  returned to the caller, stored in a global map, sent to another thread. Heap memory is
  handed out by an **allocator** (§3) and must be freed by someone — the programmer, the
  compiler, or a garbage collector.

| | Stack | Heap |
|---|---|---|
| Lifetime | Exactly the function call | Until freed or collected |
| Allocate / free | Move the stack pointer: ~1 instruction | Allocator call: tens of ns, plus GC work later |
| Size | Small and fixed per thread (8 MB main thread on Linux; Go goroutines start at 2 KB and grow) | Up to available memory |
| Failure mode | Stack overflow from deep recursion | Leaks, fragmentation, GC pressure |
| Who decides placement | Compiler (escape analysis in Go/Java, §11) | Compiler or programmer |

**Precision note:** "primitives go on the stack, objects go on the heap" is a rule of
thumb from C and early Java, not a law. In CPython *every* value, even an `int`, is a
heap object and only pointers live in the interpreter's frames. In Go and modern JVMs
the compiler decides per allocation, and a struct created with `&T{}` can stay on the
stack if it never escapes (§11).

### Vocabulary You'll Meet Below, in One Table

| Term | Meaning |
|---|---|
| Frame | One function call's slice of the stack |
| Allocator | The code behind `malloc`/`new` that carves heap memory into blocks (§3) |
| Size class | A fixed block size requests are rounded up to (§3) |
| Internal / external fragmentation | Waste inside a block / free memory split into holes too small to use (§3–§4) |
| Root | A pointer the program can use directly: globals, stack slots, registers (§7) |
| Reachable | Findable by following pointers from a root; everything else is garbage |
| Reference count | Number of pointers to an object; freed at zero (§6) |
| Mark-sweep | Tracing GC: mark everything reachable, free the rest (§7) |
| Generational GC | Collecting young objects more often, because most die young (§8) |
| Moving / compacting GC | A collector that relocates live objects to remove holes (§8) |
| Tri-colour marking | White / grey / black bookkeeping that lets marking run in pieces (§9) |
| Write barrier | Code the compiler adds to pointer writes so a concurrent collector stays correct (§9) |
| Stop-the-world (STW) pause | A moment when all program threads are halted for the collector |
| Escape analysis | Compiler proof that a value can't outlive its function, so it can live on the stack (§11) |
| RSS | Resident set size: the physical memory a process actually uses (§13) |

## 1. The Call Stack in Depth

A call does four things: push the arguments (or put them in registers), push the return
address, move the stack pointer down to make room for locals, and jump. A return undoes
them. Because each frame sits directly below its caller's, the stack is a perfect LIFO
that needs no bookkeeping — and a **debugger's backtrace, a panic's stack trace and a
profiler's flame graph** are all just walks up this chain of frames.

What each language does when the stack runs out:

```python
import sys
print('recursion limit:', sys.getrecursionlimit())
def f(n): return 0 if n == 0 else 1 + f(n - 1)
try: f(5000)
except RecursionError as e: print('f(5000):', type(e).__name__, '-', e)
sys.setrecursionlimit(100_000); print('f(50000) with a raised limit =', f(50_000))
```

```text
recursion limit: 1000
f(5000): RecursionError - maximum recursion depth exceeded
f(50000) with a raised limit = 50000
```

```c
// 1 KB of locals per frame, on the default 8 MB main-thread stack (ulimit -s = 8192 KB)
static int depth(int n) { volatile char frame[1024]; frame[0] = (char)n; return n == 0 ? 0 : 1 + depth(n - 1) + frame[0] * 0; }
```

```text
$ ./so 5000
depth 5000 ok: 5000
$ ./so 20000
Segmentation fault      (exit code 139)
```

```go
// Goroutine stacks start at 2 KB and grow by copying to a bigger block.
func depth(n int) int {
	var pad [8]int64 // make each frame a little bigger
	pad[n%8] = int64(n)
	if n == 0 {
		return int(pad[0])
	}
	return depth(n-1) + int(pad[n%8]&0)
}
```

```text
stack in use before: 320 KB
stack in use at 1,000,000 frames deep: 128 MB
```

- **CPython** counts frames and raises `RecursionError` at a configurable limit (1,000
  by default). Raising the limit works until the C stack underneath runs out, then the
  interpreter crashes; that's why the DSA module converts deep recursion to explicit
  stacks ([Python for Coding Interviews](08_python_for_coding_interviews_deep_dive.md) §6).
- **C** has a fixed stack (8 MB here). Overflowing it hits a guard page the OS left
  unmapped below the stack, and the process dies with `SIGSEGV`. 8 MB / 1 KB per frame
  is ~8,000 frames: 5,000 works, 20,000 crashes.
- **Go** starts each goroutine with a 2 KB stack and, when a function's prologue sees
  the stack is too small, allocates one twice the size and copies the old one over
  (fixing up pointers into it). A million frames deep costs 128 MB of stack and works;
  the default ceiling is 1 GB per goroutine. This is what makes a million goroutines
  affordable.

**Tail calls:** a call that is the very last thing a function does can reuse the
caller's frame. Scheme and some compilers guarantee it; **CPython, Go and Java do not**,
so "just make it tail-recursive" does not fix stack depth in interview languages.

## 2. What Can and Can't Live on the Stack

A value can live in a frame only if the compiler can prove nothing will use it after the
function returns. Returning a pointer to a local, storing it in a global or a heap
object, capturing it in a closure that outlives the call, or sending it to another
goroutine all break that proof. C lets you do it anyway, and the result is a *dangling
pointer* to a frame that the next call will overwrite. Garbage-collected languages
never let that happen: the compiler moves such values to the heap (§11), which is safe
but costs an allocation.

This is also why the stack is **per thread**: each thread runs its own sequence of
calls. Heap objects are shared between threads, which is why the heap, not the stack,
is where data races happen ([Concurrency](05_concurrency_deep_dive.md) Foundations).

## 3. The Heap and How Allocators Work

`malloc(n)` must find `n` free bytes quickly, and `free(p)` must make them reusable. The
allocator gets large regions from the OS (`brk` to grow the classic heap, `mmap` for
anything big — the 64 MB block in the Foundations example came straight from `mmap`)
and carves them into blocks.

**The core problem is fragmentation**, in two flavours:

- **Internal fragmentation** — waste *inside* a block, because requests are rounded up.
- **External fragmentation** — enough free memory in total, but split into holes too
  small for the request (§4 builds an allocator and shows it).

**The core technique is size classes.** Real allocators don't search a list of
arbitrary-sized holes for small objects. They keep separate pools for a few dozen fixed
sizes (8, 16, 24, 32, 48, 64, … bytes), round each request up to the nearest class, and
serve it from a pool of same-sized slots. Allocation becomes "pop a free slot from this
class's list" — fast, and immune to external fragmentation within a class — at the
price of internal fragmentation. You can measure the rounding in Go:

```go
// Allocators round every request up to a size class.
package main

import (
	"fmt"
	"runtime"
)

var keep [][]byte

func main() {
	for _, size := range []int{8, 24, 33, 49, 100, 1000, 1025} {
		keep = make([][]byte, 0, 100_000)
		runtime.GC()
		var before, after runtime.MemStats
		runtime.ReadMemStats(&before)
		for i := 0; i < 100_000; i++ {
			keep = append(keep, make([]byte, size))
		}
		runtime.ReadMemStats(&after)
		per := float64(after.TotalAlloc-before.TotalAlloc) / 100_000
		fmt.Printf("asked %5d B  got %5.0f B  (%.0f%% wasted)\n", size, per, 100*(per-float64(size))/per)
	}
}
```

```text
asked     8 B  got     8 B  (0% wasted)
asked    24 B  got    24 B  (0% wasted)
asked    33 B  got    48 B  (31% wasted)
asked    49 B  got    64 B  (23% wasted)
asked   100 B  got   112 B  (11% wasted)
asked  1000 B  got  1024 B  (2% wasted)
asked  1025 B  got  1152 B  (11% wasted)
```

One byte over a class boundary (33 instead of 32, 1,025 instead of 1,024) costs up to a
third more memory. For a struct allocated millions of times, trimming it under a
boundary is a real saving.

**How production allocators are organised.** They all combine size classes with
**per-thread (or per-CPU) caches**, because a single global lock on `malloc` would
serialise every thread in the program:

| Allocator | Used by | Shape |
|---|---|---|
| glibc `ptmalloc2` | Default `malloc` on most Linux | Several *arenas* to reduce lock contention, bins of free chunks by size, `mmap` above a threshold (128 KB by default) |
| `tcmalloc` | Google's C++; the model for Go's allocator | Per-thread (now per-CPU) caches of small size classes, a central free list, page heap for large spans |
| `jemalloc` | FreeBSD, Redis, many services | Per-thread caches, arenas, size classes tuned to limit fragmentation over long runs |
| Go runtime | Every Go program | `mcache` per P (no locks), `mcentral` per size class, `mheap` of 8 KB pages; ~68 size classes up to 32 KB |
| `pymalloc` | CPython objects ≤ 512 bytes | Pools of equal-sized blocks inside large arenas; bigger requests go to `malloc` |

**Precision note:** `free()` rarely returns memory to the operating system. The freed
block goes back on the allocator's free list for reuse, so a process's RSS usually stays
near its peak even after it frees most of its data. That is expected, not a leak;
allocators return whole pages or spans only when they are completely empty (Go's
scavenger does this in the background).

## 4. Build One: a Free-List Allocator

To see fragmentation rather than read about it, here is a complete first-fit allocator
over a 1,000-byte arena. Free holes are kept in a list sorted by address; `malloc` takes
the first hole big enough and splits it; `free` returns the block and optionally
**coalesces** it with adjacent holes.

```python
"""A first-fit free-list allocator over a 1,000-byte arena, with coalescing.

Blocks are (start, size). free_list is kept sorted by address so that freeing
can merge a block with its neighbours.
"""
import random


class Arena:
    def __init__(self, size):
        self.size = size
        self.free_list = [(0, size)]          # one big hole
        self.used = {}                        # start -> size

    def malloc(self, n):
        for i, (start, size) in enumerate(self.free_list):
            if size >= n:                     # first fit
                if size == n:
                    self.free_list.pop(i)
                else:                         # split: keep the tail as a hole
                    self.free_list[i] = (start + n, size - n)
                self.used[start] = n
                return start
        return None                           # no single hole is big enough

    def free(self, start, coalesce=True):
        n = self.used.pop(start)
        self.free_list.append((start, n))
        self.free_list.sort()
        if coalesce:                          # merge adjacent holes
            merged = []
            for s, sz in self.free_list:
                if merged and merged[-1][0] + merged[-1][1] == s:
                    merged[-1] = (merged[-1][0], merged[-1][1] + sz)
                else:
                    merged.append((s, sz))
            self.free_list = merged

    def stats(self):
        free = sum(sz for _, sz in self.free_list)
        largest = max((sz for _, sz in self.free_list), default=0)
        return free, largest, len(self.free_list)


def run(coalesce):
    rng = random.Random(7)
    a = Arena(1000)
    live, failures = [], 0
    for step in range(2000):
        if live and rng.random() < 0.5:
            a.free(live.pop(rng.randrange(len(live))), coalesce)
        else:
            p = a.malloc(rng.choice([8, 16, 24, 64, 120]))
            if p is None:
                failures += 1
            else:
                live.append(p)
    free, largest, holes = a.stats()
    print(f"coalesce={coalesce!s:5}  free {free:4} B in {holes:3} holes, "
          f"largest hole {largest:4} B, failed mallocs {failures}")


run(coalesce=False)
run(coalesce=True)

# External fragmentation in one picture: plenty free, nothing contiguous.
a = Arena(100)
blocks = [a.malloc(10) for _ in range(10)]
for b in blocks[::2]:
    a.free(b)
free, largest, holes = a.stats()
print(f"\n10 x 10 B allocated, every other one freed: {free} B free, largest hole {largest} B")
print("malloc(20) ->", a.malloc(20))
```

```text
coalesce=False  free  800 B in  42 holes, largest hole   64 B, failed mallocs 187
coalesce=True   free  360 B in   5 holes, largest hole  112 B, failed mallocs 44

10 x 10 B allocated, every other one freed: 50 B free, largest hole 10 B
malloc(20) -> None
```

What the run shows:

- **Without coalescing, the arena shatters.** After 2,000 random operations, 800 of the
  1,000 bytes are free — yet split into 42 holes, none larger than 64 bytes, and 187
  requests failed. Every split creates a smaller hole, and nothing ever glues them back.
- **Coalescing fixes most of it**: 5 holes, largest 112 bytes, 44 failures (and more
  memory in use, because more requests succeeded).
- **The last line is external fragmentation in its purest form**: half the arena is free,
  and a 20-byte request still fails, because no two free bytes are adjacent.

The design choices real allocators make follow directly: **first fit** is fast but
fragments the front of the heap; **best fit** (smallest adequate hole) leaves fewer
useless slivers but must search more; **boundary tags** (a size header and footer on
every block) make coalescing O(1) instead of the sort used here; and **size classes**
(§3) sidestep the problem for small objects. A **compacting** garbage collector (§8)
solves it outright by moving live objects together — something `malloc` can never do,
because C code holds raw addresses.

## 5. Manual Memory Management and Its Failure Modes

In C and C++ without smart pointers, the programmer frees memory explicitly, and every
mistake is a bug the compiler won't catch:

| Bug | What happens | Typical consequence |
|---|---|---|
| **Leak** | Memory is never freed | Process grows until OOM-killed (`01` §5) |
| **Use-after-free** | Memory is used after being freed and possibly reused | Silent corruption; attackers place their own data in the reused block |
| **Double free** | The same block is freed twice | Allocator metadata corrupted; often exploitable |
| **Buffer overflow** | Writing past the end of a block | Overwrites neighbours or allocator metadata |
| **Uninitialised read** | Using memory before writing it | Leaks old data (the Heartbleed class of bug is an over-read) |

These are not rare. Microsoft and the Chromium project have each reported that around
70% of their serious security vulnerabilities are memory-safety bugs, which is the main
argument behind the industry's move to memory-safe languages.

**The two modern answers:**

- **RAII and ownership.** In C++, a `unique_ptr` frees its object in its destructor when
  it goes out of scope; `shared_ptr` reference-counts (§6). Rust makes ownership a
  compile-time rule: every value has exactly one owner, borrows can't outlive it, and
  the compiler inserts the free. There is no collector and no runtime cost, and the
  bugs in the table above become compile errors.
- **Garbage collection**, the rest of this chapter.

**Tools when you do write C/C++:** AddressSanitizer (`-fsanitize=address`) catches
use-after-free, double free and overflows at run time with ~2× slowdown — run tests
under it; Valgrind finds leaks; fuzzers find the inputs that trigger them.

## 6. Reference Counting (How CPython Frees Almost Everything)

Every object carries a count of the references to it. Copying a reference increments
it; dropping one decrements it; at zero the object is freed immediately — and anything
it pointed to is decremented in turn.

```python
import gc, sys, weakref

class Node:
    def __init__(self, name):
        self.name, self.other = name, None
    def __del__(self):
        print(f"  freed {self.name}")

print("1) Reference counting frees the moment the last reference goes")
a = Node("a")
print("  refcount of a:", sys.getrefcount(a) - 1)  # -1: getrefcount's own argument
b = a
print("  after b = a  :", sys.getrefcount(a) - 1)
del a
print("  after del a  : still alive through b")
del b
print("  after del b  : (freed above, immediately)")

print("2) A cycle keeps both counts above zero")
gc.disable()
x, y = Node("x"), Node("y")
x.other, y.other = y, x
del x, y
print("  deleted both names; nothing freed yet")
print("  gc.collect() found", gc.collect(), "unreachable objects")
gc.enable()

print("3) A weak reference doesn't count")
p = Node("parent")
child = Node("child")
child.other = weakref.ref(p)
del p
print("  child's weakref now returns:", child.other())
del child
```

```text
1) Reference counting frees the moment the last reference goes
  refcount of a: 1
  after b = a  : 2
  after del a  : still alive through b
  freed a
  after del b  : (freed above, immediately)
2) A cycle keeps both counts above zero
  deleted both names; nothing freed yet
  freed x
  freed y
  gc.collect() found 2 unreachable objects
3) A weak reference doesn't count
  freed parent
  child's weakref now returns: None
  freed child
```

**What reference counting gets right:**

- **Prompt, predictable freeing.** Memory (and resources like file handles) is released
  the instant the last reference disappears — no pause, no headroom, and a working set
  that stays small and cache-warm.
- **Simplicity.** The work is spread evenly across the program's own operations.

**What it gets wrong:**

- **Cycles leak.** In part 2, `x` and `y` point at each other, so both counts stay at 1
  after the program drops them. Doubly linked lists, parent pointers, graphs, an object
  holding a callback that refers back to it — all form cycles. CPython therefore adds a
  **cycle-detecting tracing collector** (§8) on top; Swift instead makes you break
  cycles with `weak` references, which is what part 3 shows: a weak reference points
  at an object without keeping it alive.
- **Every pointer copy writes memory.** Passing an object to a function, storing it in a
  list, iterating over a list — each is a count update, so even *reading* data writes to
  it. That dirties cache lines, and after `fork()` it defeats copy-on-write (`01` §6):
  a child process that only reads its parent's objects still copies the pages, because
  touching an object changes its count. (Instagram hit the same effect from the cycle
  collector touching every object's header, disabled the collector in its forked web
  workers, and contributed `gc.freeze()`, added in Python 3.7, to exclude start-up
  objects from collection.)
- **Thread safety is expensive.** With several threads, each increment must be atomic.
  CPython's GIL exists largely so that reference counts can be updated without atomics
  ([Concurrency](05_concurrency_deep_dive.md) §6); the free-threaded build uses biased reference
  counting (cheap non-atomic updates for the owning thread) to avoid that cost.
- **Freeing can cascade.** Dropping the last reference to the head of a
  million-node linked list frees a million objects on the spot — a pause after all.

## 7. Tracing Garbage Collection: Mark and Sweep

A tracing collector ignores counts and asks a different question: **what can the
program still reach?** Start from the **roots** — global variables, every thread's
stack slots and registers — and follow every pointer. Anything reached is live; anything
not reached can never be used again, so it is garbage, cycles included.

The simplest tracing collector does it in two phases with the program stopped:

1. **Mark**: traverse the object graph from the roots, marking what you visit.
2. **Sweep**: walk the whole heap and free every unmarked object.

Here it is, complete, over a toy heap:

```python
class Obj:
    def __init__(self, name):
        self.name, self.refs = name, []

    def __repr__(self):
        return self.name


class Heap:
    def __init__(self):
        self.objects, self.roots = [], []

    def new(self, name):
        o = Obj(name)
        self.objects.append(o)
        return o

    def mark_sweep(self):
        marked, stack = set(), list(self.roots)
        while stack:                                   # mark: everything reachable
            o = stack.pop()
            if id(o) not in marked:
                marked.add(id(o))
                stack.extend(o.refs)
        dead = [o for o in self.objects if id(o) not in marked]
        self.objects = [o for o in self.objects if id(o) in marked]   # sweep
        return dead


h = Heap()
root, a, b, c, d = (h.new(n) for n in "RABCD")
h.roots = [root]
root.refs = [a]
a.refs = [b]
c.refs, d.refs = [d], [c]                              # C <-> D: a cycle nobody points to
print("mark-sweep freed:", h.mark_sweep(), "| survivors:", h.objects)
```

```text
mark-sweep freed: [C, D] | survivors: [R, A, B]
```

The unreachable cycle `C ↔ D` is collected — exactly the case reference counting (§6)
can't handle. Note the mark phase uses an explicit stack, not recursion: a real
collector must not overflow while traversing a million-long linked list.

**The costs, and why every later design exists:**

- **Mark cost is proportional to live data**, sweep cost to the whole heap. A collector
  that runs often on a large live set burns CPU re-marking the same long-lived objects —
  the motivation for **generations** (§8).
- **Stopping the program** for the whole mark and sweep gives pauses proportional to
  heap size — seconds on large heaps. The motivation for **incremental and concurrent
  marking** (§9).
- **Freed objects stay where they were**, leaving holes (external fragmentation, §4).
  The motivation for **compacting and copying** collectors (§8).
- **The collector needs headroom.** Garbage accumulates between collections, so a GC'd
  program needs more memory than its live set — the knob §10 measures.

**Precision note:** a tracing GC collects *unreachable* memory, not *unused* memory. An
object you'll never touch again but still reference from a global map is reachable, so
it's never freed. That's what a leak in Python, Go or Java looks like (§12).

## 8. Copying, Compacting, and Generational Collection

**Copying (semispace) collection.** Split the heap into two halves. Allocate from one
("from-space") by bumping a pointer — allocation is just an add and a bounds check. When
it fills, copy every *reachable* object into the other half, packed together, update the
pointers, and swap roles. Garbage is never touched at all: cost is proportional only to
live data, and the result has zero fragmentation. The price is half the memory sitting
idle, and moving objects means the runtime must be able to find and fix every pointer
(a *precise* collector) — impossible for C, natural for Java.

**Mark-compact** gets the same no-holes result in place: mark, then slide live objects
together. Slower than copying, but no wasted half.

**The generational hypothesis** — *most objects die young* — is the most important
empirical fact in garbage collection. Request objects, temporary strings and iterators
live for microseconds; caches and configuration live for hours. So split the heap by
age:

- A small **young generation** (the *nursery*) takes all new allocations and is
  collected often with a copying collector. Since most of it is dead, each young
  collection copies little and frees a lot, quickly.
- Objects that survive a few young collections are **promoted** to the **old
  generation**, collected rarely.
- The catch: an old object may point to a young one, and a young collection doesn't scan
  the old generation. So the compiler adds a **write barrier** to pointer stores that
  records old-to-young pointers (a *remembered set* or *card table*), and those entries
  act as extra roots.

**CPython's cycle collector is generational too.** Reference counting frees almost
everything; the tracing collector only looks for cycles, among container objects, in
three generations. You can watch it:

```python
import gc, resource, time

def peak_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Linux reports KB

class N:
    __slots__ = ("ref",)

def churn(n, cyclic):
    for _ in range(n):
        a, b = N(), N()
        if cyclic:
            a.ref, b.ref = b, a       # a 2-object cycle: refcounting alone can't free it

print("thresholds:", gc.get_threshold())
for cyclic in (False, True):
    gc.collect()
    before = [s["collections"] for s in gc.get_stats()]
    t = time.perf_counter()
    churn(1_000_000, cyclic)
    dt = time.perf_counter() - t
    after = [s["collections"] for s in gc.get_stats()]
    print(f"cyclic={cyclic!s:5} gc on : {dt*1000:4.0f} ms, collections per generation "
          f"{[a - b for a, b in zip(after, before)]}, peak RSS {peak_mb():4.0f} MB")
gc.disable()
t = time.perf_counter()
churn(1_000_000, True)
dt = time.perf_counter() - t
print(f"cyclic=True  gc off: {dt*1000:4.0f} ms, peak RSS {peak_mb():4.0f} MB, "
      f"then one collect() frees {gc.collect()} objects")
```

```text
thresholds: (700, 10, 10)
cyclic=False gc on :  154 ms, collections per generation [0, 0, 0], peak RSS    8 MB
cyclic=True  gc on :  205 ms, collections per generation [2616, 237, 0], peak RSS    8 MB
cyclic=True  gc off:  131 ms, peak RSS  100 MB, then one collect() frees 2000554 objects
```

The timings on this VM varied by ±50% between runs; the best of five fresh runs of each
case was 100 ms (no cycles), 196 ms (cycles, GC on) and 138 ms (cycles, GC off). The
collection counts and memory were identical every time. What it shows:

- **No cycles, no collections.** CPython triggers a generation-0 collection when
  *allocations minus deallocations* of container objects pass 700. Reference counting
  frees each pair immediately, so the counter never climbs.
- **Cycles trigger the collector constantly**: 2,616 young collections and 237 of
  generation 1 for a million pairs, roughly doubling the run time — and memory stays
  flat at 8 MB.
- **Disabling the collector** saves that CPU but lets 2 million dead objects pile up:
  100 MB instead of 8 MB. That is the trade every GC makes — CPU for memory — and it's
  why "turn off the GC" is a legitimate optimisation only for short-lived processes or
  code that provably creates no cycles.

## 9. Concurrent Collection: Tri-Colour Marking and Write Barriers

To avoid long pauses, modern collectors (Go's, Java's G1/ZGC/Shenandoah, V8's) mark
**while the program keeps running**, or in small increments between its steps. That
needs bookkeeping that survives interruption — **tri-colour marking**:

- **White**: not yet reached. At the end of marking, white means garbage.
- **Grey**: reached, but its children not yet scanned. The grey set is the work queue.
- **Black**: reached, and every child scanned.

Marking repeatedly takes a grey object, greys its white children, and blackens it,
until no grey is left. The invariant that makes the result correct is: **no black
object may point to a white object** — because black objects are never looked at again,
a white object reachable only from a black one would never be marked, and would be
freed while in use.

The program (the **mutator**, in GC vocabulary) can break that invariant by storing a
pointer. Here is the toy heap from §7 with incremental marking, and the program running
between marking steps:

```python
    def start_marking(self):
        self.black, self.gray = set(), list(self.roots)
        self.gray_ids = {id(o) for o in self.gray}

    def mark_step(self, budget):
        """Blacken up to `budget` grey objects, then give control back."""
        for _ in range(budget):
            if not self.gray:
                return True
            o = self.gray.pop(0)                         # FIFO: breadth-first
            self.black.add(id(o))
            for child in o.refs:
                if id(child) not in self.black and id(child) not in self.gray_ids:
                    self.gray.append(child)
                    self.gray_ids.add(id(child))
        return not self.gray

    def write(self, src, dst, barrier):
        """The program stores a pointer: src.refs.append(dst)."""
        if barrier and id(dst) not in self.black and id(dst) not in self.gray_ids:
            self.gray.append(dst)                      # Dijkstra insertion barrier:
            self.gray_ids.add(id(dst))                 # shade the target grey
        src.refs.append(dst)

    def finish_sweep(self):
        dead = [o for o in self.objects if id(o) not in self.black]
        self.objects = [o for o in self.objects if id(o) in self.black]
        return dead


def scenario(barrier):
    h = Heap()
    r, a, b, x = (h.new(n) for n in "RABX")
    h.roots = [r]
    r.refs = [a, b]
    b.refs = [x]                                       # X is reachable only through B
    h.start_marking()
    h.mark_step(2)                                     # R and then A turn black; B is grey
    h.write(a, x, barrier)                             # program: a.x = b.x  (black -> white)
    b.refs.remove(x)                                   # program: b.x = None
    while not h.mark_step(1):
        pass
    dead = h.finish_sweep()
    print(f"barrier={barrier!s:5} swept {dead}  but A still points to {a.refs}"
          + ("  <-- freed while in use!" if x in dead else "  (correct)"))


scenario(barrier=False)
scenario(barrier=True)
```

```text
barrier=False swept [X]  but A still points to [X]  <-- freed while in use!
barrier=True  swept []  but A still points to [X]  (correct)
```

Step by step: marking has blackened `R` and `A`; `B` is grey and still has to scan `X`.
The program then copies the pointer to `X` from `B` into `A` and clears `B`'s. When
marking resumes, `B` has no children, so `X` is never reached. `A` is black and won't be
rescanned. `X` stays white and is swept — while `A` still points to it. That is a
use-after-free manufactured by a correct program and a naive collector.

The fix is a **write barrier**: a few instructions the compiler adds to every pointer
store while marking is active. The **Dijkstra insertion barrier** used here greys the
target of any new pointer, so a black object can never gain a white child. The
**Yuasa deletion barrier** instead greys the *old* target of an overwritten pointer, so
nothing reachable at the start of marking can be lost (a "snapshot at the beginning").
**Go uses a hybrid of the two** (since Go 1.8), which is what lets it avoid re-scanning
goroutine stacks and keep stop-the-world pauses typically well under a millisecond.

The price of concurrency: the barrier slows every pointer write while marking runs, the
collector uses CPU the program would have used (Go targets 25% of GOMAXPROCS during a
cycle), and the heap must have headroom because the program keeps allocating while
marking is in progress.

## 10. Go's Collector in Practice: GOGC and GOMEMLIMIT

Go's GC is a **concurrent, non-moving, non-generational tri-colour mark-sweep** with
size-class allocation (§3). It doesn't move objects (so no compaction, but also no
pointer fix-ups, and cgo can hold pointers safely), and it has no generations (escape
analysis, §11, removes much of the young garbage generations would target).

**When does it collect?** When the heap grows to `live heap × (1 + GOGC/100)` since the
last cycle. With the default `GOGC=100`, a program with 50 MB live collects when the heap
reaches ~100 MB. Raise `GOGC` for fewer collections and more memory; lower it for the
opposite. Since Go 1.19, `GOMEMLIMIT` adds a soft ceiling: the collector runs as often as
needed to stay under it, whatever `GOGC` says.

The measurement — a workload with ~50 MB of long-lived data and 20 million short-lived
allocations:

```go
// GOGC trades memory for CPU: a churn workload with a 50 MB live set.
package main

import (
	"fmt"
	"os"
	"runtime"
	"time"
)

type node struct {
	next *node
	pad  [48]byte
}

var live []*node

func main() {
	// Live data that survives the whole run: ~50 MB the GC must mark every cycle.
	for i := 0; i < 800_000; i++ {
		live = append(live, &node{})
	}
	runtime.GC()
	var peak uint64
	stop := make(chan bool)
	go func() { // sample the heap size every millisecond
		var m runtime.MemStats
		for {
			select {
			case <-stop:
				return
			default:
				runtime.ReadMemStats(&m)
				if m.HeapAlloc > peak {
					peak = m.HeapAlloc
				}
				time.Sleep(time.Millisecond)
			}
		}
	}()
	var before, after runtime.MemStats
	runtime.ReadMemStats(&before)
	var head *node
	for i := 0; i < 20_000_000; i++ { // short-lived garbage
		head = &node{next: head}
		if i%1000 == 0 {
			head = nil
		}
	}
	stop <- true
	runtime.ReadMemStats(&after)
	fmt.Printf("GOGC=%-4s GOMEMLIMIT=%-7s GCs %4d  GC CPU %4.1f%%  peak heap %4d MB\n",
		os.Getenv("GOGC"), os.Getenv("GOMEMLIMIT"), after.NumGC-before.NumGC,
		100*after.GCCPUFraction, peak>>20)
}
```

| Setting | GC cycles | GC share of CPU | Peak heap |
|---|---:|---:|---:|
| `GOGC=25` | 81 | 20% | 76–78 MB |
| `GOGC=50` | 38 | 12–13% | 99 MB |
| `GOGC=100` (default) | 20 | 8% | 132–135 MB |
| `GOGC=200` | 10–11 | 4–5% | 174–186 MB |
| `GOGC=400` | 5 | 2–3% | 281–316 MB |
| `GOGC=off` | 0 | — | 1,276 MB |
| `GOGC=100 GOMEMLIMIT=100MiB` | 46 | 14% | 90 MB |
| `GOGC=off GOMEMLIMIT=200MiB` | 12 | 5% | 180–181 MB |

Ranges are across three runs: the cycle counts, CPU shares and peaks were stable; wall-clock
times on this shared VM were not (the `GOGC=off` run took anywhere from 1.4 s to 8.5 s,
mostly page-faulting in 1.2 GB of fresh memory), so they're left out.

How to read it:

- **Every doubling of `GOGC` roughly halves the number of collections and the GC's CPU
  share, and raises peak memory.** The live set is the same ~50 MB each time; what you
  choose is how much garbage to let accumulate before paying to mark it.
- **The GC cost is proportional to live data × number of cycles.** Each cycle marks the
  same 50 MB. That is why a large, stable cache in a Go service makes GC expensive even if
  it rarely changes — and why people shard it, move it off-heap, or store it as
  pointer-free data (a `[]byte` or a slice of structs without pointers is not scanned).
- **`GOMEMLIMIT` is the right knob for containers.** Set it a little below the
  container's memory limit and `GOGC=off` (or a high `GOGC`): the program uses the memory
  it has and collects only as it nears the limit — 12 cycles instead of 20 here, with the
  heap capped at about 180 MB. The one risk: if the live set itself approaches the limit, the
  collector runs continuously ("death spiral"); Go caps GC CPU at about 50% in that case
  to keep the program making progress.

**The JVM, for comparison**, offers several collectors: G1 (the default: generational,
region-based, mostly concurrent, compacting), ZGC and Shenandoah (concurrent compacting
collectors with pauses in the low milliseconds or below, even on very large heaps, paid
for with load barriers and throughput), and Parallel GC (maximum throughput, longer
pauses). The trade-off triangle is the same everywhere: **throughput, pause time, and
memory overhead — pick the two that matter**.

## 11. Escape Analysis: Keeping Values Off the Heap

The cheapest heap allocation is the one that doesn't happen. Go's compiler (and the
JVM's JIT) run **escape analysis**: if a value provably doesn't outlive its function, it
goes on the stack, costing nothing to allocate and nothing to collect.

```go
type Point struct{ X, Y, Z int64 }

//go:noinline
func byValue(i int64) Point { return Point{i, i, i} } // stays on the stack

//go:noinline
func byPointer(i int64) *Point { return &Point{i, i, i} } // escapes: outlives the call
```

```text
$ go build -gcflags=-m ./escape
escape/main.go:15:41: &Point{...} escapes to heap

by value  :  1.33 ns/op  0 allocs/op
by pointer: 29.23 ns/op  1 allocs/op  24 B/op
```

Returning a 24-byte struct by value copies three words; returning a pointer to it forces
a heap allocation that is **22× slower here, before counting the GC work it creates
later.** `-gcflags=-m` tells you exactly which allocations escape and why.

Common reasons a value escapes in Go: returning a pointer to it; storing it in a
longer-lived structure, a global or a channel; capturing it in a closure that outlives
the function; converting it to an interface (`fmt.Println(x)` often makes `x` escape);
and slices whose size isn't known at compile time. The practical rule: **in hot paths,
prefer values over pointers for small structs, preallocate slices with a known
capacity, and reuse buffers** (`sync.Pool` for objects that are expensive to create and
used in bursts).

**Precision note:** "pointers are faster because they avoid copying" is backwards for
small structs in Go. Copying 24 bytes is cheaper than an allocation plus GC, and
pointer-free memory isn't scanned by the collector at all. Pointers win for large
structs or when the callee must mutate the caller's value.

## 12. Memory Leaks in Garbage-Collected Languages

A GC frees unreachable memory. A leak in Python, Go or Java is always memory that is
**still reachable but no longer useful**. The usual suspects:

| Leak | How it happens | Fix |
|---|---|---|
| Unbounded cache or map | Keys include something unique per request | Bound it (LRU with a max size), add TTLs, fix the key |
| Registered listeners and callbacks | An object subscribes and is never unsubscribed | Unregister on close; hold listeners weakly |
| Goroutine / thread leak | A goroutine blocked forever on a channel nobody writes | Pass a `context` and select on `ctx.Done()` (`05` §5) |
| Sub-slice / substring retention | A small view keeps its huge backing array alive | Copy the small piece out |
| Closures capturing too much | A long-lived closure references a large object | Capture only what's needed |
| `functools.lru_cache` on a method | The cache holds `self`, so instances never die | Cache on a function of plain keys, or bound the cache |

**Finding one in Python** — `tracemalloc` records where every allocation came from, and
comparing two snapshots points at the line that keeps growing:

```python
"""A leak in a garbage-collected language, and how tracemalloc finds it."""
import tracemalloc

_cache = {}                                   # module-level, never evicted


def render(user_id: int, request_id: int) -> str:
    key = (user_id, request_id)               # bug: request_id makes every key unique
    if key not in _cache:
        _cache[key] = f"<profile {user_id}>" * 20
    return _cache[key]


tracemalloc.start()
before = tracemalloc.take_snapshot()
for req in range(50_000):
    render(req % 100, req)                    # only 100 distinct users
after = tracemalloc.take_snapshot()

for stat in after.compare_to(before, "lineno")[:2]:
    print(stat)
print("cache entries:", len(_cache), "for 100 distinct users")
```

```text
leak.py:10: size=16.2 MiB (+16.2 MiB), count=50001 (+50001), average=339 B
leak.py:8: size=2734 KiB (+2734 KiB), count=49984 (+49984), average=56 B
cache entries: 50000 for 100 distinct users
```

Line 10 (the cached string) and line 8 (the key tuple) grew by one object per request.
The cache was meant to hold 100 entries and holds 50,000. In production the same
technique is a heap profile compared over time: `tracemalloc` or `memray` for Python,
`go tool pprof` with `-inuse_space` for Go (compare two profiles with `-base`), a heap
dump in Eclipse MAT for the JVM — and the question to ask of the biggest growing type is
always "who is holding the reference?"

**Finding one in Go — a small view of a big array:**

```go
func headerView() []byte {
	buf := make([]byte, 64<<20) // pretend we read a 64 MB file
	return buf[:16]             // keep only the 16-byte header
}

func headerCopy() []byte {
	buf := make([]byte, 64<<20)
	return append([]byte(nil), buf[:16]...) // copy: buf becomes garbage
}
```

```text
4 headers as views:  heap + 256 MB
4 headers as copies: heap + 0 MB
```

A slice is a pointer into its backing array, so keeping 16 bytes of a 64 MB buffer keeps
all 64 MB reachable. Copying the 16 bytes out lets the collector free the rest. The
same trap exists with Python `memoryview`s and was, for years, Java's `String.substring`.

## 13. Measuring Memory Correctly

Different tools answer different questions, and mixing them up leads to wrong
conclusions:

| Measure | What it counts | Get it from |
|---|---|---|
| **VSZ / virtual size** | Every mapped address range, used or not | `ps`, `top` — mostly meaningless (reserved stacks, mmaps) |
| **RSS** | Physical pages currently resident | `ps`, `/proc/<pid>/status`, container metrics |
| **Heap in use** | Bytes in live and not-yet-collected objects | `runtime.MemStats.HeapAlloc`, `tracemalloc` |
| **Object size** | One object's own bytes, not what it references | `sys.getsizeof`, `unsafe.Sizeof` |

What Python objects really cost:

```python
import sys, tracemalloc
from array import array
print("sys.getsizeof: int 1 =", sys.getsizeof(1), "B | float =", sys.getsizeof(1.0),
      "B | empty list =", sys.getsizeof([]), "B | empty dict =", sys.getsizeof({}), "B | 'a' =", sys.getsizeof("a"), "B")
for label, make in [("list of 1M ints", lambda: [i for i in range(1_000_000)]),
                    ("array('q') of 1M ints", lambda: array("q", range(1_000_000)))]:
    tracemalloc.start()
    obj = make()
    cur, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"{label:22} {cur / 1e6:5.1f} MB  ({cur / 1e6:.1f} B per int)")
    del obj
```

```text
sys.getsizeof: int 1 = 28 B | float = 24 B | empty list = 56 B | empty dict = 64 B | 'a' = 50 B
list of 1M ints         40.4 MB  (40.4 B per int)
array('q') of 1M ints    8.2 MB  (8.2 B per int)
```

A Python `int` is a full heap object — reference count, type pointer, size, digits — and
a list holds 8-byte pointers to those objects. A million integers cost 40 bytes each in a
list and 8 in an `array` (or a NumPy array), which stores the raw machine integers
contiguously. That 5× is also why numeric Python code is fast only when the data never
becomes individual Python objects. `sys.getsizeof` is shallow: `getsizeof` of the list
alone would report only the 8 MB of pointers.

**Precision note:** RSS that stays high after a spike is usually not a leak (§3's
precision note: allocators keep freed memory). A leak is memory that grows *without
bound* under a steady workload. Watch the trend of the heap-in-use metric across
hours, not a single RSS reading.

## 14. Choosing a Strategy: the Trade-Offs Side by Side

| Runtime | Strategy | Moves objects? | Typical pause | Strengths | Costs |
|---|---|---|---|---|---|
| C / C++ | Manual, RAII, `shared_ptr` | No | None | Full control, no runtime | Memory-safety bugs; fragmentation |
| Rust | Ownership + borrow checker (`Rc`/`Arc` when shared) | No | None | Safety without a GC | Learning curve; cycles with `Rc` still leak |
| CPython | Reference counting + generational cycle collector | No | Short, per young collection | Prompt freeing, small working set | Refcount writes everywhere; GIL; per-object overhead |
| Swift / Obj-C | ARC (compiler-inserted reference counting) | No | None | Predictable | Cycles need `weak`/`unowned` |
| Go | Concurrent tri-colour mark-sweep, non-generational | No | Usually sub-millisecond | Low latency, simple tuning (`GOGC`, `GOMEMLIMIT`) | ~2× memory headroom by default; CPU during marking |
| Java (G1, ZGC) | Generational (G1) / concurrent compacting (ZGC) | Yes | Milliseconds (G1), sub-ms (ZGC) | High allocation throughput, no fragmentation | Tuning surface; barrier overhead |
| JavaScript (V8) | Generational: copying nursery, incremental/concurrent mark-compact old space | Yes | Short, incremental | Very fast short-lived allocation | Heap limits per isolate |

**How to talk about it in an interview:** name the three competing goals — throughput
(total CPU spent on memory management), latency (longest pause), and footprint (memory
beyond the live set) — and place each strategy in that triangle. Then connect it to the
system: a batch job can tolerate pauses for throughput; a latency-sensitive service
needs a concurrent collector and headroom; a memory-constrained container needs
`GOMEMLIMIT` or a small heap; a real-time system may need no GC at all.

## What Each Engineering Level Should Know

| Topic in this chapter | Junior / New Grad (Google L3) | Mid-Level (Google L4) | Senior (Google L5) | Staff+ (Google L6–L7) |
|---|---|---|---|---|
| **Address space, stack vs heap** (Foundations, §1–§2) | Knows locals live on the stack and objects on the heap | Explains frames, stack overflow, and why values escape to the heap | Explains per-language stack behaviour (Python limit, C guard page, Go growable stacks) | Sets stack and thread-sizing policy for services |
| **Allocators and fragmentation** (§3–§4) | Knows `malloc`/`free` exist | Explains internal vs external fragmentation | Explains size classes, per-thread caches, why RSS doesn't drop after `free` | Chooses allocators (jemalloc, tcmalloc) and tunes them from measurements |
| **Manual memory bugs** (§5) | Knows what a leak is | Names use-after-free, double free, overflow | Explains how RAII and Rust ownership prevent them; uses sanitizers | Drives memory-safety strategy (language choice, sanitizers in CI, fuzzing) |
| **Reference counting** (§6) | Knows Python frees objects automatically | Explains refcounting and the cycle problem | Explains refcount costs (writes, atomics, the GIL, CoW after fork) and weak references | Weighs RC vs tracing for a runtime or large codebase |
| **Tracing, generational, concurrent GC** (§7–§9) | Knows a GC exists | Explains mark-sweep and roots | Explains generations, copying vs compacting, tri-colour invariant and write barriers | Chooses and tunes collectors against latency and footprint SLOs |
| **Go GC tuning, escape analysis** (§10–§11) | — | Knows `GOGC` exists | Uses `GOGC`/`GOMEMLIMIT`, reads `-gcflags=-m`, reduces allocations in hot paths | Sets fleet-wide memory policy for Go services in containers |
| **Leaks and measurement** (§12–§13) | Notices memory growing | Finds a leak with a heap profiler | Distinguishes RSS, heap and object size; finds retention paths | Builds memory observability and regression alerts |

**Reading this table as a study plan:** Foundations and §1–§2 cover the classic "stack
vs heap" and "how does Python free memory" questions. §6–§9 are the Senior answer to
"how does garbage collection work?" §10–§12 are what you need to debug a real service.

## Interview checklist

- [ ] I can draw a process's address space and say where code, globals, heap, mmaps and stack live.
- [ ] I can explain stack vs heap: lifetime, cost, size limits, and what makes a value escape.
- [ ] I can say what happens on too-deep recursion in Python, C and Go, and why tail calls don't help in Python or Go.
- [ ] I can explain how an allocator uses size classes and per-thread caches, and define internal vs external fragmentation.
- [ ] I can name the manual-memory bugs and how RAII, Rust ownership and sanitizers address them.
- [ ] I can explain reference counting, why cycles leak, how weak references help, and what refcounting costs.
- [ ] I can explain mark-sweep from roots, and why GC collects unreachable rather than unused memory.
- [ ] I can explain copying, compacting and generational collection, and the generational hypothesis.
- [ ] I can explain tri-colour marking, the black-to-white invariant, and why concurrent marking needs a write barrier.
- [ ] I can explain Go's `GOGC` and `GOMEMLIMIT` trade-off with numbers, and read escape-analysis output.
- [ ] I can list common leaks in GC'd languages and find one with `tracemalloc` or `pprof`.
- [ ] I can compare the memory strategies of C++, Rust, CPython, Go and Java on throughput, latency and footprint.

Related: [Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md) §5 (virtual memory, page faults, OOM killer) and §6 (fork and copy-on-write), [Concurrency](05_concurrency_deep_dive.md) §6 (the GIL), [Data Structure Internals](06_data_structure_internals_deep_dive.md) §13 (per-object overhead), [Computer Architecture & Data Representation](13_computer_architecture_deep_dive.md) §6 and §11 (alignment, caches); PyEngineering and GoEngineering performance topics.
