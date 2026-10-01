# Topic 21 · Math & Geometry — Go Deep Dive

> Math problems look language-agnostic until you actually run them. Go's fixed-width,
> silently-wrapping integers, a `%` operator that disagrees with Python about signs,
> and a standard library missing `gcd`, `lcm`, and modular `pow` mean the same
> "obviously correct" formula you'd paste from a Python solution can be silently
> wrong the moment it touches Go. This is the document that stops those bugs.

---

## Part 1 · Integer Overflow Is the Headline Bug Here

### 1.1 Go's `int` is fixed-width and wraps silently

Go's `int` is **platform-dependent**: 64 bits on amd64/arm64 (essentially every
machine you'll run this on), but the language spec only guarantees it is *at
least* 32 bits — some 32-bit embedded targets really do give you a 32-bit `int`.
Never assume "`int` in Go behaves like Python's arbitrary-precision integers."
It doesn't, on any platform.

```go
var x int32 = 1 << 30
y := x * 4          // overflows int32, wraps silently — no panic, no error
fmt.Println(y)      // 0, not 4294967296

var m int64 = math.MaxInt64
fmt.Println(m + 1)  // wraps to math.MinInt64 — silent, no exception
```

Python's `int` grows arbitrarily; `2**100` just works. The equivalent Go
expression `1 << 100` doesn't compile against a 64-bit `int`, and even values
that *do* fit at the end can overflow in an **intermediate** step:

```go
a, b := 1_000_000_000, 3
c := a * b           // 3_000_000_000 — fits in int64, but would overflow int32
```

> ⚠️ **The practical rule:** the moment a problem statement says "the answer may
> not fit in a 32-bit integer," or you're multiplying two large `int`s together,
> declare the variable `int64` explicitly — don't rely on `int` defaulting to 64
> bits. Code that's correct on your amd64 laptop and wrong on a 32-bit target is
> a real, if rare, portability trap, and being explicit costs nothing.

### 1.2 `%` disagrees with Python about the sign

This is the single most common silent bug when porting modular-arithmetic code
from Python to Go.

```go
fmt.Println(-7 % 3)   // -1 in Go  — keeps the sign of the DIVIDEND
```
```python
print(-7 % 3)          # 2 in Python — keeps the sign of the DIVISOR
```

Go's `%` is a true C-style remainder operator; Python's `%` is a true modulo
operator. They agree when both operands are positive and disagree the instant
either is negative. Math/geometry problems constantly ask for results
`mod 1e9+7`, and intermediate subtractions (`(a - b) % m`) go negative all the
time.

```go
// ✅ always non-negative result, matching Python's %
func mod(x, m int64) int64 {
    return ((x % m) + m) % m
}
```

> ⚠️ Forgetting this doesn't crash — it returns a negative "modular" answer that
> looks plausible and fails only on specific inputs. Bake `mod()` into any
> problem that mentions `10^9 + 7`.

---

## Part 2 · Standard-Library Gaps You Must Fill Yourself

Python's `math` module hands you `gcd`, `lcm`, and a three-argument `pow` for
modular exponentiation. **Go's `math` package has none of these.** You hand-roll
all three, every time.

### 2.1 GCD and LCM — Euclid's algorithm

```go
func gcd(a, b int64) int64 {
    for b != 0 {
        a, b = b, a%b
    }
    return a
}

func lcm(a, b int64) int64 {
    return a / gcd(a, b) * b   // divide first — shrinks the operands before
                                // the multiply, reducing overflow risk
}
```

`math.gcd`/`math.lcm` exist in Python 3.9+ as a single stdlib call. In Go this
is ~6 lines you write from memory every time — know it cold.

### 2.2 Fast modular exponentiation

Python's built-in `pow(base, exp, mod)` does binary exponentiation for you in C.
Go's `math.Pow` only returns a `float64` and has **no modulus argument at all** —
using it for anything beyond small exact integers loses precision immediately.
You must hand-roll square-and-multiply:

```go
// powMod computes (base^exp) mod m in O(log exp) using binary exponentiation.
func powMod(base, exp, m int64) int64 {
    base %= m
    if base < 0 {
        base += m
    }
    result := int64(1)
    for exp > 0 {
        if exp&1 == 1 {
            result = result * base % m
        }
        base = base * base % m
        exp >>= 1
    }
    return result
}
```

> ⚡ Each squaring step is O(1) arithmetic on `int64`; the loop runs `O(log exp)`
> times. Naively multiplying `base` by itself `exp` times is O(exp) — for
> `exp = 10^9` that's the difference between instant and never-finishing.

