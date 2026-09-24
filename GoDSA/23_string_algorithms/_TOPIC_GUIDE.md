# Topic 23 · String Algorithms — Go Deep Dive

> Topic 01 established that a Go `string` is an immutable byte slice, not a
> character array. Every algorithm in this document lives on top of that fact.
> Pattern matching over bytes is fast and predictable; pattern matching over
> "characters" requires deciding, on every problem, whether you actually mean
> bytes or runes. This is the document that turns that foundation into real
> substring-search and hashing algorithms — the ones interviewers actually ask
> you to derive on a whiteboard.

---

## Part 0 · Recap: Bytes, Runes, Builders

From topic 01: a Go `string` is a read-only `[]byte` header. `len(s)` counts
**bytes**, not characters — `len("héllo")` is 6, not 5, because `é` is 2 bytes
in UTF-8. Indexing `s[i]` yields a `byte`, not a rune. `for i, r := range s`
decodes UTF-8 on the fly and gives you `rune`s, with `i` jumping by more than 1
across multi-byte characters. `[]rune(s)` is an O(n) decode you pay once when a
problem is genuinely Unicode-sensitive; otherwise treat ASCII input as bytes
and skip the conversion. `strings.Builder` is the O(n) way to build a string in
a loop — `s += x` is O(n²) because each concatenation allocates and copies the
whole accumulated string (measured: 20,000 appends took 12 ms, 100,000 took 284 ms — five times the input, twenty-three
times the time; the `Builder` did 100,000 in 0.06 ms). That's the foundation. Everything below assumes it.

---

## Part 1 · Naive Substring Search — the O(n·m) Baseline

Before KMP or Rabin-Karp, know what they're improving on:

```go
func naiveSearch(text, pattern string) int {
    n, m := len(text), len(pattern)
    for i := 0; i+m <= n; i++ {
        j := 0
        for j < m && text[i+j] == pattern[j] {
            j++
        }
        if j == m {
            return i          // match starting at i
        }
    }
    return -1
}
```

Worst case is O(n·m): a text like `"aaaaaaaaab"` against pattern `"aaab"`
re-scans nearly the whole pattern at almost every starting position. The two
algorithms below both exist to eliminate that redundant re-scanning, using two
different tricks — precomputed pattern structure (KMP) vs. incremental hashing
(Rabin-Karp).

---

## Part 2 · KMP (Knuth-Morris-Pratt) — the Interview Classic

KMP's insight: when a match attempt fails at pattern position `j`, you already
know the last `j` characters of `text` matched `pattern[0:j]`. If the pattern
has internal repeated structure, you don't need to restart the comparison from
`pattern[0]` — you can jump ahead using information baked into the pattern
itself. That precomputed jump table is the **LPS array** (Longest proper
Prefix which is also a Suffix).

### 2.1 Building the LPS array

`lps[i]` = the length of the longest proper prefix of `pattern[0:i+1]` that is
also a suffix of it. "Proper" means the whole string doesn't count as its own
prefix/suffix.

```go
func buildLPS(pattern string) []int {
    m := len(pattern)
    lps := make([]int, m)     // lps[0] is always 0
    length := 0               // length of the current matched prefix-suffix
    i := 1
    for i < m {
        if pattern[i] == pattern[length] {
            length++
            lps[i] = length
            i++
        } else if length != 0 {
            length = lps[length-1]   // fall back — do NOT increment i here
        } else {
            lps[i] = 0
            i++
        }
    }
    return lps
}
```

Trace for `pattern = "ababaca"`:

```
index:    0  1  2  3  4  5  6
char:     a  b  a  b  a  c  a
lps:      0  0  1  2  3  0  1

i=1: 'b' vs pattern[0]='a'      → mismatch, length==0 → lps[1]=0
i=2: 'a' vs pattern[0]='a'      → match, length=1     → lps[2]=1
i=3: 'b' vs pattern[1]='b'      → match, length=2     → lps[3]=2
i=4: 'a' vs pattern[2]='a'      → match, length=3     → lps[4]=3
i=5: 'c' vs pattern[3]='b'      → mismatch, length=3≠0 → length=lps[2]=1
     'c' vs pattern[1]='b'      → mismatch, length=1≠0 → length=lps[0]=0
     'c' vs pattern[0]='a'      → mismatch, length==0  → lps[5]=0
i=6: 'a' vs pattern[0]='a'      → match, length=1     → lps[6]=1
```

> ⚠️ The trap everyone hits: on a mismatch with `length != 0`, you fall back to
> `length = lps[length-1]` and **retry the same `i`** — you do not advance `i`.
> Advancing `i` on that branch silently produces a wrong LPS array that still
> "looks plausible," and the bug only surfaces on adversarial patterns.

### 2.2 The search scan

```go
func kmpSearch(text, pattern string) int {
    if len(pattern) == 0 {
        return 0
    }
    lps := buildLPS(pattern)
    i, j := 0, 0                 // i walks text, j walks pattern
    for i < len(text) {
        if text[i] == pattern[j] {
            i++
            j++
            if j == len(pattern) {
                return i - j      // full match found
            }
        } else if j != 0 {
            j = lps[j-1]          // reuse the matched prefix — i does NOT reset
        } else {
            i++
        }
    }
    return -1
}
```

The reason this is O(n+m): `i` **never decreases**. Every character of `text`
is examined a bounded number of times because `j`'s fallbacks are paid for by
the LPS array, which itself cost O(m) to build once. Total: O(n+m), a genuine
improvement over naive's O(n·m).

---

## Part 3 · Rabin-Karp — Rolling Hash Search

Rabin-Karp's insight: instead of comparing characters, compare a **hash** of
each window. If you can update that hash in O(1) as the window slides, you get
O(n+m) average time using nothing but arithmetic.

```go
const (
    base = 256          // treat each byte as a digit in base-256
    mod  = 1_000_000_007 // large prime — keeps hashes bounded, avoids overflow
)

func rabinKarpSearch(text, pattern string) int {
    n, m := len(text), len(pattern)
    if m > n {
        return -1
    }

    var patternHash, windowHash, pow int64 = 0, 0, 1
    for i := 0; i < m-1; i++ {
        pow = (pow * base) % mod       // pow = base^(m-1) mod p, for peeling off the leading digit
    }
    for i := 0; i < m; i++ {
        patternHash = (patternHash*base + int64(pattern[i])) % mod
        windowHash = (windowHash*base + int64(text[i])) % mod
    }

    for i := 0; ; i++ {
        if windowHash == patternHash && text[i:i+m] == pattern {
            return i    // hash match verified with a real comparison
        }
        if i+m == n {
            break
        }
        // slide the window: drop text[i], bring in text[i+m]
        windowHash = (windowHash - int64(text[i])*pow%mod + mod) % mod
        windowHash = (windowHash*base + int64(text[i+m])) % mod
    }
    return -1
}
```

