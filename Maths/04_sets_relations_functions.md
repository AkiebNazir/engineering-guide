# Sets, Relations and Functions — The Data Model Under Everything

Sets, relations and functions are the maths that databases, type systems, hash tables
and graphs are built on. A set is a collection with no duplicates; a relation is a set
of pairs (a database table is literally one); a function is a relation where every
input has exactly one output (a hash function, a lookup table). This chapter builds
all three from scratch, then uses them to explain equivalence classes (union-find),
partial orders (dependency graphs and sorting comparators), the pigeonhole principle
(why collisions are unavoidable), and why some infinities are bigger than others
(why some problems can never be solved by any program).

**Where this fits:** Part 1 · The language of maths, chapter 4 of 15. **Builds on:** [03 Logic and proofs](03_logic_and_proofs.md) (logic and quantifiers). **Used again in:** 05, 08, 14. **Next in order:** [05 Counting, permutations and combinations](05_counting_and_combinatorics.md).

## Where You Will Use This

| Concept | Shows up as |
|---|---|
| Set operations, inclusion–exclusion | `set` in Python, SQL `UNION`/`INTERSECT`/`EXCEPT`, counting problems |
| Power set | "all subsets" backtracking, bitmask DP |
| Relations | Database tables, joins, graphs |
| Equivalence relations | Union-find, grouping anagrams, connected components |
| Partial orders | Build systems, task scheduling, topological sort, `Comparator` contracts |
| Injective / surjective / bijective | Hash collisions, encoding and decoding, permutations |
| Pigeonhole | Collision guarantees, "no compressor shrinks every file" |
| Countability | Why the halting problem is unsolvable |

## Foundations — What a Set Is

A **set** is a collection of distinct things, called its **elements**, with no order
and no duplicates. $\{1, 2, 3\}$, $\{3, 2, 1\}$ and $\{1, 1, 2, 3\}$ are the **same**
set. We write $x \in A$ for "x is an element of A" and $\lvert A \rvert$ for the number
of elements (the **cardinality**).

> **Analogy:** A set is a guest list. Writing a name twice does not invite them twice,
> and the order of the names does not matter. The only question a guest list answers
> is "is this person on it?" — which is exactly the operation a hash set makes O(1).

```python
A = {1, 2, 3}
print(A == {3, 2, 1}, A == {1, 1, 2, 3})   # → True True
print(2 in A, len({1, 1, 2, 3}))           # → True 3
```

Some sets have names: the **empty set** $\emptyset$ (no elements; `set()` — not `{}`,
which is an empty dict), and the number sets ℕ, ℤ, ℚ, ℝ from chapter 01. A is a
**subset** of B, $A \subseteq B$, if every element of A is in B.

## 1 · Set Operations

| Operation | Maths | Contains | Python | SQL |
|---|---|---|---|---|
| Union | $A \cup B$ | in A **or** B | `A \| B` | `UNION` |
| Intersection | $A \cap B$ | in A **and** B | `A & B` | `INTERSECT` |
| Difference | $A \setminus B$ or $A - B$ | in A, **not** in B | `A - B` | `EXCEPT` |
| Symmetric difference | $A \,\triangle\, B$ | in exactly one | `A ^ B` | — |
| Complement | $A^c$ or $\overline{A}$ | in the universe U, not in A | `U - A` | `NOT IN` |

Each set operation is a logic operation on membership: ∪ is OR, ∩ is AND, complement
is NOT, △ is XOR. So every law from chapter 03 has a set version — including
**De Morgan**: $(A \cup B)^c = A^c \cap B^c$.

**Try it: shade the result.** U is 1…20, A the even numbers, B the multiples of 3. Pick
each operation and read the result, the Python, SQL and bitmask equivalents. Compare
$(A \cup B)^c$ with $A^c \cap B^c$: De Morgan says they shade the same region.

<div class="lab" data-viz="math-venn"></div>

### Inclusion–exclusion: counting a union

Adding $\lvert A \rvert + \lvert B \rvert$ counts the overlap twice, so subtract it once:

$$
\lvert A \cup B \rvert = \lvert A \rvert + \lvert B \rvert - \lvert A \cap B \rvert
$$

For three sets, add the singles, subtract the pairs, add back the triple:

$$
\lvert A \cup B \cup C \rvert = \lvert A \rvert + \lvert B \rvert + \lvert C \rvert - \lvert A \cap B \rvert - \lvert A \cap C \rvert - \lvert B \cap C \rvert + \lvert A \cap B \cap C \rvert
$$

> **Worked example:** How many numbers below 1000 are multiples of 3 or 5? Multiples
> of 3: 333. Of 5: 199. Of both (that is, of 15): 66. Answer: 333 + 199 − 66 = 466 —
> no loop over 1000 numbers needed. Their **sum** follows the same pattern, using
> Gauss's formula for each multiple count.

```python
def count_multiples(k, below):
    return (below - 1) // k

def sum_multiples(k, below):
    m = (below - 1) // k
    return k * m * (m + 1) // 2

n = 1000
print(count_multiples(3, n) + count_multiples(5, n) - count_multiples(15, n))   # → 466
print(sum_multiples(3, n) + sum_multiples(5, n) - sum_multiples(15, n))         # → 233168
print(sum(x for x in range(n) if x % 3 == 0 or x % 5 == 0))                     # → 233168
```

## 2 · Subsets and the Power Set

The **power set** $\mathcal{P}(A)$ is the set of all subsets of A. If $\lvert A \rvert = n$
it has $2^n$ elements: for each of the n elements you independently decide **in or
out** — n yes/no choices.

Three ways to generate it, each teaching something:

```python
from itertools import combinations

def power_set_recursive(items):
    if not items:
        return [[]]
    rest = power_set_recursive(items[1:])
    return rest + [[items[0]] + s for s in rest]          # without the first, then with it

def power_set_bits(items):
    n = len(items)
    return [[items[i] for i in range(n) if mask >> i & 1] for mask in range(1 << n)]

def power_set_by_size(items):
    return [list(c) for k in range(len(items) + 1) for c in combinations(items, k)]

s = ["a", "b", "c"]
print(len(power_set_recursive(s)), len(power_set_bits(s)), len(power_set_by_size(s)))   # → 8 8 8
print(power_set_recursive(s))   # → [[], ['c'], ['b'], ['b', 'c'], ['a'], ['a', 'c'], ['a', 'b'], ['a', 'b', 'c']]
```

The recursive version *is* the proof that there are $2^n$ subsets: the subsets of n
items are the subsets of the other n − 1 items, once without the first item and once
with it — twice as many. It is also the shape of every "include or exclude" backtracking
solution.

> **Interview angle:** Whenever a brute force is "try every subset", its cost is
> $O(2^n)$ (times the work per subset). That is fine for n ≤ 20 or so and hopeless at
> n = 60 — the constraint in the problem statement is often the hint (chapter 06 and
> CS Fundamentals chapter 07).

> **Notebook example:** List every subset of $\{a, b, c\}$ with the "in or out" method.
> Then count the subsets of $\{1, \dots, 10\}$ that contain 1 but not 2.
>
> 1. Start with the subsets of nothing: $\{\varnothing\}$.
> 2. Decide about a: keep each old subset, and add a copy with a in it:
>    $\varnothing, \{a\}$.
> 3. Decide about b the same way: $\varnothing, \{a\}, \{b\}, \{a, b\}$.
> 4. Decide about c: $\varnothing, \{a\}, \{b\}, \{a, b\}, \{c\}, \{a, c\}, \{b, c\}, \{a, b, c\}$.
>    That is 8 subsets, $2^3$: each step doubled the list.
> 5. Second question: 1 is forced in and 2 is forced out, so only 8 elements (3…10) are
>    still free. That gives $2^8 = 256$ subsets.

## 3 · Ordered Pairs and the Cartesian Product

In a set, order does not matter; in an **ordered pair** $(a, b)$, it does:
$(1, 2) \ne (2, 1)$. The **Cartesian product** $A \times B$ is the set of all pairs
with the first from A and the second from B, so $\lvert A \times B \rvert = \lvert A \rvert \cdot \lvert B \rvert$.