```arch
%% caption: Binary exponentiation: n halves every round, so O(log n) multiplications instead of n - 1. For negative n, invert x first.
grid 170x80
node a "pow(x, n)" at 1,0 shape=pill sub="result = 1"
node b "n == 0 ?" at 1,1 shape=diamond color=amber
node z "return result" at 2,1 color=green
node c "n is odd?" at 1,2 shape=diamond color=amber
node e "skip" at 2,2 color=slate
node d "result *= x" at 1,3
node f "x = x * x" at 1,4 color=amber sub="n = n / 2"
a -> b
b -> z : "yes"
b -> c : "no"
c -> d : "yes"
c -> e : "no"
d -> f
e:B -> f:R
f:L -> b:L
```

### 2.3 Primality — no shortcuts either

```go
func isPrime(n int64) bool {
    if n < 2 {
        return false
    }
    for i := int64(2); i*i <= n; i++ {   // i*i avoids a float Sqrt call
        if n%i == 0 {
            return false
        }
    }
    return true
}
```

Using `i*i <= n` instead of `i <= math.Sqrt(float64(n))` sidesteps Part 3's
float-precision trap entirely — prefer it whenever the bound fits comfortably
in the integer type.

---

## Part 3 · Floating Point Gotchas

### 3.1 `math` functions are all `float64` in, `float64` out

```go
n := 50
r := math.Sqrt(float64(n))   // explicit conversion in — Go never does this implicitly
fmt.Println(int(r))          // truncates toward zero, NOT rounds
```

Two traps stack here: `int(r)` **truncates**, it does not round — `int(4.9999999)`
is `4`, which matters when float imprecision nudges an exact integer result
slightly under its true value. This bites hardest right at perfect squares:

```go
n := 2147395600          // = 46340 * 46340, a perfect square
r := int(math.Sqrt(float64(n)))
// r can come out as 46339 on some inputs due to float64 rounding in Sqrt,
// even though the true root is the exact integer 46340
```

> ⚠️ **The safe fix:** never trust `int(math.Sqrt(x))` as the final answer when
> exactness matters — verify and nudge:
> ```go
> r := int(math.Sqrt(float64(n)))
> for r*r > n {
>     r--
> }
> for (r+1)*(r+1) <= n {
>     r++
> }
> // r is now the exact integer floor(sqrt(n)), no float trust required
> ```

### 3.2 Comparing floats

```go
if math.Abs(a-b) < 1e-9 { /* "equal" */ }   // ✅
if a == b { /* ⚠️ almost never what you want for computed floats */ }
```

Same rule as every other language with IEEE-754 floats — Go is not special
here, but it's worth stating since geometry problems (distances, slopes,
areas) are float-heavy by nature.

---

## Part 4 · Geometry Primitives

### 4.1 In-place matrix rotation (transpose + reverse)

Rotating an `n×n` matrix 90° clockwise in O(1) extra space: transpose across
the main diagonal, then reverse each row. (Full matrix-representation tradeoffs
— `[][]int` vs a flattened `[]int` — are covered in Topic 24; this is just the
rotation algorithm.)

```go
func rotate(matrix [][]int) {
    n := len(matrix)
    for i := 0; i < n; i++ {                  // transpose
        for j := i + 1; j < n; j++ {
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
        }
    }
    for i := 0; i < n; i++ {                  // reverse each row
        for l, r := 0, n-1; l < r; l, r = l+1, r-1 {
            matrix[i][l], matrix[i][r] = matrix[i][r], matrix[i][l]
        }
    }
}
```

Go's multi-assignment tuple-swap (`a, b = b, a`) makes both passes read cleanly
with no temp variable — the same idiom called out in the arrays/hashing guide.

### 4.2 Spiral traversal — boundary tracking

Four shrinking boundaries (`top, bottom, left, right`) walked in turn; the loop
condition `top <= bottom && left <= right` re-checked **between each of the
four directional walks**, not just once per outer iteration — a very common
off-by-one source when a row or column empties out mid-layer.

```go
func spiralOrder(matrix [][]int) []int {
    if len(matrix) == 0 {
        return nil
    }
    top, bottom := 0, len(matrix)-1
    left, right := 0, len(matrix[0])-1
    res := make([]int, 0, len(matrix)*len(matrix[0]))

    for top <= bottom && left <= right {
        for c := left; c <= right; c++ { res = append(res, matrix[top][c]) }
        top++
        for r := top; r <= bottom; r++ { res = append(res, matrix[r][right]) }
        right--
        if top <= bottom {
            for c := right; c >= left; c-- { res = append(res, matrix[bottom][c]) }
            bottom--
        }
        if left <= right {
            for r := bottom; r >= top; r-- { res = append(res, matrix[r][left]) }
            left++
        }
    }
    return res
}
```

### 4.3 Cross product — orientation / turn direction

The 2D cross product's **sign** tells you whether three points turn left,
right, or are collinear — the primitive underneath convex hull, line
intersection, and polygon-area problems.

```go
type point struct{ x, y int }

// cross returns (b-a) × (c-a). Positive: counter-clockwise turn at b.
// Negative: clockwise turn. Zero: a, b, c are collinear.
func cross(a, b, c point) int {
    return (b.x-a.x)*(c.y-a.y) - (b.y-a.y)*(c.x-a.x)
}
```