> ⚠️ **The subtraction can go negative in Go.** `windowHash - int64(text[i])*pow%mod`
> can be negative before the final `% mod`, and Go's `%` keeps the sign of the
> **dividend** (unlike Python, where `%` is always non-negative for a positive
> divisor) — see topic 21's modular-arithmetic notes for the general rule. The
> fix is the `+ mod) % mod` normalization shown above: adding `mod` before the
> final modulo guarantees a non-negative result regardless of Go's sign
> convention. Skipping this is the single most common Rabin-Karp bug in Go.

> ⚠️ **A hash match is not proof of a match.** Two different windows can
> collide on the hash (a false positive) — always verify with `text[i:i+m] ==
> pattern` before declaring a match. This is what makes Rabin-Karp's worst case
> O(n·m) (adversarial input causing many collisions) despite averaging O(n+m).

Rabin-Karp generalizes better than KMP to problems needing **many** pattern
hashes at once (e.g. finding duplicate substrings of a fixed length across an
entire text) — that's its real interview niche, not "faster than KMP."

---

## Part 4 · `strings.Builder`, Properly

Topic 01 introduced `strings.Builder` as the fix for O(n²) concatenation. Two
details worth knowing at this depth:

```go
var sb strings.Builder
sb.Grow(n)                  // preallocate — avoids repeated reallocation, same
                             // amortized-growth argument as topic 01's append
sb.WriteByte('a')           // single byte
sb.WriteRune('é')           // UTF-8-encodes a rune, may write >1 byte
sb.WriteString("hello")     // append a string
result := sb.String()       // O(1) — see below
```

`Grow(n)` reserves capacity the same way `make([]byte, 0, n)` would for a
slice — it does not change length, only avoids reallocation as you write.

> ⚡ **Why `String()` is O(1).** `strings.Builder` accumulates into an internal `[]byte`, and `String()` does not copy it — it
> reinterprets the buffer as a string with `unsafe.String(unsafe.SliceData(b.buf), len(b.buf))`. That is safe because the
> Builder only ever **appends**: bytes already written are never modified (a later write either lands past the string's end or
> reallocates the buffer), so a string you obtained earlier cannot change under you. What the type does guard against is being
> **copied**: a `Builder` remembers its own address (`addr`) and every write calls `copyCheck`, so writing to a copy of a non-zero
> `Builder` **panics at run time** — measured: `strings: illegal use of non-zero Builder copied by value`. It is a runtime
> check, not a `go vet` one (`Builder` carries no `noCopy` marker). Pass a `*strings.Builder`, never a value, once it has been written to.

---

## Part 5 · Frequency-Array Patterns (Anagrams, Permutation-in-String)

These reuse two ideas already covered elsewhere rather than introducing new
ones: topic 01's `[26]int` ASCII frequency array, and topic 03's sliding
window. For "permutation in string" / "find all anagrams," maintain a
fixed-size window and compare frequency arrays (or a single running "matches"
counter) as the window slides — O(1) work per shift, O(n) total, instead of
re-sorting or rebuilding a map on every window position.

```go
func findAnagrams(s, p string) []int {
    if len(s) < len(p) {
        return nil
    }
    var need, window [26]int
    for i := 0; i < len(p); i++ {
        need[p[i]-'a']++
        window[s[i]-'a']++
    }

    var result []int
    if need == window {
        result = append(result, 0)
    }
    for i := len(p); i < len(s); i++ {
        window[s[i]-'a']++
        window[s[i-len(p)]-'a']--
        if need == window {              // array comparison — [26]int is comparable
            result = append(result, i-len(p)+1)
        }
    }
    return result
}
```

> ✅ `[26]int` arrays are directly comparable with `==` in Go (arrays are value
> types, per topic 01 Part 1.1) — `need == window` compares all 26 counts in
> one expression, no manual loop needed. This only works because they're
> **arrays**, not slices; slices are never comparable with `==` except to `nil`.

---

## Part 6 · Palindromes: Expand-Around-Center vs. Manacher's

**Expand-around-center** (longest palindromic substring): for each of the
`2n-1` possible centers (n single-character centers, n-1 between-character
centers for even-length palindromes), expand outward while characters match.

```go
func longestPalindrome(s string) string {
    start, maxLen := 0, 0
    expand := func(l, r int) {
        for l >= 0 && r < len(s) && s[l] == s[r] {
            l--
            r++
        }
        if r-l-1 > maxLen {
            start, maxLen = l+1, r-l-1
        }
    }
    for i := 0; i < len(s); i++ {
        expand(i, i)      // odd-length palindromes, center on i
        expand(i, i+1)    // even-length palindromes, center between i and i+1
    }
    return s[start : start+maxLen]
}
```