```python
from itertools import product
sizes, colours = ["S", "M", "L"], ["red", "blue"]
print(len(list(product(sizes, colours))), list(product(sizes, colours))[:2])   # → 6 [('S', 'red'), ('S', 'blue')]
```

This is SQL's `CROSS JOIN`, a nested loop, and a grid's coordinates ($\mathbb{Z} \times \mathbb{Z}$).
A join without a join condition is a Cartesian product — the classic accidental query
that returns rows × rows results.

> **Notebook example:** Let $A = \{x, y\}$ and $B = \{1, 2, 3\}$. List $A \times B$, compare
> it with $B \times A$, and size a cross join.
>
> 1. Pair each element of A with each element of B:
>    $(x,1), (x,2), (x,3), (y,1), (y,2), (y,3)$. That is 6 pairs, $2 \times 3$.
> 2. $B \times A$ has pairs like $(1, x)$. Those are **different** pairs, because order
>    matters, so $A \times B \ne B \times A$, even though both have 6 elements.
> 3. A `CROSS JOIN` of a 1,000-row table with a 500-row table returns
>    $1000 \times 500 = 500{,}000$ rows. Forgetting a join condition does exactly this.

## 4 · Relations: Sets of Pairs

A **relation** R from A to B is any subset of $A \times B$. We write $a \mathrel{R} b$
when $(a, b) \in R$. That is all a relation is — a set of pairs that are "related".

> **In practice:** A database table *is* a relation: `enrolled(student, course)` is a
> set of pairs, and Edgar Codd named the relational model after exactly this idea. A
> directed graph is a relation on its vertices: $u \mathrel{R} v$ when there is an edge
> $u \to v$. "Follows" on a social network is a relation on users.

A relation on a single set A can have these properties:

| Property | Definition | Example that has it | Example that does not |
|---|---|---|---|
| **Reflexive** | $a \mathrel{R} a$ for every a | $=$, $\le$, "same birthday as" | $<$ |
| **Symmetric** | $a \mathrel{R} b \Rightarrow b \mathrel{R} a$ | "is a sibling of", "same birthday as" | "follows" |
| **Antisymmetric** | $a \mathrel{R} b$ and $b \mathrel{R} a \Rightarrow a = b$ | $\le$, $\subseteq$, "divides" (on positive integers) | "same birthday as" |
| **Transitive** | $a \mathrel{R} b$ and $b \mathrel{R} c \Rightarrow a \mathrel{R} c$ | $<$, "is an ancestor of" | "is the parent of", "is a friend of" |

```python
def props(R, A):
    return {
        "reflexive": all((a, a) in R for a in A),
        "symmetric": all((b, a) in R for a, b in R),
        "antisymmetric": all(a == b for a, b in R if (b, a) in R),
        "transitive": all((a, d) in R for a, b in R for c, d in R if b == c),
    }

A = range(1, 7)
divides = {(a, b) for a in A for b in A if b % a == 0}
same_mod3 = {(a, b) for a in A for b in A if a % 3 == b % 3}
print(props(divides, A))     # → {'reflexive': True, 'symmetric': False, 'antisymmetric': True, 'transitive': True}
print(props(same_mod3, A))   # → {'reflexive': True, 'symmetric': True, 'antisymmetric': False, 'transitive': True}
```

Those two combinations are the two most important kinds of relation.

> **Notebook example:** On $A = \{1, 2, 3\}$, let
> $R = \{(1,1), (2,2), (3,3), (1,2), (2,1), (2,3)\}$. Which of the four properties
> does R have?
>
> 1. **Reflexive?** Are $(1,1), (2,2), (3,3)$ all in R? Yes. ✓
> 2. **Symmetric?** Every pair needs its mirror. $(1,2)$ has $(2,1)$, but $(2,3)$ has no
>    $(3,2)$. ✗
> 3. **Antisymmetric?** Two different elements must never point both ways. But $(1,2)$
>    and $(2,1)$ are both in R, and $1 \ne 2$. ✗
> 4. **Transitive?** Look for chains $a \to b \to c$. $(1,2)$ and $(2,3)$ need $(1,3)$,
>    which is missing. ✗
>
> **Answer:** reflexive only. A single missing pair is enough to break a "for every"
> property, so name it when you answer.