```
        c
       ╱
      ╱     cross(a,b,c) > 0 → counter-clockwise (left turn)
     b
    ╱
   a
```

> ⚡ Keep this in integer arithmetic whenever input coordinates are integers —
> converting to `float64` for a cross product reintroduces Part 3's comparison
> problems for zero gratuitously.

---

## Part 5 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Integer size | Arbitrary precision | Fixed-width, **wraps silently** on overflow |
| `%` sign | Matches the **divisor** (non-negative) | Matches the **dividend** (can be negative) |
| `gcd`/`lcm` | `math.gcd`, `math.lcm` (3.9+) built in | Hand-roll Euclid's algorithm |
| Modular exponentiation | `pow(base, exp, mod)` built in | Hand-roll binary exponentiation |
| `sqrt`/`pow` | Work on `int` and `float` transparently | `float64` only — explicit conversions both ways |
| Big numbers | Native | Need `math/big` (not covered here — rare in interviews) |

---

## Part 6 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| Euclid's GCD / LCM | O(log(min(a,b))) | O(1) | LC 1979, LC 2 (add w/ carry-style problems) |
| Fast modular exponentiation | O(log exp) | O(1) | LC 50 Pow(x, n), competitive "mod 1e9+7" problems |
| Trial-division primality | O(√n) | O(1) | LC 204 Count Primes (sieve variant), LC 263 |
| Sieve of Eratosthenes | O(n log log n) | O(n) | LC 204 Count Primes |
| In-place matrix rotation | O(n²) | O(1) | LC 48 Rotate Image |
| Spiral boundary walk | O(rows·cols) | O(1)* | LC 54 Spiral Matrix |
| Cross-product orientation | O(1) per triple | O(1) | LC 149 Max Points on a Line, convex hull |

\* excluding the output slice

---

## Part 7 · Building It From Scratch — Modular Arithmetic Toolkit

```go
package main

// gcd returns the greatest common divisor via Euclid's algorithm.
func gcd(a, b int64) int64 {
    for b != 0 {
        a, b = b, a%b
    }
    return a
}

// lcm returns the least common multiple. Dividing before multiplying keeps
// the intermediate product as small as possible, reducing overflow risk.
func lcm(a, b int64) int64 {
    return a / gcd(a, b) * b
}

// mod returns x mod m in the mathematical (always non-negative) sense,
// matching Python's % rather than Go's native dividend-signed %.
func mod(x, m int64) int64 {
    return ((x % m) + m) % m
}

// powMod computes (base^exp) mod m in O(log exp) via binary exponentiation.
// base is reduced mod m up front (and corrected to non-negative) so every
// subsequent multiply-mod stays within a safe range for int64 arithmetic.
func powMod(base, exp, m int64) int64 {
    base = mod(base, m)
    result := int64(1)
    for exp > 0 {
        if exp&1 == 1 {
            result = result * base % m   // both operands < m, so the
        }                                 // product safely fits int64
        base = base * base % m
        exp >>= 1
    }
    return result
}
```

**Talk track while writing:** `gcd` first because `lcm` depends on it; divide
before multiplying in `lcm` to keep numbers small; `mod` exists because Go's
`%` disagrees with the mathematical definition on negative input; `powMod`
reduces `base` mod `m` *before* the loop and after every multiply, so no
intermediate product ever exceeds `m² ` — safely inside `int64` for any `m`
that itself fits in `int64` without its square overflowing (true for the
`10^9`-scale moduli these problems use).

---

<!-- block:21_go_1_toolkit -->
## Part 8 · The Number-Theory and Geometry Toolkit in Go — Where Every Product Can Wrap

Parts 1–7 cover Go's integer, float and standard-library gaps and the in-place matrix and geometry primitives. What
interviews actually probe is the toolkit *underneath* the ten problems — modular arithmetic, primes, exact roots, integer geometry — and in Go each of those has one
extra question: **can an intermediate value leave the type?** Every snippet below was compiled with `go vet` and run on
Go 1.24; every timing is the best of nine runs on this machine.

```arch
%% caption: In Go, decide how wide the intermediate value can get before writing the formula — and never let a float be a key.
grid 200x80
node q "A math expression in Go" at 0,0 shape=pill w=220
node a "How large can an\nintermediate get?" at 0,2 shape=diamond color=amber w=260
node b "int64 is enough: a * b % m" at 1,0 color=green w=340 sub="a product of two values below m, m at most 3.04 billion"
node c "bits.Mul64 + bits.Div64" at 1,1 color=green w=340 sub="modulus up to 2^64 · 128-bit product"
node d "math/big" at 1,2 color=green w=340 sub="genuinely unbounded"
node e "gcd-reduced [2]int key, never float64" at 1,3 color=amber w=340 sub="a ratio or slope is the map key"
node f "math.Sqrt, then correct with r*r" at 1,4 color=amber w=340 sub="the square root of an integer"
q -> a
a:R -> b:L
a:R -> c:L
a:R -> d:L
a:R -> e:L
a:R -> f:L
```