O(n²) time, O(1) extra space — good enough for essentially all interview-sized
inputs. **Manacher's algorithm** finds the same answer in O(n) by reusing
previously-computed palindrome radii (via a mirror-index trick, analogous in
spirit to KMP's LPS reuse) to skip redundant expansions — worth knowing exists
and being able to sketch the idea (transform the string with separators to
unify odd/even cases, track a rightmost-palindrome boundary and its center,
mirror known radii into the unexplored region before expanding) but rarely
required to implement fully in an interview.

> ⚠️ **Byte-vs-rune correctness for palindromes.** `expand` above compares
> `s[l] == s[r]` as bytes — correct for ASCII, but wrong for multi-byte UTF-8
> input, since a byte-level mirror can split a multi-byte rune in half. For
> Unicode-correct palindrome checks, convert to `[]rune` first and index that
> instead (topic 01, Part 2.6) — the O(n²) or O(n) complexity is unchanged,
> only the element type is.

---

## Part 7 · Complexity Table

| Algorithm | Time | Space | Note |
|---|:--:|:--:|---|
| Naive substring search | O(n·m) worst | O(1) | Fine for small inputs |
| KMP | **O(n+m)** | O(m) | LPS array; worst case matches average |
| Rabin-Karp | O(n+m) average, O(n·m) worst | O(1) | Worst case only under many hash collisions |
| Expand-around-center | O(n²) | O(1) | Longest palindromic substring |
| Manacher's algorithm | **O(n)** | O(n) | Same problem, linear time |
| `strings.Builder` append | O(1) amortized per write | O(n) buffer | `Grow(n)` avoids reallocation |
| `[26]int` window comparison | O(1) per shift | O(1) | Anagram/permutation-in-string |

---

## Part 8 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Substring search | `str.find` — a skip-based scan, and the linear-time Two-Way algorithm for long needles (3.10+) | `strings.Index` — `IndexByte` jumps on the first byte, SIMD brute force for short needles, and a switch to **Rabin–Karp** after too many false starts (Part 11.5) |
| String building in a loop | `''.join(parts)` — O(n), idiomatic | `strings.Builder` — O(n), must `Grow` explicitly to preallocate |
| Fast string-copy return | Strings are already immutable/shared | `Builder.String()` avoids a copy via `unsafe` + a vet-enforced no-copy contract |
| Modulo in rolling hash | `%` always non-negative for positive modulus | `%` keeps sign of dividend — must `+mod) % mod` |
| Comparing two frequency windows | `Counter(a) == Counter(b)`, or `==` on two lists (both compare by value; lists are just not hashable) | Fixed-size arrays are `==`-comparable (`[26]int`); slices are not |
| String indexing | Characters (code points) | **Bytes** — must `[]rune` for Unicode correctness |
| Built-in polynomial hashing | No stdlib rolling-hash primitive either | No stdlib rolling-hash primitive — hand-roll in both languages |

---

## Part 9 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| Naive substring search | O(n·m) | O(1) | Baseline / LC 28 brute force |
| KMP (LPS + scan) | O(n+m) | O(m) | LC 28, LC 459 Repeated Substring Pattern |
| Rabin-Karp rolling hash | O(n+m) avg | O(1) | LC 187 Repeated DNA Sequences, duplicate-substring search |
| Sliding frequency array | O(n) | O(1) | LC 438 Find All Anagrams, LC 567 Permutation in String |
| Expand-around-center | O(n²) | O(1) | LC 5 Longest Palindromic Substring |
| Manacher's algorithm | O(n) | O(n) | LC 5, optimal version |
| `strings.Builder` construction | O(n) | O(n) | Any string-building loop |

---

## Part 10 · Building KMP From Scratch (LC 28 / LC 459)

```go
package main

// strStr implements LC 28: return the index of the first occurrence of
// needle in haystack, or -1 if it does not occur.
func strStr(haystack, needle string) int {
    if len(needle) == 0 {
        return 0
    }
    lps := buildLPS(needle)
    i, j := 0, 0
    for i < len(haystack) {
        if haystack[i] == needle[j] {
            i++
            j++
            if j == len(needle) {
                return i - j
            }
        } else if j != 0 {
            j = lps[j-1]
        } else {
            i++
        }
    }
    return -1
}

func buildLPS(pattern string) []int {
    m := len(pattern)
    lps := make([]int, m)
    length := 0
    i := 1
    for i < m {
        if pattern[i] == pattern[length] {
            length++
            lps[i] = length
            i++
        } else if length != 0 {
            length = lps[length-1]   // fall back without advancing i
        } else {
            lps[i] = 0
            i++
        }
    }
    return lps
}

// repeatedSubstringPattern implements LC 459: does s consist of one
// substring repeated multiple times? Classic LPS-array application: if
// s is built from a repeating unit of length k, then len(s)-lps[n-1] is a
// divisor of len(s) equal to k.
func repeatedSubstringPattern(s string) bool {
    n := len(s)
    lps := buildLPS(s)
    period := n - lps[n-1]
    return period != n && n%period == 0
}
```

**Talk track while writing:** the LPS array answers one question — "if I
mismatch here, how much of my prefix can I reuse instead of restarting from
index 0?" — and both the search scan and the repeated-substring check are
just different consumers of that same array. Build the LPS array once,
correctly, and both problems fall out of it. The `length = lps[length-1]`
fallback line is the one line worth rehearsing until it's automatic.

---

<!-- block:23_go_1_search -->
## Part 11 · The Search Toolkit in Go — Prefix Function, Z-Function, Find-All, Periods, and What `strings.Index` Really Does

Parts 1–10 give KMP and Rabin–Karp for one search. This Part adds the pieces a complete answer needs — the Z-function, *all*
matches, what the tables say about periods and borders — and checks them against the standard library. All code below was
compiled with `go vet` and compared with brute force on 3,000 random strings over `{a, b, c}`.

```arch
%% caption: Pick the string tool from the question being asked. Go's standard library already covers plain search.
grid 200x85
node q "A string problem in Go" at 0,0 shape=pill w=200
node a "What is being\ncompared?" at 0,2 shape=diamond color=amber
node b "strings.Index / Contains in production" at 1,0 color=green w=380 sub="one pattern inside one text · prefix function or Z-function to write it yourself"
node c "prefix function: n - lps[n-1] is the smallest period" at 1,1 color=green w=380 sub="a string against itself (period, border, repetition)"
node d "rolling hash + binary search on the length" at 1,2 color=amber w=380 sub="many equal-length windows, or a 'longest length such that' question · verify every hash match"
node e "expand around centres O(n^2)" at 1,3 color=green w=380 sub="palindromes · Manacher O(n); prefix function on s + 0x00 + reverse(s)"
node f "trie / Aho-Corasick" at 1,4 color=amber w=380 sub="many patterns at once"
q -> a
a:R -> b:L
a:R -> c:L
a:R -> d:L
a:R -> e:L
a:R -> f:L
```

### 11.1 The prefix function (Part 2's `buildLPS`) and why it is linear

```go
func prefixFunction(s string) []int {
    pi := make([]int, len(s))
    k := 0
    for i := 1; i < len(s); i++ {
        for k > 0 && s[i] != s[k] { k = pi[k-1] } // fall back; i does NOT move
        if s[i] == s[k] { k++ }
        pi[i] = k
    }
    return pi
}
// prefixFunction("ababaca") = [0 0 1 2 3 0 1]
```

There is a `for` inside a `for`, yet the total is O(n): `k` rises by at most one per character and every fallback strictly lowers
it, so fallbacks can never outnumber increments. The same argument covers the search scan, where `i` only ever moves forward.

### 11.2 The Z-function — the same information, read the other way

`z[i]` is the longest common prefix of `s` and `s[i:]`, with `z[0] = len(s)`.

```go
func zFunction(s string) []int {
    n := len(s)
    z := make([]int, n)
    if n == 0 { return z }
    z[0] = n
    l, r := 0, 0 // [l, r) = the rightmost prefix-match window found so far
    for i := 1; i < n; i++ {
        if i < r { z[i] = min(r-i, z[i-l]) } // reuse the mirror position inside the window
        for i+z[i] < n && s[z[i]] == s[i+z[i]] { z[i]++ }
        if i+z[i] > r { l, r = i, i+z[i] }
    }
    return z
}
// zFunction("aabxaab") = [7 1 0 0 3 1 0]
```

`min` is the Go 1.21 built-in. The two tables are interconvertible and both O(n); use the prefix function for "how much of my
prefix can I reuse" (search, periods) and the Z-function for "how far does the prefix match starting here".

### 11.3 Every match — overlapping ones included

```go
func findAllKMP(text, pat string) []int {
    if pat == "" { return nil } // define your own convention; strings.Index(s, "") is 0
    pi, k := prefixFunction(pat), 0
    var out []int
    for i := 0; i < len(text); i++ {
        for k > 0 && text[i] != pat[k] { k = pi[k-1] }
        if text[i] == pat[k] { k++ }
        if k == len(pat) {
            out = append(out, i-k+1)
            k = pi[k-1] // keep going: reuse the border instead of restarting
        }
    }
    return out
}

func findAllZ(text, pat string) []int {
    z := zFunction(pat + "\x00" + text) // a separator byte that occurs in neither string
    var out []int
    for i := len(pat) + 1; i < len(z); i++ {
        if z[i] >= len(pat) { out = append(out, i-len(pat)-1) }
    }
    return out
}
```

`findAllKMP("aaaa", "aa")` is `[0 1 2]` — three overlapping matches — while `strings.Count("aaaa", "aa")` is `2`, because `Count`
counts **non-overlapping** occurrences. The separator `"\x00"` stops a match from straddling the join (the same reason as in Problem 006).

### 11.4 Periods, borders, and the shortest palindrome

- **Smallest period:** `p := n - pi[n-1]`. Problem 002 asks for *whole* repeats, which additionally needs `n%p == 0 && p != n`:

```go
func repeatedSubstringPattern(s string) bool {
    n := len(s)
    p := n - prefixFunction(s)[n-1]
    return p != n && n%p == 0
}
```

  `"abcabcabc"` → true, `"abac"` → false, and `"abcab"` has period 3 but `3` does not divide `5`, so it is *not* a repetition.
- **Borders:** follow `k = pi[k-1]` from `pi[n-1]` to list every border, longest first.
- **Shortest palindrome (Problem 006):**

```go
func shortestPalindrome(s string) string {
    t := s + "\x00" + reverse(s)
    k := prefixFunction(t)[len(t)-1] // length of the longest palindromic PREFIX of s
    return reverse(s[k:]) + s
}

func reverse(s string) string { // bytes: correct for ASCII only
    b := []byte(s)
    slices.Reverse(b)
    return string(b)
}
// shortestPalindrome("aacecaaa") = "aaacecaaa"     shortestPalindrome("abcd") = "dcbabcd"
```

  It matched brute force on 3,000 random strings. In Python the measured cost of *omitting* the separator was a wrong answer for
  203 of 3,000 random strings; the mechanism is identical in Go. `reverse` works on bytes — for non-ASCII text reverse a `[]rune`.

### 11.5 What `strings.Index` actually does — and how the algorithms compare

Reading the Go 1.24 source (`internal/stringslite`): a one-byte needle uses `IndexByte`; a needle no longer than the platform limit
(32 bytes on arm64, 63 or 31 on amd64) jumps between candidate first bytes with `IndexByte` and falls back to a SIMD brute force
(`bytealg.IndexString`) once false positives pile up; and a longer needle does the same first-byte jumping but, after enough
failures, **switches to Rabin–Karp** (`bytealg.IndexRabinKarp`) for the rest of the text. So the library is never quadratic.

Measured, a text of a million `'a'` bytes against an adversarial needle `a…a b a…a` (the last byte matches at every window, the mismatch is in the middle);
best of five, none of them found the needle:

| Needle length `m` | Naive | KMP | Rabin–Karp (mod 10⁹+7) | `strings.Index` |
|---|--:|--:|--:|--:|
| 100 | 18.6 ms | 0.94 ms | 5.8 ms | 1.1 ms |
| 1,000 | 128 ms | 0.89 ms | 5.8 ms | 1.1 ms |
| 10,000 | **1,217 ms** | 1.0 ms | 5.8 ms | 1.1 ms |

The naive scan grows with `m` (it re-reads about `m/2` bytes per window); the three linear methods do not. Rabin–Karp pays a modular
multiplication per byte, hence about 6× KMP; KMP is a tight byte loop; the library sits at KMP speed. In real code call
`strings.Index`, `strings.Contains`, `strings.HasPrefix`; write the algorithm when the *table* is the point or a rule forbids the library.

### 11.6 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Find *all* occurrences, overlapping too." | Keep scanning after a match with `k = pi[k-1]`; `strings.Count` will not do (non-overlapping). |
| "Many patterns against one text." | Aho–Corasick: a trie plus failure links — O(text + total pattern length + matches). |
| "Is `t` a rotation of `s`?" | `len(s) == len(t) && strings.Contains(s+s, t)`. |
| "Same needle, millions of texts." | Build `pi` once and reuse it. |
| "Smallest string to prepend to make a palindrome?" | Prefix function on `s + sep + reverse(s)` (Problem 006). |
| "Longest repeated substring?" | Rolling hash + binary search, or a suffix array with an LCP array (Part 13). |

---
<!-- /block:23_go_1_search -->

<!-- block:23_go_2_hashing -->
## Part 12 · Rolling Hashes in Go — Wrap-Around, `2⁶¹−1` with 128-Bit Products, and the Thue–Morse Attack

Part 3 gives Rabin–Karp with a `10⁹ + 7` modulus. In Go there is a second temptation — let `uint64` overflow do the reduction for
free — and a better tool: a `2⁶¹ − 1` modulus with a 128-bit product from `math/bits`. Everything here was run and checked.

### 12.1 The wrap-around hash is breakable — measured

Multiplying `uint64` values wraps modulo `2⁶⁴` silently, so `h = h*B + c` is a polynomial hash mod `2⁶⁴` with no `%` at all. It is fast,
and it is broken. The **Thue–Morse** strings (`0`, `01`, `0110`, `01101001`, …, each built by appending the complement of the previous
one) and their bitwise complements have the same hash mod `2⁶⁴` for **every odd base**: the difference of the hashes is
`±∏ (B^(2ⁱ) − 1)` over `i < k`, and for odd `B` each factor is divisible by `2^(i+2)` (`2` for `i = 0`), so by `k = 10` the product is divisible by `2⁶⁴`.

```go
hash64 := func(s []byte, B uint64) uint64 {
    var h uint64
    for _, c := range s { h = h*B + uint64(c) + 1 } // natural wrap-around = mod 2^64
    return h
}
```

Measured on the Go code above: the first Thue–Morse collision was at **length 1,024** for bases `131`, `911382323` and `1000003`, and at
**length 512** for a random 63-bit odd base. A hidden test set (or a hostile one) can contain exactly these strings; a randomly drawn
base does not help. Use a large **prime** modulus.

### 12.2 A `2⁶¹ − 1` modulus with `bits.Mul64`

A Mersenne modulus makes reduction cheap: since `2⁶¹ ≡ 1 (mod 2⁶¹−1)`, a 122-bit product folds down with shifts and adds.

```go
const M61 = (1 << 61) - 1

func mulmod61(a, b uint64) uint64 { // a, b < M61
    hi, lo := bits.Mul64(a, b)
    r := (lo & M61) + (lo >> 61) + (hi << 3) // 2^64 = 8 * 2^61, so hi contributes hi*8
    r = (r & M61) + (r >> 61)
    if r >= M61 { r -= M61 }
    return r
}

type Hasher struct{ h, p []uint64 } // h[i] = hash of s[:i], p[i] = B^i

func NewHasher(s string, B uint64) *Hasher {
    n := len(s)
    H := &Hasher{make([]uint64, n+1), make([]uint64, n+1)}
    H.p[0] = 1
    for i := 0; i < n; i++ {
        H.h[i+1] = (mulmod61(H.h[i], B) + uint64(s[i])) % M61
        H.p[i+1] = mulmod61(H.p[i], B)
    }
    return H
}

func (H *Hasher) Sub(l, r int) uint64 { // hash of s[l:r], O(1)
    return (H.h[r] + M61 - mulmod61(H.h[l], H.p[r-l])) % M61
}
```

`mulmod61` agreed with the slow, obviously-correct `bits.Div64(hi, lo, M61)` remainder on 100,000 random operand pairs (the
`hi < M61` precondition of `Div64` holds because the product is below `2¹²²`). Note the `+ M61` before the subtraction: Go's unsigned
subtraction wraps around instead of going negative, so it needs the same fix-up the signed version needs in Part 3. Draw the base at
run time (`rand.Int63n(M61-256) + 256`). This is the general "128-bit product" ladder from topic 21.

Collision odds, by the birthday bound `n²/2m`: for 100,000 windows a 30-bit modulus expects about 5 collisions (measured in the
Python guide: 3), a 61-bit modulus about `2·10⁻⁹`. So **verify every hash match with a real comparison** — that turns the
randomised test into an always-correct one.

### 12.3 Longest Duplicate Substring (Problem 007), complete

```go
func longestDup(s string) string {
    n := len(s)
    if n < 2 { return "" }
    H := NewHasher(s, uint64(rand.Int63n(M61-256))+256)
    dup := func(L int) int { // start of a duplicate of length L, or -1
        seen := make(map[uint64][]int, n)
        for i := 0; i+L <= n; i++ {
            h := H.Sub(i, i+L)
            for _, j := range seen[h] {
                if s[j:j+L] == s[i:i+L] { return i } // VERIFY: a hash match is only a candidate
            }
            seen[h] = append(seen[h], i)
        }
        return -1
    }
    lo, hi, best := 1, n-1, ""
    for lo <= hi { // binary search on the LENGTH: "a duplicate of length L exists" is monotone
        mid := (lo + hi) / 2
        if i := dup(mid); i != -1 {
            best = s[i : i+mid]
            lo = mid + 1
        } else {
            hi = mid - 1
        }
    }
    return best
}
// longestDup("banana") = "ana"     longestDup("abcd") = ""
```

Matched brute force on 3,000 random strings. Why the binary search is valid: if a duplicate of length `L` exists, so does one of every
shorter length (drop the last byte of both copies). Overlapping copies are allowed — `"aa"` inside `"aaa"` counts. The `s[j:j+L]`
comparison is cheap in Go: slicing a string never copies, and `==` stops at the first difference.

### 12.4 Problem 004: when the alphabet is tiny the "hash" is exact

```go
func repeatedDNA(s string) []string {
    const L = 10
    enc := [256]uint32{'A': 0, 'C': 1, 'G': 2, 'T': 3}
    const mask = 1<<(2*L) - 1
    seen, rep := map[uint32]bool{}, map[string]bool{}
    var h uint32
    for i := 0; i < len(s); i++ {
        h = (h<<2 | enc[s[i]]) & mask // shift in 2 bits, mask off the byte that left the window
        if i >= L-1 {
            if seen[h] { rep[s[i-L+1:i+1]] = true }
            seen[h] = true
        }
    }
    out := make([]string, 0, len(rep))
    for k := range rep { out = append(out, k) }
    sort.Strings(out) // map iteration order is random
    return out
}
// repeatedDNA("AAAAACCCCCAAAAACCCCCCAAAAAGGGTTT") = [AAAAACCCCC CCCCCAAAAA]     repeatedDNA("AAAAAAAAAAAAA") = [AAAAAAAAAA]
```

A 10-mer over four letters is a 20-bit integer — a bijection, so a `uint32` suffices, no modulus, no verification. The shift is
`h<<2` on a `uint32` and the mask `1<<20 - 1`; without the mask the old bits pile up above bit 20 and two equal windows stop matching.
The result is sorted only because Go randomises map order — a solution that returns keys in map order is non-deterministic.

---
<!-- /block:23_go_2_hashing -->

<!-- block:23_go_3_palindromes -->
## Part 13 · Palindromes and Suffix Structures in Go — Manacher, Suffix Array with LCP, Palindrome Pairs

Part 6 covers expand-around-center and *names* Manacher's algorithm; here it is written out, along with the suffix-array route to
"longest repeated substring" and Problem 008. All code was compiled with `go vet` and matched brute force on thousands of random strings.

### 13.1 The palindrome toolbox

| Tool | Time | Use it for |
|---|---|---|
| Expand around each of the `2n − 1` centres | O(n²), O(1) space | the interview default (Part 6) |
| **Manacher's algorithm** | **O(n)** | the linear-time follow-up |
| Prefix function on `s + sep + reverse(s)` | O(n) | the longest palindromic **prefix** (Problem 006) |
| Hash of `s[l:r]` against the hash of its reverse | O(1) per query | many queries, or binary search on a radius |
| Map from word to index, plus split points | O(n · L²) | Palindrome Pairs (Problem 008) |

### 13.2 Manacher's algorithm

```go
func manacher(s string) (start, length int) { // bytes: correct for ASCII
    if s == "" { return 0, 0 }
    t := make([]byte, 0, 2*len(s)+3)
    t = append(t, '^')
    for i := 0; i < len(s); i++ { t = append(t, '#', s[i]) }
    t = append(t, '#', '$') // sentinels stop the expansion loop without bounds checks
    p := make([]int, len(t)) // p[i] = radius of the palindrome centred at t[i]
    c, r := 0, 0             // centre and right edge of the rightmost palindrome found so far
    for i := 1; i < len(t)-1; i++ {
        if i < r { p[i] = min(r-i, p[2*c-i]) } // the mirror of i about c, capped by the edge
        for t[i+1+p[i]] == t[i-1-p[i]] { p[i]++ } // grow past what the mirror guarantees
        if i+p[i] > r { c, r = i, i+p[i] }
    }
    centre := 0
    for i, v := range p { if v > p[centre] { centre = i } }
    return (centre - p[centre]) / 2, p[centre]
}
// manacher("babad") = (0, 3) → "bab" (an equally long "aba" is the other valid answer)
```

The interleaved `#` turns odd and even palindromes into the same case; `r` only moves right and the `while` only runs when it is about to push
`r` further, so the total work is O(n). The length always equalled brute force, and the returned slice was a palindrome, on 3,000 random strings.
(`"babad"` has two longest palindromes. This Go version keeps the *first* maximum and returns `"bab"`; the Python guide's `max` over `(radius, index)` keeps
the *last* and returns `"aba"`. Both are correct — compare **lengths** in tests, not substrings.)

### 13.3 Palindrome Pairs (Problem 008)

`words[i] + words[j]` is a palindrome exactly when, splitting one word `left | right`, either (`left` is a palindrome and the other word is
`reverse(right)`, placed *before*) or (`right` is a palindrome and the other word is `reverse(left)`, placed *after*).

```go
func palindromePairs(words []string) [][2]int {
    idx := make(map[string]int, len(words))
    for i, w := range words { idx[w] = i }
    isPal := func(s string) bool {
        for i, j := 0, len(s)-1; i < j; i, j = i+1, j-1 { if s[i] != s[j] { return false } }
        return true
    }
    seen := map[[2]int]bool{}
    var out [][2]int
    add := func(a, b int) {
        if !seen[[2]int{a, b}] { seen[[2]int{a, b}] = true; out = append(out, [2]int{a, b}) }
    }
    for i, w := range words {
        for j := 0; j <= len(w); j++ {
            left, right := w[:j], w[j:]
            if isPal(left) { // reverse(right) goes BEFORE w
                if k, ok := idx[reverse(right)]; ok && k != i { add(k, i) }
            }
            if j != len(w) && isPal(right) { // j != len(w): the empty-right split was already handled above
                if k, ok := idx[reverse(left)]; ok && k != i { add(i, k) }
            }
        }
    }
    return out
}
// ["abcd","dcba","lls","s","sssll"] → [[1 0] [0 1] [3 2] [2 4]] in discovery order (sort it if the caller expects an order)
// ["a",""] → [[0 1] [1 0]]
```

It matched a brute-force `O(n²)` scan on 2,000 random word lists (after sorting both), including the empty string. The guards are the
documented traps: `k != i` (a palindromic word must not pair with itself) and `j != len(w)` (without it, every whole-word reverse pair is
reported twice — the `seen` set here would hide the bug, so test the guard by removing the set). A `[2]int` is a valid map key in Go,
which is why the dedupe set is one line. Slicing `w[:j]` and `w[j:]` copies nothing; `reverse` does allocate.

### 13.4 Suffix array + LCP: repeated substrings without hashing

```go
func suffixArray(s string) []int {
    sa := make([]int, len(s))
    for i := range sa { sa[i] = i }
    slices.SortFunc(sa, func(a, b int) int { return strings.Compare(s[a:], s[b:]) }) // s[a:] shares memory: no copy in Go
    return sa
}

func kasai(s string, sa []int) []int { // lcp[i] = LCP(suffix sa[i-1], suffix sa[i]), O(n)
    n := len(s)
    rank := make([]int, n)
    for i, p := range sa { rank[p] = i }
    lcp, h := make([]int, n), 0
    for i := 0; i < n; i++ {
        if rank[i] > 0 {
            j := sa[rank[i]-1]
            for i+h < n && j+h < n && s[i+h] == s[j+h] { h++ }
            lcp[rank[i]] = h
            if h > 0 { h-- } // moving to the next suffix shortens the LCP by at most 1
        } else { h = 0 }
    }
    return lcp
}

func longestRepeated(s string) string {
    if s == "" { return "" }
    sa := suffixArray(s)
    lcp := kasai(s, sa)
    best := 0
    for i := range lcp { if lcp[i] > lcp[best] { best = i } }
    return s[sa[best] : sa[best]+lcp[best]]
}
// suffixArray("banana") = [5 3 1 0 4 2]   lcp = [0 1 3 0 0 2]   longestRepeated = "ana"
```

No hash means no collisions. Unlike Python, where `s[i:]` copies (so sorting slices costs O(n²) memory), a Go string slice is a two-word
header over the same bytes; the sort's cost is the comparisons, which are bounded by the LCPs — O(n² log n) in the worst case (a string
of one repeated byte), fast for typical input. Prefix doubling gives O(n log² n) and SA-IS O(n). The array also counts distinct substrings:
`n(n+1)/2 − Σ lcp` (for `"banana"`: `21 − 6 = 15`).