## 5 · Equivalence Relations: "Same in the Way That Matters"

A relation that is **reflexive, symmetric and transitive** is an **equivalence
relation**. It captures "these are the same, for my purposes": same remainder mod 3,
same connected component, anagrams of each other, same user after case-folding the
email.

> **Key idea:** An equivalence relation **partitions** the set into disjoint groups
> called **equivalence classes**: every element is in exactly one class, and two
> elements are related exactly when they share a class. Mod 3 splits the integers into
> {…, 0, 3, 6, …}, {…, 1, 4, 7, …} and {…, 2, 5, 8, …}.

There are two standard ways to compute the classes, and both are interview staples:

1. **A canonical key.** Map each element to one representative of its class, then
   group by key. Anagrams: the key is the sorted letters.
2. **Union-find.** When the relation is given as a list of "these two are the same"
   facts, merge sets as the facts arrive; transitivity is handled automatically.

```python
from collections import defaultdict

def group_anagrams(words):
    groups = defaultdict(list)
    for w in words:
        groups["".join(sorted(w))].append(w)       # canonical key = sorted letters
    return sorted(groups.values())

print(group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]))   # → [['bat'], ['eat', 'tea', 'ate'], ['tan', 'nat']]

def classes_from_pairs(n, same):
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]          # path halving
            x = parent[x]
        return x
    for a, b in same:
        parent[find(a)] = find(b)
    groups = defaultdict(list)
    for x in range(n):
        groups[find(x)].append(x)
    return sorted(groups.values())

print(classes_from_pairs(6, [(0, 1), (1, 2), (4, 5)]))   # → [[0, 1, 2], [3], [4, 5]]
```

Note that 0 and 2 ended up together although no fact said so directly — that is
transitivity, done by the data structure.

> **Notebook example:** Six servers, 1 to 6. The facts "1 and 2 share a rack", "3 and 4
> share a rack" and "2 and 4 share a rack" arrive in that order. Which racks are there?
>
> 1. Start with everything alone: $\{1\}, \{2\}, \{3\}, \{4\}, \{5\}, \{6\}$.
> 2. Fact (1, 2): merge their groups. $\{1, 2\}, \{3\}, \{4\}, \{5\}, \{6\}$.
> 3. Fact (3, 4): $\{1, 2\}, \{3, 4\}, \{5\}, \{6\}$.
> 4. Fact (2, 4): 2 is in $\{1, 2\}$ and 4 is in $\{3, 4\}$, so merge the two groups:
>    $\{1, 2, 3, 4\}, \{5\}, \{6\}$.
>
> **Answer:** three racks. No fact mentioned 1 and 3 together, but they share a rack by
> transitivity. This is union-find, done by hand. The classes also partition the set:
> every server is in exactly one group.

## 6 · Partial Orders: "Must Come Before"

A relation that is **reflexive, antisymmetric and transitive** is a **partial order**.
$\le$ on numbers, $\subseteq$ on sets, "divides" on positive integers, and "must be
built before" in a build system are all partial orders. "Partial" because some pairs
may be **incomparable**: neither {1} ⊆ {2} nor {2} ⊆ {1}. If every pair is comparable
it is a **total order**.

A partial order is drawn as a **Hasse diagram**: an arrow from a to b when a comes
directly before b, leaving out anything implied by transitivity or reflexivity.

```mermaid
%% caption: "Divides" on the divisors of 12 is a partial order. 2 and 3 are incomparable (neither divides the other), so there is more than one valid ordering of them — every topological sort is a valid total order that respects all arrows.
flowchart BT
  1 --> 2
  1 --> 3
  2 --> 4
  2 --> 6
  3 --> 6
  4 --> 12
  6 --> 12
```