### 8.1 The overflow ladder: `int64` → 128-bit → `math/big`

Go's integers wrap silently — there is no panic and no exception. `x := int64(4_000_000_000); x*x % 1_000_000_007` prints
`-582343224`, not the true `784`. Three more wraps worth knowing by heart, all measured:

- `-x` for the most negative value is itself: `-int32(math.MinInt32) == math.MinInt32` is `true`.
- `math.MinInt64 / -1` does **not** panic; it returns `math.MinInt64` (and `%` returns `0`).
- `20!` fits in `int64` (`2432902008176640000`) but `21!` prints `-4249290049419214848` — never build a factorial.

For modular work the rule is: **if both operands are below `m`, `a*b` fits `int64` exactly when `m ≤ 3,037,000,500`**
(`⌊√(2⁶³−1)⌋ = 3,037,000,499`, and the largest operand is `m−1`; checked directly: `(m−1)² % m == 1` holds for `m = 3037000500`
and fails for `3037000501`). Every `10⁹ + 7` and `998244353` problem is safely inside. Beyond that, take the 128-bit product
from `math/bits`:

```go
// mulMod returns a*b mod m for any m < 2^64 — the product is computed in 128 bits.
func mulMod(a, b, m uint64) uint64 {
    hi, lo := bits.Mul64(a, b)
    _, rem := bits.Div64(hi%m, lo, m) // Div64 panics if hi >= m, so reduce hi first
    return rem
}

func powMod64(b, e, m uint64) uint64 {
    r := uint64(1) % m
    b %= m
    for ; e > 0; e >>= 1 {
        if e&1 == 1 { r = mulMod(r, b, m) }
        b = mulMod(b, b, m)
    }
    return r
}
```

`(hi·2⁶⁴ + lo) mod m = ((hi mod m)·2⁶⁴ + lo) mod m`, so reducing `hi` first changes nothing — and it is *required*:
`bits.Div64` panics with `runtime error: integer overflow` when `hi >= m` (measured). With `m = 10¹⁸ + 3` and operands
`m−4`, `m−5`, `mulMod` returns the correct `20`, while the plain `a*b % m` returns `919594847110692839`. When the numbers are
unbounded (big factorials, RSA-sized moduli), `math/big` is the tool — slower, but never wrong.

### 8.2 Extended GCD, modular inverse, and `big.Int.ModInverse`

```go
func extGCD(a, b int64) (g, x, y int64) { // a·x + b·y = g
    if b == 0 { return a, 1, 0 }
    g, x1, y1 := extGCD(b, a%b)
    return g, y1, x1 - (a/b)*y1
}

// modInv returns a⁻¹ mod m; ok is false when gcd(a, m) != 1.
func modInv(a, m int64) (int64, bool) {
    g, x, _ := extGCD(((a%m)+m)%m, m)   // normalise first: Go's % keeps the dividend's sign
    if g != 1 { return 0, false }
    return ((x % m) + m) % m, true
}
```

`extGCD(240, 46)` returns `(2, -9, 47)`; `modInv(3, 1e9+7)` is `333333336`; `modInv(6, 9)` reports *not invertible*;
`modInv(-3, 7)` is `2` because the input is normalised. For a **prime** modulus, Fermat gives the shorter form
`powMod(a, MOD-2, MOD)`. `math/big` has it built in — `new(big.Int).ModInverse(g, n)` — and returns **`nil`** when no inverse
exists (measured), so nil-check the result before using it.

One Go-only trap while you are here: Euclid's algorithm on *negative* inputs returns a **negative** gcd, because `%`
follows the dividend — `gcd(4, -6) = -2` and `gcd(-4, -6) = -2` (measured). Take the absolute value before dividing by it.

### 8.3 `nCr mod p` from factorials and inverse factorials

Division mod `p` is multiplication by an inverse, and one `powMod` is enough for *all* the inverse factorials:

```go
type Comb struct{ fact, inv []int64 }

func NewComb(n int) *Comb {
    c := &Comb{make([]int64, n+1), make([]int64, n+1)}
    c.fact[0] = 1
    for i := 1; i <= n; i++ { c.fact[i] = c.fact[i-1] * int64(i) % MOD }
    c.inv[n] = powMod(c.fact[n], MOD-2, MOD)            // the only exponentiation
    for i := n; i > 0; i-- { c.inv[i-1] = c.inv[i] * int64(i) % MOD } // (i-1)!⁻¹ = i!⁻¹ · i
    return c
}

func (c *Comb) C(n, r int) int64 {
    if r < 0 || r > n { return 0 }
    return c.fact[n] * c.inv[r] % MOD * c.inv[n-r] % MOD
}
// C(5,2) = 10   C(10,3) = 120   C(1000,500) matches big.Int.Binomial(1000,500) mod 1e9+7
```