| Structure | Build | Answers |
|---|---|---|
| Trie | O(total length) | prefix queries, many-word lookups (topic 13) |
| Aho–Corasick | O(total pattern length) | all occurrences of many patterns in one pass |
| Suffix array + LCP | O(n log n) – O(n) | longest repeated substring, distinct substrings, LCP of any two suffixes |
| Suffix automaton | O(n) | distinct-substring counts, occurrence counts |

---
<!-- /block:23_go_3_palindromes -->

<!-- block:23_go_4_gofacts -->
## Part 14 · Go String Facts That Decide the Answer — Bytes, Runes, `strings`, `Atoi`, and the Last Two Problems

```arch
%% caption: In Go the first question about any string problem is what an "element" is: a byte, a rune, or a user-perceived character.
grid 240x85
node q "A Go string problem" at 0,0 shape=pill
node a "Is the input\nguaranteed ASCII?" at 0,1 shape=diamond color=amber w=250
node b "index s[i] as bytes" at 1,1 color=green w=260 sub="most interview problems · no conversion, O(1) access"
node c "[]rune(s) once, or range over s" at 0,2 color=amber w=240 sub="O(n), copies"
node d "User-perceived\ncharacters?" at 0,3 shape=diamond color=amber w=250 sub="accents, emoji"
node e "Grapheme segmentation\nneeds a library" at 1,3 color=red w=260 sub="neither bytes nor runes are enough"
node f "Work on the []rune" at 0,4 color=green w=240 sub="convert back with string(r)"
q -> a
a -> b : "yes"
a -> c : "no: code points matter"
c -> d
d -> e : "yes"
d -> f : "no"
```