> **Key idea:** A **topological sort** extends a partial order to a total order — a
> line-up that respects every "must come before". Build tools, package managers,
> spreadsheet recalculation and course prerequisites all do this. It exists exactly
> when the dependency graph has **no cycle** (chapter 08).

### Why sorting comparators must be consistent

Sorting algorithms assume your comparison is a **strict weak order**: irreflexive
(`x < x` is false), transitive, and with "incomparable" itself transitive. Break the
rules and the result is garbage — Java's `TimSort` even throws
`IllegalArgumentException: Comparison method violates its general contract!`.

```python
import functools
# "Rock-paper-scissors" order: not transitive (r beats s, s beats p, p beats r)
beats = {("r", "s"), ("s", "p"), ("p", "r")}
cmp = lambda a, b: 0 if a == b else (1 if (a, b) in beats else -1)
print(sorted(["r", "p", "s"], key=functools.cmp_to_key(cmp)))   # → ['r', 'p', 's']
print(sorted(["s", "r", "p"], key=functools.cmp_to_key(cmp)))   # → ['s', 'r', 'p']
```

Same three items, different input orders, different "sorted" outputs — because there
is no correct answer to find. A comparator that compares floats containing NaN has the
same problem.

> **Notebook example:** Build steps: *compile* and *docs* both need *fetch*, *test* needs
> *compile*, and *package* needs *test* and *docs*. Find a valid order.
>
> 1. List what each step waits for: fetch (nothing), compile (fetch), docs (fetch),
>    test (compile), package (test, docs).
> 2. Only **fetch** waits for nothing. Output it and cross it off everywhere.
> 3. Now compile and docs wait for nothing. Pick **compile**, then cross it off.
> 4. test and docs are ready. Pick **test**, then **docs**.
> 5. package is ready last.
>
> **Answer:** fetch, compile, test, docs, package. Another valid order is fetch, docs,
> compile, test, package. compile and docs are **incomparable**, which is why more than
> one order works.

## 7 · Functions, Precisely

With relations in hand, a **function** $f: A \to B$ is a relation from A to B in which
**every** $a \in A$ is related to **exactly one** $b \in B$. Three properties decide
what you can do with it:

| Property | Definition | Picture | CS meaning |
|---|---|---|---|
| **Injective** (one-to-one) | different inputs → different outputs | no two arrows land on the same target | no collisions; information is preserved |
| **Surjective** (onto) | every output is hit by some input | no target left without an arrow | every bucket/value is used |
| **Bijective** | both | a perfect pairing | invertible: you can decode |

**Try it: move the arrows.** Click an input to move its arrow. With 4 inputs and 4
outputs, make a bijection, then create a collision. Switch to 3 outputs (injective
becomes impossible — pigeonhole) and to 5 outputs (surjective becomes impossible).

<div class="lab" data-viz="math-function"></div>

> **Worked example:** Which are invertible?
> - `lambda x: 2 * x` on integers → injective (no collisions) but not surjective onto
>   ℤ (odd numbers are never hit). Invertible on its image (the even numbers).
> - `lambda x: x % 10` on integers → surjective onto {0…9} but hugely non-injective.
>   Not invertible: 3, 13, 23 all give 3.
> - A permutation of `range(n)` → bijection. Its inverse is the permutation that puts
>   each element back.
> - A cryptographic hash → from all strings to 256-bit values: cannot be injective
>   (infinitely many inputs, finitely many outputs). It is *designed* so collisions are
>   infeasible to *find*, not impossible.

```python
perm = [2, 0, 3, 1]                       # f(i) = perm[i], a bijection on {0,1,2,3}
inv = [0] * len(perm)
for i, p in enumerate(perm):
    inv[p] = i
print(inv, [inv[perm[i]] for i in range(4)])   # → [1, 3, 0, 2] [0, 1, 2, 3]
```

## 8 · The Pigeonhole Principle

> **Definition:** If more than n pigeons fly into n holes, some hole gets at least two
> pigeons. More generally, putting N items into k boxes puts at least
> $\lceil N / k \rceil$ items into some box.

