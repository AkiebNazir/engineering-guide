# Topic 21 · Math & Geometry — Python Deep Dive

> Every prior topic organized itself around a DATA STRUCTURE or a SEARCH
> STRATEGY. This topic is different: it's the grab-bag of numeric and
> geometric reasoning tricks that don't fit any of those patterns — they
> live in the arithmetic itself, not in a container you build. The
> throughline is: **exploit the STRUCTURE of numbers (digits, factors,
> ratios) instead of brute-forcing over their VALUES**, because the values
> themselves get astronomically large (factorials, `x^n`, products of two
> huge numbers) or the naive per-item check is too slow at scale (primality,
> line-membership).

---

## Part 0 · The ten problems and their tricks

**Reverse-half-and-compare, not reverse-and-convert** (001 Palindrome
Number): a negative number is never a palindrome (the sign only appears on
one side), and a positive number ending in a nonzero-then-0 digit (e.g.
`120`) can never be one either (a palindrome can't have a leading zero once
reversed) — both are O(1) rejections before doing any digit work. The
elegant trick past that: don't reverse the WHOLE number and compare to the
original (that risks overflow in fixed-width languages, and is unnecessary
work even where it doesn't) — peel digits off the back into a "reversed
half" only until it becomes `>=` the remaining front half, then compare the
two halves directly (adjusting for odd digit-counts by dropping the middle
digit with `// 10`). Python ints don't overflow, but the technique is
worth knowing cold because it's the general pattern for "detect a
palindrome without materializing the full reverse."

```arch
%% caption: Binary exponentiation: n halves every round, so O(log n) multiplications instead of n - 1. For negative n, invert x first.
grid 170x80
node a "pow(x, n)" at 1,0 shape=pill sub="result = 1"
node b "n == 0 ?" at 1,1 shape=diamond color=amber
node z "return result" at 2,1 color=green
node c "n is odd?" at 1,2 shape=diamond color=amber
node e "skip" at 2,2 color=slate
node d "result *= x" at 1,3
node f "x = x * x" at 1,4 color=amber sub="n = n // 2"
a -> b
b -> z : "yes"
b -> c : "no"
c -> d : "yes"
c -> e : "no"
d -> f
e:B -> f:R
f:L -> b:L
```


**Manual carry propagation over an array/string, right-to-left** (002 Plus
One, 005 Multiply Strings): once a number is too big to trust to a fixed
machine word (or the problem explicitly bans converting to int), addition
and multiplication become the grade-school algorithms you'd do on paper —
walk from the least-significant digit, propagate carries forward, and the
result may be LONGER than either input (all-9s plus one grows the array;
two n-digit numbers can produce an (n+1)-digit product but never more).

**Cycle detection over a numeric sequence, not a linked list** (003 Happy
Number): repeatedly applying "sum of squares of digits" to a number either
reaches 1 or falls into a cycle that never includes 1 — this is EXACTLY
the linked-list-cycle problem from **topic 08** (`003_linked_list_cycle`,
`012_find_the_duplicate_number`) with the "next pointer" replaced by a
function call. Both a `seen` set (O(n) extra space) and Floyd's slow/fast
pointer (O(1) extra space) apply unchanged — the technique doesn't care
whether the "next" step follows a `.next` field or evaluates `f(x)`.

**Fast/binary exponentiation** (004 Pow(x, n)): `x^n` doesn't need n-1
multiplications — halving the exponent and squaring the base at each step
is the exact same "halve the search space each round" idea as **topic 05's
binary search**, just multiplicative instead of comparison-based:
`x^n = (x^(n/2))^2` (even n) or `x * (x^((n-1)/2))^2` (odd n), giving
O(log n) multiplications instead of O(n). Negative exponents reduce to
`1 / x^(-n)` after computing the positive case.

**Counting a factor's multiplicity without computing the giant number**
(007 Factorial Trailing Zeroes): trailing zeros in `n!` come from factors
of 10 = 2×5 in the product 1×2×...×n. Factors of 2 are strictly more
abundant than factors of 5 among 1..n (every other number is even, only
every fifth is a multiple of 5), so the count of trailing zeros is bounded
by — and equal to — the count of factor-5's: `floor(n/5) + floor(n/25) +
floor(n/125) + ...` (numbers like 25, 125 contribute more than one factor
of 5 each, which is why the sum has multiple terms). O(log₅ n) time,
never touching the astronomically large value of `n!` itself.

**The Sieve of Eratosthenes vs. trial division per number** (008 Count
Primes): checking one number for primality by trial division is O(√k);
doing that for every k up to n is O(n√n) total. The sieve flips the
question from "is THIS number prime" to "cross off every MULTIPLE of every
prime I've found so far," each composite gets crossed off by its smallest
prime factor, giving O(n log log n) total — a genuinely different
algorithmic shape, not just a constant-factor speedup, and the gap becomes
visible (not just theoretical) once n reaches the hundred-thousands.

**Greedy digit-to-symbol mapping via a lookup table with the subtractive
cases baked in** (006 Integer to Roman): Roman numerals have six
"subtractive" pairs (CM, CD, XC, XL, IX, IV) alongside the six standard
symbols. Instead of special-casing "if the digit is 4 or 9, do X" inside a
digit-by-digit loop, bake ALL twelve values (1000 down to 1, subtractive
pairs interleaved at their correct magnitude) into one ordered
value→symbol table and greedily subtract the largest value that fits,
appending its symbol, looping until the remainder is 0. No branching on
digit identity at all — the table encodes every special case once.

**Hash-map invariant counting for a streaming query** (009 Detect
Squares): each `add(point)` just increments a count in a
`Counter[(x, y)]`; each `count(point)` needs to find axis-aligned squares
with a query corner. Rather than scanning every stored point, only points
sharing an x OR y coordinate with the query can be a square's DIAGONAL
partner — enumerate those diagonal candidates (found via the same
coordinate-count map, keyed the other axis), derive the other two corners
algebraically, and look up their counts in O(1) each. The map that stores
"how many times have I seen this point" doubles as the index for "which
points share my x/y" once you group by axis.

**Slope-as-a-reduced-fraction to dodge floating point** (010 Max Points on
a Line): for each anchor point, group every other point by the "direction"
to it. A float slope (`dy/dx`) is the wrong key — two truly-equal slopes
computed from different (dx, dy) pairs can round to different floats, and
two truly-different slopes can round to the SAME float, both silently
wrong. The fix: reduce `(dx, dy)` by their `gcd` and use the reduced pair
(with a fixed sign convention) as an exact, hashable dictionary key —
never divide. Vertical lines (`dx == 0`) and duplicate points (`dx == dy
== 0`, which augment every line's count but define no slope of their own)
need explicit handling outside the slope map.

```arch
%% caption: Slope as a reduced fraction avoids floating point: equal slopes produce identical (dx, dy) keys.
grid 200x75
node a "anchor p and another point q" at 0,0 shape=pill w=260
node b "dx = qx - px" at 0,1 w=260 sub="dy = qy - py"
node c "g = gcd(dx, dy)" at 0,2 w=260
node d "Normalise the sign" at 0,3 color=amber w=260 sub="key = (dx/g, dy/g)"
node e "count[key] for this anchor" at 0,4 color=green w=260 sub="max count + 1 = most points on one line"
a -> b -> c -> d -> e
```


---

## Part 1 · Why these don't belong in earlier topics

001–010 could each superficially be filed under "arrays" or "strings" or
"hash maps," but the graded skill in every one of them is: **recognize the
NUMERIC or GEOMETRIC structure that lets you avoid brute force**, not
manipulate a container. There's no tree to walk, no window to slide, no
graph to search — the insight is always something like "half the number
suffices," "only the factor-of-5 count matters," "only diagonal-sharing
points matter," "a reduced integer pair is an exact key where a float
isn't." That's a fundamentally different kind of interview signal than
"do you know how to use a heap," and it's why this topic exists
separately even though several individual problems reuse tools (hash
maps, gcd, sieve) seen elsewhere.

---

## Part 2 · Problem-by-problem map

| # | Problem | Difficulty | Core trick |
|---|---|---|---|
| 001 | Palindrome Number | Easy | reverse only the second half, compare halves |
| 002 | Plus One | Easy | manual carry propagation, array can grow by one digit |
| 003 | Happy Number | Easy | cycle detection over `f(x)` — set or Floyd's (cf. topic 08) |
| 004 | Pow(x, n) | Medium | binary/fast exponentiation, O(log n) — same halving idea as binary search |
| 005 | Multiply Strings | Medium | grade-school multiply into an `m+n`-sized result array |
| 006 | Integer to Roman | Medium | greedy table with subtractive pairs baked in |
| 007 | Factorial Trailing Zeroes | Medium | count factors of 5, never compute n! |
| 008 | Count Primes | Medium | Sieve of Eratosthenes, O(n log log n) |
| 009 | Detect Squares | Medium | hash map of point counts, iterate diagonal candidates only |
| 010 | Max Points on a Line | Hard | gcd-reduced (dx, dy) as an exact slope key |

---

## Part 3 · Cross-references worth remembering

- **003 ↔ topic 08** (`003_linked_list_cycle`, `012_find_the_duplicate_number`):
  same Floyd's-cycle-detection technique, applied to a numeric function
  instead of a `.next` pointer. If you can write one, you can write the
  other — the "tortoise and hare" invariant doesn't care what "next" means.
- **004 ↔ topic 05** (Binary Search): halving a search space each step is
  the shared idea; binary search halves by COMPARISON, fast exponentiation
  halves by ARITHMETIC (squaring), but both turn O(n) into O(log n) by
  discarding half the remaining work every round.
- **008's sieve ↔ topic 22** (Sorting Algorithms, upcoming): both are
  examples of "do a little more work up front to avoid repeating a check
  per element" — the sieve amortizes primality checks the same way a
  counting sort amortizes comparisons.
- **009/010's hash-map keying** is the same "make the dictionary key exact
  and collision-free" discipline as topic 01's anagram/grouping problems —
  here the key is a coordinate tuple or a gcd-reduced direction instead of
  a sorted string or character count.

---

## Part 4 · Where this topic ends

Ten problems, each a self-contained trick rather than an extensible
pattern family — there's no "topic 21 continued." The transferable skill
is recognizing, fast, when a problem is secretly about the STRUCTURE of a
number or a geometric relationship (parity of digits, factor
multiplicity, exact rational slope) rather than about searching, sorting,
or traversing a container.

<!-- block:21_py_1_toolkit -->
## Part 5 · The Number-Theory and Geometry Toolkit the Ten Problems Draw On

Part 0 explains the ten tricks. Interviews in this area rarely ask those ten — they ask for the *toolkit* underneath:
GCD and modular arithmetic, primes, and a handful of geometry primitives. Every snippet below was run, and every timing is a
measurement from this machine (CPython 3.13).

```arch
%% caption: Most math problems reduce to one of five moves: exploit divisibility, work modulo something, sieve, exponentiate by squaring, or replace a float by an exact rational.
grid 200x80
node q "A math problem" at 0,1 shape=pill
node a "What blows up or repeats?" at 0,2 shape=diamond color=amber
node b "Exponentiation by squaring" at 1,0 color=green w=380 sub="a huge value (x^n, n!, a big product) · work mod p; never build the full number"
node c "gcd, lcm, prime factorisation" at 1,1 color=green w=380 sub="divisibility / common factors"
node d "Sieve once" at 1,2 color=green w=380 sub="many primality or factor queries · smallest-prime-factor table"
node e "Reduce by gcd, fix the sign" at 1,3 color=amber w=380 sub="a ratio, slope or fraction as a key · never a float"
node f "Cross product with integers" at 1,4 color=green w=380 sub="orientation, area, intersection"
q -> a
a:R -> b:L
a:R -> c:L
a:R -> d:L
a:R -> e:L
a:R -> f:L
```

### 5.1 GCD, LCM and the extended Euclidean algorithm

`math.gcd` and `math.lcm` (3.9+) are in the standard library; `gcd(84, 36) = 12`, `lcm(4, 6) = 12`. The *extended* algorithm
also returns Bézout coefficients `x, y` with `a·x + b·y = gcd(a, b)`, which is what a **modular inverse** is:

```python
def ext_gcd(a, b):
    if b == 0: return a, 1, 0
    g, x, y = ext_gcd(b, a % b)
    return g, y, x - (a // b) * y           # ext_gcd(240, 46) -> (2, -9, 47):  240·(-9) + 46·47 = 2
```

### 5.2 Modular arithmetic: inverses, `pow(x, n, m)` and combinations

Working "modulo `p`" keeps numbers small; the only operation that is *not* automatic is **division**, which becomes
multiplication by the modular inverse. Python does both natively:

```python
MOD = 10**9 + 7
pow(3, 5, MOD)                  # fast modular exponentiation — never x**n % MOD (that builds the whole number first)
pow(3, -1, MOD)                 # 333333336: the modular inverse (Python 3.8+); 3 * 333333336 % MOD == 1
pow(6, -1, 9)                   # ValueError: base is not invertible for the given modulus  (gcd(6, 9) != 1)
```

An inverse exists **iff** `gcd(a, m) == 1`. For a *prime* modulus, Fermat's little theorem gives `a⁻¹ ≡ a^(p−2)`. That makes
`nCr mod p` cheap: precompute factorials and inverse factorials once, and each query is three multiplications:

```python
fact = [1] * (N + 1)
for i in range(1, N + 1): fact[i] = fact[i-1] * i % MOD
inv_fact = [pow(f, MOD - 2, MOD) for f in fact]
nCr = lambda n, r: 0 if r < 0 or r > n else fact[n] * inv_fact[r] % MOD * inv_fact[n - r] % MOD
# nCr(5, 2) = 10    nCr(10, 3) = 120    nCr(1000, 500) matches math.comb(1000, 500) % MOD
```

Never divide with `//` inside a modular expression — `(a // b) % m` is not `a · b⁻¹ % m`. Catalan numbers are
`comb(2n, n) // (n + 1)` → `1, 1, 2, 5, 14, 42, 132, 429`, and Fibonacci in O(log n) uses **fast doubling**
(`F(2k) = F(k)(2F(k+1) − F(k))`, `F(2k+1) = F(k)² + F(k+1)²`): `F(90) = 2880067194370816120`.

### 5.3 Primes: trial division, the sieve, and a factor table

| Method | Cost | Use when |
|---|---|---|
| Trial division up to `isqrt(n)` | O(√n) per number | a few checks |
| **Sieve of Eratosthenes** | O(n log log n) once | *every* prime up to `n` |
| **Smallest-prime-factor (SPF) sieve** | O(n log log n) once, then O(log x) per factorisation | many factorisation queries |
| Miller–Rabin | O(k · log³ n) | a single huge `n` (up to 64 bits, deterministically) |

Measured: counting the 9,592 primes below 100,000 took **49 ms** by trial division and **0.3 ms** with a `bytearray` sieve —
and the sieve found the 78,498 primes below 10⁶ in **2.9 ms**. The sieve's two details (Problem 008): start crossing off at
`i*i` (smaller multiples were already removed), and stop `i` at `isqrt(n)`. Slice assignment
(`is_p[i*i::i] = bytearray(...)`) does the inner loop in C.

```python
spf = list(range(n + 1))
for i in range(2, isqrt(n) + 1):
    if spf[i] == i:
        for j in range(i * i, n + 1, i):
            if spf[j] == j: spf[j] = i
def factorize(x):
    out = []
    while x > 1: out.append(spf[x]); x //= spf[x]
    return out                              # factorize(84) -> [2, 2, 3, 7]     factorize(97) -> [97]
```

**Miller–Rabin** tests primality of one large number by writing `n − 1 = d·2^s` and checking witnesses. With the twelve
bases `2, 3, 5, …, 37` it is *deterministic* for every `n < 3.3·10²⁴`. It correctly says `2⁶¹ − 1` (a Mersenne prime) is prime,
`2⁶¹ + 1` is not, the Carmichael number `561` is not (Fermat's test alone is fooled by it), and it finds 168 primes below 1000.

### 5.4 Exact integers beat floats — and `isqrt` beats `sqrt`

Floats have 53 bits of mantissa, so anything above ~9·10¹⁵ is inexact. `int(math.sqrt(10**60 - 1))` returns `10**30`
(wrong — the floor of the true root is `10**30 − 1`); `math.isqrt(10**60 - 1)` returns the exact `10**30 − 1`. The same discipline
is why Problem 010 keys slopes on a gcd-reduced integer pair rather than `dy / dx`, and why `0.1 + 0.2 == 0.3` is `False`
while `Fraction(1, 10) + Fraction(2, 10) == Fraction(3, 10)` is `True`. Compare floats with `math.isclose`, use
`fractions.Fraction` or `decimal.Decimal` for exact rationals, and remember Python's `round` is **banker's rounding**:
`round(0.5) == 0`, `round(1.5) == 2`, `round(2.5) == 2`.

### 5.5 Geometry with integers: the cross product

Almost every geometry primitive is one integer expression, the **cross product** `cross(o, a, b) = (a−o) × (b−o)`. Its sign is
the turn direction; its magnitude is twice the triangle's area:

```python
cross = lambda o, a, b: (a[0]-o[0]) * (b[1]-o[1]) - (a[1]-o[1]) * (b[0]-o[0])
cross((0,0),(4,0),(4,3))     # +12  counter-clockwise (left turn)
cross((0,0),(4,0),(4,-3))    # -12  clockwise (right turn)
cross((0,0),(2,2),(4,4))     #   0  collinear
```

| Primitive | Built from | Note |
|---|---|---|
| Collinear (three points) | `cross == 0` | Exact with integers — no slope, no division. |
| Polygon area | shoelace: `½ · |Σ (xᵢ·yᵢ₊₁ − xᵢ₊₁·yᵢ)|` | Rectangle `(0,0),(4,0),(4,3),(0,3)` → `12.0`; triangle → `6.0`. |
| Do two segments intersect? | four cross products (opposite sides) **plus** the collinear-on-segment cases | The collinear cases are the classic omission. |
| Point in polygon | ray casting: count edges a horizontal ray crosses; odd = inside | `(2,2)` inside the unit square of side 4, `(5,2)` outside. |
| Convex hull | Andrew's monotone chain, O(n log n) | Pop while the last turn is not strictly left (`<= 0` also drops collinear points). |
| Rectangles overlap | `a.x1 < b.x2 and b.x1 < a.x2 and a.y1 < b.y2 and b.y1 < a.y2` | Strict `<`: touching edges do **not** overlap. |
| Distance comparisons | compare **squared** distances | `sqrt` is monotonic — skip it (and its rounding). |

```python
# Andrew's monotone chain
lower, upper = [], []
for p in pts:                                             # pts sorted by (x, y)
    while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0: lower.pop()
    lower.append(p)
for p in reversed(pts):
    while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0: upper.pop()
    upper.append(p)
hull = lower[:-1] + upper[:-1]       # [(1,1),(2,2),(2,0),(2,4),(3,3),(4,2)] -> [(1,1),(2,0),(4,2),(2,4)]
```

Segment intersection is true for the crossing pair `(0,0)-(4,4)` / `(0,4)-(4,0)`, false for the *collinear but disjoint*
`(0,0)-(1,1)` / `(2,2)-(3,3)`, and **true** for the collinear *overlapping* `(0,0)-(2,2)` / `(1,1)-(3,3)` — which is why the
collinear-and-on-segment checks cannot be skipped.

### 5.6 Digit and base tricks

| Task | Pattern |
|---|---|
| Digit sum / reverse digits | `while n: n, d = divmod(n, 10)` |
| Convert to base `b` | repeated `divmod`, collect remainders, reverse |
| Number of digits | `len(str(n))`, or `int(math.log10(n)) + 1` (beware exact powers of ten in floats) |
| Add / multiply digit arrays | right-to-left with a carry; the result may be one digit longer |
| Trailing zeros of `n!` | `Σ n // 5ᵏ` (Problem 007) — count the factor **5**, never build `n!` |
| Reverse an integer safely | check the 32-bit range *before* the multiply (a fixed-width concern; Python never overflows) |

### 5.7 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "The answer is huge — return it mod `10⁹ + 7`." | Reduce after every multiply; division is multiplication by `pow(x, -1, MOD)`. |
| "Many queries on the same range." | Sieve once (or an SPF table); precompute factorials and inverse factorials. |
| "Is this one large number prime?" | Miller–Rabin with fixed bases (deterministic below 3.3·10²⁴). |
| "No floating point allowed." | Cross products, gcd-reduced pairs, `Fraction`, `isqrt`. |
| "Overflow in a fixed-width language?" | Use a wider type for the product, or check before multiplying (`a > MAX / b`). |
| "Why is the sieve O(n log log n)?" | Each prime `p` crosses off `n/p` entries; `Σ n/p` over primes is `n log log n`. |

---
<!-- /block:21_py_1_toolkit -->

<!-- problem-map:start -->
## Part 6 · Every Problem in This Topic, by Pattern

Ten problems, five moves (digit arithmetic · cycle detection over a numeric sequence · exponentiation by squaring · counting factors · exact keys instead of floats). Each **Trap** is a mistake documented in that problem's solution file.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Palindrome Number](PyDSA/21_math_geometry/001_palindrome_number_solution.py) <br>LC 9 · Easy | Reverse half, then compare | A negative number, or a positive one ending in `0`, is never a palindrome; peel digits into a reversed half until it is `>=` the remaining front half, then compare (dropping the middle digit for odd lengths). **Trap:** converting to a string; reversing the *whole* number (overflows in fixed-width languages — `1534236469`); forgetting the odd-length `// 10`. |
| [002 · Plus One](PyDSA/21_math_geometry/002_plus_one_solution.py) <br>LC 66 · Easy | Carry, right to left | Walk from the least-significant digit adding the carry; an all-9s input grows the array by one. **Trap:** no post-loop carry branch (`[9,9,9] → [0,0,0]`); appending the 1 at the wrong end (`digits + [1]`); converting to `int`. |
| [003 · Happy Number](PyDSA/21_math_geometry/003_happy_number_solution.py) <br>LC 202 · Easy | Cycle detection on a number sequence | "Sum of squares of digits" reaches 1 or falls into a cycle — the linked-list cycle problem (topic 08) over `f(n)`. **Trap:** no cycle detection (loops forever); comparing `slow == fast` before advancing either pointer. |
| [004 · Pow(x, n)](PyDSA/21_math_geometry/004_powx_n_solution.py) <br>LC 50 · Medium | Exponentiation by squaring | `x^n` in `O(log n)` multiplications: square `x`, halve `n`, multiply into the result on odd bits; invert `x` first for negative `n`. **Trap:** recursing on a negative `n`; testing parity of a negative `n` with `%` in a language where the remainder is negative; the odd-case off-by-one. |
| [005 · Multiply Strings](PyDSA/21_math_geometry/005_multiply_strings_solution.py) <br>LC 43 · Medium | Grade-school multiplication | Digit `i` times digit `j` lands at positions `i + j` (carry out) and `i + j + 1` (units); a final carry pass. **Trap:** `int(a) * int(b)` (bans the point); mapping both digits to `i + j`; skipping the carry pass. |
| [006 · Integer to Roman](PyDSA/21_math_geometry/006_integer_to_roman_solution.py) <br>LC 12 · Medium | A flat greedy table | Descending `(value, symbol)` pairs *including the six subtractive forms* (`CM`, `CD`, `XC`, `XL`, `IX`, `IV`), repeated subtraction. **Trap:** separate `if` blocks per place value; omitting a subtractive entry (`1940` → `MCMXXXX`). |
| [007 · Factorial Trailing Zeroes](PyDSA/21_math_geometry/007_factorial_trailing_zeroes_solution.py) <br>LC 172 · Medium | Count the factor 5 | Trailing zeros = the number of factors of 5 in `n!`: `n//5 + n//25 + n//125 + …`, never computing `n!`. **Trap:** `n // 5` alone (undercounts multiples of 25); counting factors of 2; computing `n!` first. |
| [008 · Count Primes](PyDSA/21_math_geometry/008_count_primes_solution.py) <br>LC 204 · Medium | Sieve of Eratosthenes | Cross off multiples starting at `i*i`, for `i` up to `√n`. O(n log log n). **Trap:** starting at `2*i` (correct but slower); an off-by-one on "strictly less than `n`". |
| [009 · Detect Squares](PyDSA/21_math_geometry/009_detect_squares_solution.py) <br>LC 2013 · Medium | Hash the points, scan one column | A square through the query point has a diagonal partner in the *same column*: for each stored `y != py` the side is `\|y − py\|`, and the other two corners are counted from a `Counter`. **Trap:** scanning *all* points; not skipping `y == py` (a zero-area "square"). |
| [010 · Max Points on a Line](PyDSA/21_math_geometry/010_max_points_on_a_line_solution.py) <br>LC 149 · Hard | A gcd-reduced integer slope key | Reduce `(dx, dy)` by their gcd and fix the sign so the same direction always yields the same key; count the maximum per anchor point. **Trap:** `dy / dx` as a float key (two *different* slopes can round to one float — `165580141/102334155` and `267914296/165580141` both print `1.618033988749895`, demonstrated in the solution file); reducing without a sign convention (`(1,2)` vs `(-1,-2)`). |

---
<!-- problem-map:end -->


## Checklist Before Leaving This Topic <!--ca-->

- [ ] Compute a modular inverse with `pow(a, -1, m)` and say when it does not exist (`gcd(a, m) != 1`) <!--ca-->
- [ ] Write `nCr mod p` from precomputed factorials and inverse factorials <!--ca-->
- [ ] Choose between trial division, a sieve, an SPF table and Miller–Rabin, and quote the sieve's measured advantage <!--ca-->
- [ ] Use `math.isqrt` and integer cross products instead of `sqrt` and slopes <!--ca-->
- [ ] Write segment intersection *including* the collinear cases, and the monotone-chain convex hull <!--ca-->