### 14.1 Three different "lengths"

| String | `len(s)` (bytes) | runes | Note |
|---|--:|--:|---|
| `"héllo"` | 6 | 5 | `é` is 2 bytes |
| `"🇮🇳"` | 8 | 2 | two regional-indicator code points |
| `"👨‍👩‍👧"` | 18 | 5 | three emoji joined by zero-width joiners |
| `"éx"` | 4 | 3 | `e` + a combining accent — not the same as `"éx"` |

Consequences, each run: `strings.Index("héllo", "l")` is `3` — a **byte offset**, not the rune index 2. Ranging over an invalid UTF-8 string
(`"a\xffb"`) yields `U+FFFD` for the bad byte, and `utf8.ValidString` is `false`. Reversing `"héllo"` **byte by byte** produces
`"oll\xa9\xc3h"` — invalid UTF-8 — whereas reversing a `[]rune` gives `"olléh"`. Case mapping differs from Python's: `strings.ToUpper("ß")` is
`"ß"` (Python: `"SS"`) and `strings.ToLower("İ")` is one rune, `"i"` (Python: two). `strings.EqualFold` compares with Unicode folding
(`"K"` equals the Kelvin sign U+212A; `"ß"` does not equal `"SS"`). Interview problems almost always promise lowercase ASCII — state that
assumption, then use bytes.