Setup is O(N), each query O(1). This needs a **prime** modulus (or one coprime to every factor up to `n`); for an arbitrary
modulus fall back to Pascal's triangle, `C[i][j] = C[i-1][j-1] + C[i-1][j]`, which needs no inverses at all.

### 8.4 Primes: the sieve, a smallest-prime-factor table, Miller–Rabin

| Method | Cost | Use when |
|---|---|---|
| Trial division, `i*i <= n` | O(√n) per number | a few checks |
| **Sieve of Eratosthenes** | O(n log log n) once | *every* prime below `n` |
| **Smallest-prime-factor (SPF) table** | O(n log log n) once, O(log x) per factorisation | many factorisation queries |
| Miller–Rabin | O(k · log² n) multiplies, each a `mulMod` | one number up to 64 bits |

```go
func countPrimes(n int) int {          // primes strictly less than n
    if n < 3 { return 0 }
    comp := make([]bool, n)            // comp[i] reports "i is composite"
    for i := 2; i*i < n; i++ {
        if !comp[i] {
            for j := i * i; j < n; j += i { comp[j] = true } // smaller multiples were already crossed off
        }
    }
    c := 0
    for i := 2; i < n; i++ { if !comp[i] { c++ } }
    return c
}

func spfTable(n int) []int32 {
    spf := make([]int32, n+1)
    for i := 2; i <= n; i++ {
        if spf[i] == 0 {               // i is prime
            for j := i; j <= n; j += i { if spf[j] == 0 { spf[j] = int32(i) } }
        }
    }
    return spf
}

func factorize(x int, spf []int32) (out []int) {
    for x > 1 { p := int(spf[x]); out = append(out, p); x /= p }
    return
}
// countPrimes(10) = 4   countPrimes(100000) = 9592   countPrimes(1_000_000) = 78498
// factorize(84) = [2 2 3 7]     factorize(97) = [97]
```

Measured (best of nine, counting primes below `n`): at `n = 10⁵` the sieve took **0.18 ms** and trial division **2.2 ms**;
at `n = 10⁶` the sieve took **1.8 ms** against **33 ms**; the sieve found the 664,579 primes below `10⁷` in **10.6 ms**. A
`[]bool` costs one byte per entry (10 MB at `10⁷`); pack it into a `[]uint64` bitset if memory matters.

```go
func isPrime64(n uint64) bool { // deterministic for every uint64
    if n < 2 { return false }
    bases := []uint64{2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37}
    for _, p := range bases { if n%p == 0 { return n == p } }
    d, s := n-1, 0
    for d%2 == 0 { d /= 2; s++ }                 // n-1 = d·2^s with d odd
    for _, a := range bases {
        x := powMod64(a, d, n)
        if x == 1 || x == n-1 { continue }
        composite := true
        for i := 1; i < s; i++ {
            if x = mulMod(x, x, n); x == n-1 { composite = false; break }
        }
        if composite { return false }
    }
    return true
}
```

With those twelve bases the test is exact for every `n < 3.3·10²⁴`, so for all of `uint64`. Checked: `2⁶¹−1` is prime, `2⁶¹+1`
is not, the Carmichael number `561` is not, there are 168 primes below 1000, and `18446744073709551557` (the largest prime
below 2⁶⁴) is prime while `…556` is not. Against `big.Int.ProbablyPrime(20)` it agreed on **20,000 random odd `uint64`
values with zero mismatches**. In the standard library, `ProbablyPrime` is documented as 100 % accurate below 2⁶⁴, so it is a
handy oracle when you test your own.

### 8.5 The exact integer square root — and why `math.Sqrt` is not one

`math.Sqrt` takes and returns `float64`, which has 53 mantissa bits. The conversion is exact for a long time and then
silently isn't. Measured on Go 1.24: for the worst cases `k²` and `k²−1`, `int(math.Sqrt(float64(n)))` is right for every
`k ≤ 2²⁶`, so — because the square root is monotonic — for **every `n ≤ 2⁵² ≈ 4.5·10¹⁵`**. The first failure is
`n = 4,503,599,761,588,224` (`= (2²⁶+1)² − 1`): the float result rounds up to `67108865`, but the floor is `67108864`. At
`n = 10¹⁸ − 1` it returns `1000000000` where the answer is `999999999`. So correct the estimate with integer arithmetic:

```go
func isqrt(n uint64) uint64 {
    r := uint64(math.Sqrt(float64(n)))
    if r > math.MaxUint32 { r = math.MaxUint32 } // (r+1)² must not overflow uint64
    for r*r > n { r-- }
    for r < math.MaxUint32 && (r+1)*(r+1) <= n { r++ }
    return r
}
// isqrt(1e18-1) = 999999999   isqrt(1<<63) = 3037000499   isqrt(math.MaxUint64) = 4294967295
```