It sounds too obvious to be useful. It is one of the most useful ideas in CS:

- **Hash collisions are unavoidable.** Any function from a bigger set to a smaller one
  cannot be injective. With 11 keys and 10 buckets, some bucket holds two.
- **No lossless compressor shrinks every file.** There are $2^n$ files of exactly n
  bits, but only $2^0 + 2^1 + \dots + 2^{n-1} = 2^n - 1$ shorter files. Some n-bit file
  cannot map to a shorter one without colliding with another — and a collision would
  make decompression ambiguous.
- **Repeated states mean a cycle.** A function on a finite set of m states, applied
  over and over, must repeat a state within m + 1 steps; from then on it cycles. This
  is why pseudo-random generators have periods and why Floyd's cycle detection works
  (chapter 07 and the linked-list cycle problems).
- **Birthdays.** Among 367 people, two share a birthday (366 possible days,
  including 29 February). Chapter 10 shows the far more surprising fact that 23 people
  are enough for a 50% chance.

```python
n = 16
print(2**n, sum(2**k for k in range(n)))   # → 65536 65535
```

> **Interview angle:** "Given n + 1 integers in the range 1…n, show some integer
> repeats" — pigeonhole. The follow-up, "find it in O(1) extra space without changing
> the array", treats the array as a function `i → a[i]` and finds the cycle that
> pigeonhole guarantees (Floyd's tortoise and hare).

> **Notebook example:** (a) A drawer holds socks of 4 colours. How many must you pull out
> in the dark to be sure of a matching pair? (b) Among 100 people, what is the largest
> number you can be sure share a birth month?
>
> 1. (a) The holes are the 4 colours. With 4 socks you could get one of each colour, so
>    no match is guaranteed. The 5th sock must repeat a colour: **5 socks**.
> 2. (b) 100 items in 12 boxes: some box has at least $\lceil 100 / 12 \rceil$ people.
>    $100 / 12 = 8.33\ldots$, so the answer is **9**.
> 3. Check (b) by contradiction: if every month had at most 8 people, there would be at
>    most $12 \times 8 = 96 < 100$ people. So some month has at least 9. ✓

## 9 · Infinity Comes in Sizes

Two sets have the **same size** if there is a bijection between them — you can pair
their elements off perfectly. For finite sets that is ordinary counting. For infinite
sets it gives surprising answers.

**Countable sets** can be paired with ℕ = {0, 1, 2, …}, i.e. listed as a sequence
where every element eventually appears:

- The even numbers: $n \mapsto 2n$. As many evens as naturals, although they are a
  proper subset.
- The integers: list them as 0, 1, −1, 2, −2, 3, …
- The rationals: list the fractions by $\lvert p \rvert + q$ (diagonal by diagonal).
- **All finite strings** over an alphabet — and so **all programs** in any language:
  list them by length, then alphabetically.

**The real numbers are not countable.** Cantor's **diagonal argument** (1891): suppose
you had a list of every real number between 0 and 1. Build a new number whose k-th
digit differs from the k-th digit of the k-th number on the list. It differs from
every listed number somewhere, so it is not on the list — contradiction.

```python
listing = ["0.5000", "0.1415", "0.7182", "0.4142"]        # any claimed "complete" list
diag = "".join("5" if s[2 + k] != "5" else "6" for k, s in enumerate(listing))
new = "0." + diag
print(new, new in listing)   # → 0.6555 False
```

> **Key idea:** The same diagonal trick proves the most important limit in computer
> science. Programs are countable; the set of all yes/no problems (subsets of ℕ) is
> not. So **there are problems no program can solve** — and chapter 14 exhibits one,
> the halting problem, using a diagonal argument of exactly this shape.

> **Notebook example:** Someone claims this is a complete list of numbers between 0 and
> 1: 0.5102…, 0.3333…, 0.2753…, 0.8885…. Build a number that is not on it.
>
> 1. Take the k-th digit of the k-th number (the **diagonal**): 1st digit of the 1st
>    number is 5, 2nd of the 2nd is 3, 3rd of the 3rd is 5, 4th of the 4th is 5.
> 2. Change every one of them: write 6 if the digit is 5, otherwise 5. That gives 6, 5,
>    6, 6.
> 3. The new number is 0.6566….
> 4. Check it against the list: it differs from number 1 in digit 1 (6 vs 5), from
>    number 2 in digit 2 (5 vs 3), from number 3 in digit 3 (6 vs 5), and from number 4
>    in digit 4 (6 vs 5). ✓
>
> **Answer:** 0.6566… is missing. The same recipe beats **any** list, however long,
> which is why the real numbers cannot be listed.

## Common Mistakes

1. Using `{}` for an empty set in Python (it is a dict). Use `set()`.
2. Adding counts of overlapping sets without inclusion–exclusion.
3. Forgetting that set order is not guaranteed — never rely on iteration order of a
   `set` for output.
4. A comparator that is not transitive or not consistent (random, NaN, "close enough"
   equality) — sorting results become input-dependent or the sort throws.
5. Assuming a hash function can be collision-free on unbounded input.
6. Treating "infinite" as one size.

## Check Yourself

**1.** How many relations are there on a set of n elements? How many are reflexive?

<details>
<summary>Open the answer</summary>

A relation is any subset of $A \times A$, which has $n^2$ pairs, so there are
$2^{n^2}$ relations. Reflexive ones must contain the n pairs $(a, a)$ and may contain
any subset of the other $n^2 - n$: $2^{n^2 - n}$.

</details>

**2.** Is "is within 1 of" ($\lvert a - b \rvert \le 1$) an equivalence relation on integers?

<details>
<summary>Open the answer</summary>

No. It is reflexive and symmetric but not transitive: 1 is within 1 of 2 and 2 of 3,
but 1 is not within 1 of 3. This is why "fuzzy equality" (floats within epsilon,
timestamps within a second) cannot be used to group items into consistent classes.

</details>

**3.** A URL shortener maps long URLs to 7-character codes from 62 symbols. Can it be
injective? When must collisions occur?

<details>
<summary>Open the answer</summary>

There are $62^7 \approx 3.5 \times 10^{12}$ codes. On all possible URLs (unboundedly
many) it cannot be injective — pigeonhole. It can be injective on the URLs actually
stored, as long as fewer than $62^7$ are stored and codes are assigned (e.g. from a
counter) rather than hashed. Random or hashed codes collide much earlier — around
$1.18\sqrt{62^7} \approx 2.2$ million URLs for a 50% chance (the birthday bound, chapter 10).

</details>

**4.** Why must every topological order of a DAG exist, and why is it not unique?

<details>
<summary>Open the answer</summary>

A finite DAG always has a vertex with no incoming edges (otherwise walking backwards
forever would repeat a vertex — a cycle, by pigeonhole). Output it, remove it, repeat.
It is not unique whenever two items are incomparable (no path between them): either can
go first.

</details>

## What Each Level Should Know

| Level | Expected |
|---|---|
| **Getting started** | Set operations and Venn diagrams; subsets and the $2^n$ power set; Cartesian products; injective/surjective/bijective |
| **Interview-ready** | Inclusion–exclusion counting; equivalence classes via canonical keys and union-find; partial orders and topological sort; pigeonhole arguments for collisions, duplicates and cycles; comparator contracts |
| **Going deeper** | Relational algebra as the theory of SQL; countable vs uncountable sets; Cantor's diagonal argument and its reuse in computability |

## Checklist

- [ ] I can compute unions, intersections, differences and complements, and count a union with inclusion–exclusion.
- [ ] I can generate a power set three ways and explain why it has $2^n$ elements.
- [ ] I can test a relation for the four properties and recognise equivalence relations and partial orders.
- [ ] I can group elements into equivalence classes with a canonical key or union-find.
- [ ] I can say when a function is invertible and connect it to hashing and encoding.
- [ ] I can use the pigeonhole principle to prove a collision, a duplicate or a cycle must exist.
- [ ] I can explain Cantor's diagonal argument and what it means for computability.