### 14.2 `strings` traps

| Call | Gotcha (all run) |
|---|---|
| `strings.TrimLeft(s, "op")` | strips a **set of characters**: `TrimLeft("oops", "op")` is `"s"`; `TrimPrefix("oops", "oo")` is `"ps"` |
| `strings.Split(" a  b ", " ")` | 5 elements including empty strings; `strings.Fields(" a  b ")` is `[a b]` |
| `strings.Count("aaaa", "aa")` | `2` — non-overlapping |
| `strings.Repeat("a", -1)` | panics: `strings: negative Repeat count` |
| `strings.Cut("key=value=x", "=")` | `("key", "value=x", true)` — splits at the *first* separator (Go 1.18+) |
| `strings.Index` | byte offset; `-1` when absent |

### 14.3 Problem 003 — `atoi`, and how `strconv.Atoi` differs

```go
func myAtoi(s string) int {
    i, n := 0, len(s)
    for i < n && s[i] == ' ' { i++ }                       // 1. leading spaces only
    sign := 1
    if i < n && (s[i] == '+' || s[i] == '-') {             // 2. at most one sign
        if s[i] == '-' { sign = -1 }
        i++
    }
    num := 0
    for i < n && s[i] >= '0' && s[i] <= '9' {              // 3. ASCII digits, then stop at anything else
        d := int(s[i] - '0')
        if num > (math.MaxInt32-d)/10 {                    // 4. clamp BEFORE the multiply overflows a 32-bit int
            if sign == 1 { return math.MaxInt32 }
            return math.MinInt32
        }
        num = num*10 + d
        i++
    }
    return sign * num
}
```