The cap is not decoration. For `n` near `2⁶⁴` the float rounds up to `2³²`, and `2³² · 2³²` wraps to `0` in `uint64`, so an
uncapped "raise `r` while `(r+1)² <= n`" loop never terminates — that is exactly how the first version of this helper hung
on `isqrt(math.MaxUint64)`. For a loop bound, avoid `Sqrt` altogether and write `i*i <= n`.

The same distrust applies to `math.Pow` for integers: `int(math.Pow(3, 33))` is right (`5559060566555523`), but
`int64(math.Pow(3, 34))` gives `16677181699666568` where the true value is `16677181699666569` — `3³⁴` exceeds `2⁵³`. Use an
integer loop (or `powMod`) for integer powers.

### 8.6 Geometry with integers: the cross product and what it costs in `int64`

```go
type P struct{ x, y int64 }

func cross(o, a, b P) int64 { return (a.x-o.x)*(b.y-o.y) - (a.y-o.y)*(b.x-o.x) }
// cross((0,0),(4,0),(4,3)) = 12 (left turn)   (4,-3) → -12 (right turn)   (2,2),(4,4) → 0 (collinear)
```

**Overflow bound.** With `|coordinate| ≤ C`, each difference is at most `2C`, each product at most `4C²`, and the cross
product at most `8C²`. That fits `int64` while `C` stays near `10⁹`: the corners `±10⁹` give exactly `4·10¹⁸`, but with
`±3·10⁹` the same expression wraps to `-893488147419103232` (true value `3.6·10¹⁹`). LeetCode constraints are far smaller;
past `10⁹`, use `math/big` or compare 128-bit products with `bits.Mul64`.

```go
func sgn(v int64) int { if v > 0 { return 1 }; if v < 0 { return -1 }; return 0 }

func onSeg(a, b, p P) bool { // p is already known collinear with a–b
    return min(a.x, b.x) <= p.x && p.x <= max(a.x, b.x) && min(a.y, b.y) <= p.y && p.y <= max(a.y, b.y)
}

func segInter(a, b, c, d P) bool {
    d1, d2 := sgn(cross(a, b, c)), sgn(cross(a, b, d))
    d3, d4 := sgn(cross(c, d, a)), sgn(cross(c, d, b))
    if d1*d2 < 0 && d3*d4 < 0 { return true }           // a proper crossing
    return (d1 == 0 && onSeg(a, b, c)) || (d2 == 0 && onSeg(a, b, d)) ||
           (d3 == 0 && onSeg(c, d, a)) || (d4 == 0 && onSeg(c, d, b)) // touching / collinear cases
}

func area2(poly []P) int64 { // TWICE the area — keeps it an exact integer
    var s int64
    for i := range poly {
        j := (i + 1) % len(poly)
        s += poly[i].x*poly[j].y - poly[j].x*poly[i].y
    }
    if s < 0 { s = -s }
    return s
}
```

Results, all run: the crossing pair `(0,0)-(4,4)` / `(0,4)-(4,0)` is `true`; the collinear-but-disjoint `(0,0)-(1,1)` /
`(2,2)-(3,3)` is `false`; the collinear-and-overlapping `(0,0)-(2,2)` / `(1,1)-(3,3)` is `true`; the T-junction
`(0,0)-(2,0)` / `(1,0)-(1,5)` is `true`. `area2` gives `24` for the 4×3 rectangle and `12` for the right triangle with legs
4 and 3 — halve it only at the very end, since the area of a lattice polygon is a multiple of ½.

```go
func hull(pts []P) []P { // Andrew's monotone chain, O(n log n); drops collinear points
    pts = slices.Clone(pts)
    slices.SortFunc(pts, func(a, b P) int { return cmp.Or(cmp.Compare(a.x, b.x), cmp.Compare(a.y, b.y)) })
    pts = slices.CompactFunc(pts, func(a, b P) bool { return a == b })
    if len(pts) < 3 { return pts }
    build := func(seq []P) []P {
        h := make([]P, 0, len(seq))
        for _, p := range seq {
            for len(h) >= 2 && cross(h[len(h)-2], h[len(h)-1], p) <= 0 { h = h[:len(h)-1] }
            h = append(h, p)
        }
        return h
    }
    lower := build(pts)
    slices.Reverse(pts)
    upper := build(pts)
    return append(lower[:len(lower)-1], upper[:len(upper)-1]...)
}
// hull({1,1},{2,2},{2,0},{2,4},{3,3},{4,2}) = [{1 1} {2 0} {4 2} {2 4}]   ((2,2) is interior; (3,3) lies on an edge)
```