Results, all run: `"42"` → 42, `"   -042"` → -42, `"1337c0d3"` → 1337, `"0-1"` → 0, `"words and 987"` → 0, `"-91283472332"` → -2147483648,
`"91283472332"` → 2147483647, `"+-12"` → 0, `"3.14"` → 3. The check must come *before* the multiply: accumulating in an `int32` without it turns `"2147483648"`
into `-2147483648` silently (measured). Go's `int` is 64-bit, so the clamp is a *choice* you make explicit, not an accident of the type.

`strconv.Atoi` is **not** LeetCode's `atoi`: it rejects a leading space (`" 42"` → error), rejects trailing junk (`"42abc"`), rejects underscores
(`"1_000"`) and non-ASCII digits (`"٣"`), accepts a leading `+`, and on overflow returns the max `int` *and* an error
(`strconv.Atoi: parsing "99999999999999999999": value out of range`). Python's `int()` is more permissive than Go's in the opposite direction
(it accepts spaces, underscores and non-ASCII digits — see the Python guide).

### 14.4 Problem 005 — Repeated String Match

```go
func repeatedStringMatch(a, b string) int {
    q := (len(b) + len(a) - 1) / len(a) // ceiling division
    for k := q; k <= q+1; k++ {
        if strings.Contains(strings.Repeat(a, k), b) { return k }
    }
    return -1
}
// ("abcd", "cdabcdab") = 3    ("a", "aa") = 2    ("abc", "wxyz") = -1
```

Why only `q` and `q+1` are candidates: a match of `b` can start anywhere in the first copy of `a`, so the repeated string never needs more than
`len(a) − 1 + len(b)` characters — at most one copy beyond the ceiling `q`. `("abcd", "cdabcdab")` is the boundary case: `q = 2` fails and `3` succeeds.
Testing only `q` is the classic miss; using floor division under-counts. For inputs where `b` uses a byte that `a` lacks, a set check up front avoids
building a large string (`strings.Repeat` allocates it).

---
<!-- /block:23_go_4_gofacts -->

<!-- problem-map:start -->
## Part 15 · Every Problem in This Topic, by Pattern