`cmp.Or` needs Go 1.22, `slices` and `cmp` Go 1.21. A `struct` or `[2]int` of integers is a valid **map key** in Go; a
`float64` key is the trap. Problem 010's float slope fails for a concrete reason, reproducible in Go:
`165580141.0/102334155.0 == 267914296.0/165580141.0` is `true` (both `1.618033988749895`), yet the cross-multiplied integers
differ — `165580141² − 102334155·267914296 = 1` — so the two slopes are different. A `[2]int` key (`dx`, `dy` divided by the
absolute gcd, with `dx ≥ 0` and `dy ≥ 0` when `dx == 0`) never has this problem; `(1,2)`, `(-1,-2)` and `(2,4)` all reduce
to `[1 2]`, `(0,-5)` to `[0 1]`, `(-3,6)` to `[1 -2]`.

### 8.7 Go-specific hazards in the ten problems

| # | Hazard | Go answer |
|---|---|---|
| 001 | Reversing the *whole* number wraps in `int32`: `1534236469` reverses to `9646324351`, which `int32` turns into `1056389759` (measured); `int64` happens to hold it | Half-reverse until `x <= rev`; compare `x == rev \|\| x == rev/10` |
| 002 | Prepending a digit to a slice | `append([]int{1}, d...)` — O(n), fine once |
| 004 | The exponent is an `int32`: `n = -n` leaves `math.MinInt32` negative, the loop never runs, and `myPow(2, math.MinInt32)` returns `1` instead of `0` (measured) | Widen first: `e := int64(n); if e < 0 { x, e = 1/x, -e }` |
| 005 | Digits are bytes | `int(a[i]-'0')`; build the answer in a `strings.Builder` and skip only the leading zero |
| 006 | Iterating a `map[int]string` of numerals visits keys in a *random* order — a 13-key map gave 13 distinct orders over 200 loops (measured) | A **slice** of `struct{v int; s string}` in descending order |
| 007 | `21!` overflows `int64` | `for n > 0 { n /= 5; c += n }` |
| 008 | `[]int` sieve wastes 8× memory | `[]bool` (1 byte) or a `[]uint64` bitset |
| 009 | Reading a missing key of a nested map is safe (`d.cols[x][y]` is `0`), but *writing* through a `nil` inner map panics with `assignment to entry in nil map` (measured) | Create the inner map on first `Add`; index by column so `Count` scans one column |
| 010 | Negative gcd from `%`; `float64` keys | `abs(gcd)`, `[2]int` key |

### 8.8 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Return it modulo `10⁹ + 7`." | Reduce after every multiply; divide by multiplying with `powMod(x, MOD-2, MOD)`. |
| "The modulus is near `2⁶⁴`." | `bits.Mul64` + `bits.Div64` (reduce `hi` first), or `math/big`. |
| "Many queries on one range." | One sieve or SPF table; factorial and inverse-factorial tables for `nCr`. |
| "Is this one large number prime?" | Miller–Rabin with the twelve fixed bases — exact for all `uint64`. |
| "No floating point." | Cross products, gcd-reduced `[2]int` keys, `isqrt` with an `r*r` correction. |
| "Coordinates up to `10⁹`?" | The cross product needs up to `8·10¹⁸` — inside `int64`, but only just; beyond that, go 128-bit. |
| "Why is the sieve O(n log log n)?" | Each prime `p` crosses off `n/p` entries; `Σ n/p` over primes below `n` is `n log log n`. |

---
<!-- /block:21_go_1_toolkit -->

<!-- problem-map:start -->
## Part 9 · Every Problem in This Topic, by Pattern

Ten problems, five moves (digit arithmetic · cycle detection over a numeric sequence · exponentiation by squaring · counting factors · exact keys instead of floats) — the Python guide's map in Go, where fixed-width integers add an overflow question to every step. Each **Trap** is a mistake documented in that problem's solution file, plus Go-specific hazards. Topic 21's Go solutions are still placeholders; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Palindrome Number](GoDSA/21_math_geometry/001_palindrome_number/solution.go) <br>LC 9 · Easy | Reverse half, then compare | Reject negatives and positives ending in `0`; peel digits into `rev` until `x <= rev`, then `x == rev \|\| x == rev/10`. **Trap:** converting to a string; reversing the *whole* number (wraps in `int32`: `1534236469`); forgetting the odd-length `/10`. |
| [002 · Plus One](GoDSA/21_math_geometry/002_plus_one/solution.go) <br>LC 66 · Easy | Carry, right to left | Walk from the last digit; a digit `< 9` increments and returns, otherwise it becomes `0`. All 9s: `append([]int{1}, d...)`. **Trap:** no post-loop carry branch (`[9,9,9] → [0,0,0]`); appending the 1 at the wrong end; converting to an integer. |
| [003 · Happy Number](GoDSA/21_math_geometry/003_happy_number/solution.go) <br>LC 202 · Easy | Cycle detection on a number sequence | `slow, fast = next(slow), next(next(fast))` until `fast == 1` or they meet — topic 08's Floyd over `f(n)`. **Trap:** no cycle detection (infinite loop); comparing `slow == fast` before advancing either pointer. |
| [004 · Pow(x, n)](GoDSA/21_math_geometry/004_powx_n/solution.go) <br>LC 50 · Medium | Exponentiation by squaring | Widen `n` to `int64`, invert `x` for negative `n`, then square `x` and halve `e`, multiplying into the result on odd bits. **Trap:** `-n` on an `int32` `math.MinInt32` (stays negative → returns `1`); recursing on a negative `n`; the odd-case off-by-one. |
| [005 · Multiply Strings](GoDSA/21_math_geometry/005_multiply_strings/solution.go) <br>LC 43 · Medium | Grade-school multiplication | Digit `i` times digit `j` lands at `i+j+1` (units) and `i+j` (carry) in an `[]int` of `m+n`; skip only the leading zero. **Trap:** `int(a) * int(b)` (bans the point); mapping both digits to `i+j`; not special-casing `"0"`. |
| [006 · Integer to Roman](GoDSA/21_math_geometry/006_integer_to_roman/solution.go) <br>LC 12 · Medium | A flat greedy table | A **slice** of `struct{v int; s string}` in descending order, including the six subtractive forms, drained with a `strings.Builder`. **Trap:** a `map[int]string` (random iteration order); omitting a subtractive entry (`1940` → `MCMXXXX`). |
| [007 · Factorial Trailing Zeroes](GoDSA/21_math_geometry/007_factorial_trailing_zeroes/solution.go) <br>LC 172 · Medium | Count the factor 5 | `for n > 0 { n /= 5; c += n }` — never compute `n!`. **Trap:** `n / 5` alone (undercounts multiples of 25); counting factors of 2; building the factorial (`21!` overflows `int64`). |
| [008 · Count Primes](GoDSA/21_math_geometry/008_count_primes/solution.go) <br>LC 204 · Medium | Sieve of Eratosthenes | `[]bool` of length `n`; for `i*i < n`, cross off from `i*i` in steps of `i`. **Trap:** starting at `2*i` (correct but slower); an off-by-one on "strictly less than `n`"; a `[]int` sieve (8× the memory). |
| [009 · Detect Squares](GoDSA/21_math_geometry/009_detect_squares/solution.go) <br>LC 2013 · Medium | Hash the points, scan one column | Index counts as `map[int]map[int]int` (column → y → count); for each `y != py` the side is `\|y − py\|`, and the other two corners come from columns `px ± side`. **Trap:** scanning *all* points; not skipping `y == py`; writing into a `nil` inner map. |
| [010 · Max Points on a Line](GoDSA/21_math_geometry/010_max_points_on_a_line/solution.go) <br>LC 149 · Hard | A gcd-reduced integer slope key | `[2]int{dx, dy}` divided by `abs(gcd)`, sign-fixed so `dx >= 0` (and `dy >= 0` if `dx == 0`); count the maximum per anchor. **Trap:** a `float64` key (`165580141/102334155` and `267914296/165580141` collide); a negative gcd from `%`; reducing without a sign convention. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Explain why Go's `int` wraps instead of raising an overflow error
- [ ] Know that Go's `%` keeps the dividend's sign, and write `((x%m)+m)%m` from memory
- [ ] Hand-roll GCD and LCM without hesitating — Go's stdlib doesn't have them
- [ ] Hand-roll modular exponentiation via square-and-multiply, O(log exp)
- [ ] Know why `int(math.Sqrt(float64(n)))` can be off by one near perfect squares, and how to correct it
- [ ] Use `i*i <= n` instead of `math.Sqrt` for integer bounds when exactness matters
- [ ] Compare floats with an epsilon, never `==`
- [ ] Compute a 2D cross product and read its sign as a turn direction
- [ ] Rotate a matrix in place via transpose + row-reverse, and trace the spiral-walk boundary updates without an off-by-one
- [ ] State the overflow ladder: `int64` while operands are below `m ≤ 3,037,000,500`, then `bits.Mul64`/`bits.Div64`, then `math/big` <!--ca-->
- [ ] Write `extGCD` and `modInv`, normalise negative inputs, and nil-check `big.Int.ModInverse` <!--ca-->
- [ ] Build `nCr mod p` with one `powMod` for all inverse factorials <!--ca-->
- [ ] Write the sieve (`i*i < n`, inner loop from `i*i`) and quote the measured gap to trial division <!--ca-->
- [ ] Write an `isqrt` that corrects `math.Sqrt` with `r*r`, and explain the `MaxUint32` cap <!--ca-->
- [ ] Know the cross-product overflow bound (`8C²`) and write segment intersection with the collinear cases <!--ca-->
- [ ] Key slopes on a gcd-reduced `[2]int` with an absolute gcd — never a `float64` <!--ca-->