Eight problems, five moves (the prefix function reused three ways · exact keys when the alphabet is tiny · arithmetic that bounds a search · binary search on the length with a verified hash · reverse-and-lookup instead of all pairs) — the Python guide's map in Go. Each **Trap** is a mistake documented in that problem's solution file, plus Go-specific hazards. Topic 23's Go solutions are still placeholders; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Find the Index of the First Occurrence in a String](GoDSA/23_string_algorithms/001_find_the_index_of_the_first_occurrence_in_a_string/solution.go) <br>LC 28 · Easy | KMP substring search | `prefixFunction(needle)`; scan with `i` that never moves back, `k = pi[k-1]` on a mismatch; the match starts at `i - k`. **Trap:** moving `i` backwards; advancing `i` in the fallback branch; returning `i` instead of `i - k`; an empty needle indexing `pat[0]`. |
| [002 · Repeated Substring Pattern](GoDSA/23_string_algorithms/002_repeated_substring_pattern/solution.go) <br>LC 459 · Easy | Period from the prefix function | `p := n - pi[n-1]`; a repetition iff `p != n && n%p == 0`. **Trap:** dropping `p != n` (every string then "repeats"); treating `pi[n-1]` itself as the period; in the `(s+s)[1:len(s+s)-1]` trick, trimming only one end. |
| [003 · String to Integer (atoi)](GoDSA/23_string_algorithms/003_string_to_integer_atoi/solution.go) <br>LC 8 · Medium | A four-phase parser | Skip spaces → one optional sign → ASCII digits → clamp *before* multiplying. **Trap:** skipping whitespace after the sign; a second sign or a sign after digits; treating `.` as part of the number; accumulating in `int32` without the check (`"2147483648"` wraps); assuming `strconv.Atoi` behaves the same. |
| [004 · Repeated DNA Sequences](GoDSA/23_string_algorithms/004_repeated_dna_sequences/solution.go) <br>LC 187 · Medium | An exact 2-bit code | `h = (h<<2 \| enc[s[i]]) & mask` in a `uint32`: a perfect 20-bit hash of a 10-mer. Report a window the *second* time it is seen. **Trap:** no mask; reporting on the first sighting; returning `map` keys unsorted (random order); a modular hash that can only add false positives. |
| [005 · Repeated String Match](GoDSA/23_string_algorithms/005_repeated_string_match/solution.go) <br>LC 686 · Medium | Two candidate repeat counts | `q := (len(b)+len(a)-1)/len(a)`; test `strings.Repeat(a, q)` and `q+1` with `strings.Contains`. **Trap:** testing only `q`; floor instead of ceiling; looping over ever more repeats; building a huge repeat for an impossible `b`. |
| [006 · Shortest Palindrome](GoDSA/23_string_algorithms/006_shortest_palindrome/solution.go) <br>LC 214 · Hard | Prefix function on `s + "\x00" + reverse(s)` | `pi[last]` is the longest palindromic *prefix*; the answer is `reverse(s[k:]) + s`. **Trap:** no separator; a separator that occurs in `s`; a palindromic *substring* instead of a *prefix*; mirroring `s[:k]` instead of `s[k:]`; reversing bytes of non-ASCII text. |
| [007 · Longest Duplicate Substring](GoDSA/23_string_algorithms/007_longest_duplicate_substring/solution.go) <br>LC 1044 · Hard | Binary search on length + verified hash | "A duplicate of length `L` exists" is monotone; prefix hashes mod `2⁶¹−1` give `Sub(l, r)` in O(1); compare the real substrings before trusting a match. **Trap:** trusting the hash alone; a `uint64` wrap-around hash (Thue–Morse); recomputing each window from scratch; binary searching on the string; forbidding overlapping copies. |
| [008 · Palindrome Pairs](GoDSA/23_string_algorithms/008_palindrome_pairs/solution.go) <br>LC 336 · Hard | Reverse-and-lookup at every split | For each word and split `left \| right`: `left` palindromic → look up `reverse(right)`; `right` palindromic → look up `reverse(left)`. **Trap:** no `k != i` guard; not excluding `j == len(w)` in the second case (duplicate pairs); testing only whole-word reverses; the O(n²·L) all-pairs scan. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Build the LPS array for a pattern by hand and explain what `lps[i]` means
- [ ] Explain why the LPS fallback does not advance `i`, and why that gives O(n+m)
- [ ] Implement the KMP search scan without looking it up
- [ ] Explain Rabin-Karp's rolling hash update, and why you still verify on hash match
- [ ] Apply the `((x % m) + m) % m` fix to a negative intermediate hash in Go
- [ ] Explain why `strings.Builder.String()` is O(1) and what guarantees make it safe
- [ ] Use a `[26]int` frequency array with `==` comparison for anagram/window problems
- [ ] Implement expand-around-center for longest palindromic substring
- [ ] State Manacher's algorithm's complexity and the mirror-index idea, even if not implementing it
- [ ] Know when byte comparison is wrong for a palindrome/string check and `[]rune` is required
- [ ] Write the prefix function and the Z-function in Go, and explain why each is O(n) despite the nested loop <!--ca-->
- [ ] List every overlapping match with KMP, and explain why `strings.Count` returns fewer <!--ca-->
- [ ] Distinguish "has period `p`" from "is a repetition" (`n%p == 0` and `p != n`) <!--ca-->
- [ ] Explain why a `uint64` wrap-around hash is breakable (Thue–Morse at length 1,024) and use `2⁶¹−1` with `bits.Mul64` instead <!--ca-->
- [ ] Verify every hash match, and say why a 61-bit modulus makes the expected verification cost negligible <!--ca-->
- [ ] Write Manacher's algorithm, Kasai's LCP, and Palindrome Pairs with both guards (`k != i`, `j != len(w)`) <!--ca-->
- [ ] State what `strings.Index` does (first-byte jumps, SIMD brute force, Rabin–Karp fallback) and quote the measured adversarial timings <!--ca-->
- [ ] Know that `strings.Builder` copies panic at run time, and that `s += x` measured 12 ms for 20,000 appends and 284 ms for 100,000 <!--ca-->
- [ ] Reject `strconv.Atoi` as a stand-in for LeetCode's `atoi`, and clamp *before* the multiply <!--ca-->
- [ ] Choose bytes, runes or a grapheme library deliberately, and know that reversing bytes can produce invalid UTF-8 <!--ca-->
