package main

import (
	"fmt"
	"sort"
	"strings"
	"time"
	"unicode/utf8"
)

/*
================================================================================
SOLUTION · LeetCode 242 · Valid Anagram                                  [Easy]
https://leetcode.com/problems/valid-anagram/
================================================================================

THE CORE IDEA
-------------
Anagram == identical character MULTISET. Counts matter, not just membership.
Count both strings, compare the counts. Guard on length first — different
lengths can never be anagrams, and that check is O(1).

In Go this problem is really about one thing: STRINGS ARE BYTES. The ASCII fast
path and the Unicode follow-up are genuinely different programs, and knowing
why is the whole lesson.


================================================================================
⚠️  STRINGS ARE BYTES, NOT CHARACTERS
================================================================================

    s := "héllo"
    len(s)                        // 6  — BYTES. 'é' is 2 bytes in UTF-8.
    utf8.RuneCountInString(s)     // 5  — actual characters
    s[1]                          // 0xC3 — a byte, half of 'é'. Not a character.
    for i, r := range s { }       // r is a rune; i JUMPS 1 -> 3 across 'é'

For the stated constraint (lowercase English) byte length == rune length, so
`len(s)` is correct and `s[i]` is a genuine character. The moment Unicode
enters, both assumptions break.

    "anagram"  ->  len 7, runes 7   ✓ interchangeable
    "école"    ->  len 6, runes 5   ✗ NOT interchangeable


================================================================================
APPROACH 1 · Fixed [26]int array — the fastest ✅✅
================================================================================

    if len(s) != len(t) { return false }
    var counts [26]int
    for i := 0; i < len(s); i++ {
        counts[s[i]-'a']++
        counts[t[i]-'a']--
    }
    for _, c := range counts {
        if c != 0 { return false }
    }
    return true

STEP BY STEP for s = "rat", t = "car":

    lengths 3 == 3  ✓

    i=0:  counts['r'-'a'=17]++  ->  [17]=1
          counts['c'-'a'=2 ]--  ->  [2]=-1
    i=1:  counts['a'-'a'=0 ]++  ->  [0]=1
          counts['a'-'a'=0 ]--  ->  [0]=0
    i=2:  counts['t'-'a'=19]++  ->  [19]=1
          counts['r'-'a'=17]--  ->  [17]=0

    final: [2]=-1, [19]=1, rest 0  ->  not all zero  ->  false   ✓

Because the lengths are known equal, ONE loop covers both strings: increment
for s, decrement for t. Anagrams are exactly the case where every counter
lands on zero.

    Time:  O(n)
    Space: O(1)  — 26 ints, independent of n

WHY [26]int AND NOT map[byte]int: an array is a value type. It lives on the
stack, is zero-initialised for free, and indexing is pointer arithmetic. A map
hashes every key, masks to a bucket, compares tophash bytes, and allocates.
Same O(n), dramatically better constant — the benchmark at the bottom of this
file measures it.

⚠️ This approach BREAKS on Unicode: `s[i]-'a'` on a multi-byte character
produces a garbage index, silently corrupting a neighbouring counter or
panicking with index out of range.


================================================================================
APPROACH 2 · map[rune]int — the Unicode-safe answer ✅
================================================================================

    if utf8.RuneCountInString(s) != utf8.RuneCountInString(t) { return false }
    counts := make(map[rune]int)
    for _, r := range s { counts[r]++ }
    for _, r := range t {
        counts[r]--
        if counts[r] < 0 { return false }
    }
    return true

Note `for _, r := range s` decodes UTF-8 and yields runes, and the length guard
uses RuneCount, not len. Both changes are required — using `len` here would
reject valid anagrams whose bytes differ in count.

Go's zero value does the work again: `counts[r]++` on an absent key starts from
0, so no initialisation branch is needed.

    Time:  O(n)
    Space: O(k), k = distinct runes


================================================================================
APPROACH 3 · Sort and compare
================================================================================
    a := strings.Split(s, ""); sort.Strings(a)
    b := strings.Split(t, ""); sort.Strings(b)
    return slicesEqual(a, b)

Or, more idiomatically, sort []rune:

    ra, rb := []rune(s), []rune(t)
    sort.Slice(ra, func(i, j int) bool { return ra[i] < ra[j] })

    Time:  O(n log n)
    Space: O(n) — []rune(s) allocates a decoded copy

Slower, but it needs no alphabet assumption, so it also survives the follow-up.
Worth naming as the obvious first answer before you improve on it.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach          Time         Space   Unicode-safe?  Allocates?
    ----------------  -----------  ------  -------------  ----------
    [26]int     ✅✅  O(n)         O(1)    NO             no
    map[rune]   ✅    O(n)         O(k)    yes            yes
    Sort              O(n log n)   O(n)    yes            yes


================================================================================
THE UNICODE FOLLOW-UP (they will ask)
================================================================================
Three separate things break, and naming all three is what distinguishes a
senior answer:

1. `len(s)` counts bytes  ->  use utf8.RuneCountInString.
2. `s[i]` yields a byte   ->  range the string to get runes.
3. `s[i]-'a'` assumes a 26-letter alphabet -> use a map, which has no bound.

There is a fourth, subtler issue: "é" can be ONE rune (U+00E9) or TWO
(e + U+0301 combining acute). They render identically but compare unequal. A
fully correct answer normalises to NFC first. Go's stdlib has no normaliser —
it lives in golang.org/x/text/unicode/norm. Saying "I'd normalise with
x/text/unicode/norm" is a strong signal.


================================================================================
EDGE CASES
================================================================================
    ("a", "a")        -> true.   Minimum input.
    ("a", "ab")       -> false.  Caught by the length guard.
    ("aacc", "ccac")  -> false.  Same letter SET, different counts — this is
                                 the case a set-based solution gets wrong.
    ("", "")          -> true.   Loop does not run; all counters zero.


================================================================================
COMMON MISTAKES
================================================================================
1. Using map[byte]bool (a set) instead of counts — returns true for
   ("aacc", "ccac"). Sets discard multiplicity.

2. Omitting the length guard. With only the decrement loop, s="ab", t="a"
   drains cleanly and wrongly returns true.

3. `counts := make([]int, 26)` instead of `var counts [26]int`. Works, but it
   heap-allocates a slice where a stack array would do.

4. Using `len(s)` in the Unicode version — byte length is not rune length.

5. Ranging with an index and then indexing: `for i := range s { c := s[i] }`
   silently reintroduces byte semantics inside a loop you thought was
   rune-aware.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 49   Group Anagrams        — the canonical key idea, applied to grouping
    LC 438  Find All Anagrams in a String — anagram + sliding window
    LC 567  Permutation in String — fixed-window count matching
    LC 383  Ransom Note           — one-directional version of this check
================================================================================
*/

// isAnagram is the interview answer for the stated constraint: a fixed 26-slot
// array, one pass, no allocation. Time O(n), space O(1).
func isAnagram(s string, t string) bool {
	if len(s) != len(t) {
		return false
	}
	var counts [26]int // value type: stack, zeroed, no hashing
	for i := 0; i < len(s); i++ {
		counts[s[i]-'a']++ // s[i] is a byte; 'a' is 97
		counts[t[i]-'a']--
	}
	for _, c := range counts {
		if c != 0 {
			return false
		}
	}
	return true
}

// isAnagramUnicode is the follow-up answer: no alphabet assumption, rune-aware
// length check, rune-aware iteration.
func isAnagramUnicode(s string, t string) bool {
	if utf8.RuneCountInString(s) != utf8.RuneCountInString(t) {
		return false
	}
	counts := make(map[rune]int)
	for _, r := range s {
		counts[r]++ // zero value means no initialisation branch
	}
	for _, r := range t {
		counts[r]--
		if counts[r] < 0 {
			return false
		}
	}
	return true
}

// isAnagramSort is O(n log n) but needs no counting structure.
func isAnagramSort(s string, t string) bool {
	ra, rb := []rune(s), []rune(t)
	if len(ra) != len(rb) {
		return false
	}
	sort.Slice(ra, func(i, j int) bool { return ra[i] < ra[j] })
	sort.Slice(rb, func(i, j int) bool { return rb[i] < rb[j] })
	return string(ra) == string(rb)
}

func main() {
	type testCase struct {
		s, t string
		want bool
	}
	cases := []testCase{
		{"anagram", "nagaram", true},
		{"rat", "car", false},
		{"a", "a", true},
		{"a", "ab", false},
		{"aacc", "ccac", false},
		{"ab", "ba", true},
		{"", "", true},
	}

	impls := []struct {
		name string
		fn   func(string, string) bool
	}{
		{"[26]int array", isAnagram},
		{"map[rune]int ", isAnagramUnicode},
		{"sort         ", isAnagramSort},
	}

	allOK := true
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			if impl.fn(tc.s, tc.t) != tc.want {
				ok = false
			}
		}
		allOK = allOK && ok
		fmt.Printf("%s  %s (%d cases)\n", status(ok), impl.name, len(cases))
	}

	// A set discards multiplicity — the classic wrong answer.
	fmt.Println("\n--- why a set is the wrong tool ---")
	set := func(x string) map[rune]struct{} {
		m := make(map[rune]struct{})
		for _, r := range x {
			m[r] = struct{}{}
		}
		return m
	}
	a, b := "aacc", "ccac"
	sameSet := len(set(a)) == len(set(b))
	for r := range set(a) {
		if _, ok := set(b)[r]; !ok {
			sameSet = false
		}
	}
	fmt.Printf("  s=%q t=%q\n", a, b)
	fmt.Printf("  same letter set? %t   <- WRONG answer\n", sameSet)
	fmt.Printf("  correct answer:  %t\n", isAnagram(a, b))

	// Strings are bytes: the fact that breaks the fast path.
	fmt.Println("\n--- strings are BYTES, not characters ---")
	for _, w := range []string{"anagram", "école"} {
		fmt.Printf("  %-9q len=%d bytes, %d runes%s\n",
			w, len(w), utf8.RuneCountInString(w),
			map[bool]string{true: "  <- interchangeable",
				false: "  <- NOT interchangeable"}[len(w) == utf8.RuneCountInString(w)])
	}

	fmt.Println("\n--- the Unicode follow-up ---")
	u1, u2 := "école", "eécol"
	fmt.Printf("  isAnagramUnicode(%q, %q) = %t  <- correct\n",
		u1, u2, isAnagramUnicode(u1, u2))
	fmt.Printf("  the [26]int version would index s[i]-'a' on a 0xC3 byte:\n")
	fmt.Printf("    'é' first byte = %d, minus 'a' (97) = %d -> out of [0,26)\n",
		"é"[0], int("é"[0])-97)

	// Measure why [26]int beats a map.
	fmt.Println("\n--- [26]int vs map, 200k comparisons ---")
	long1 := strings.Repeat("abcdefghijklmnopqrstuvwxyz", 40)
	long2 := strings.Repeat("zyxwvutsrqponmlkjihgfedcba", 40)
	bench := func(name string, fn func(string, string) bool) {
		start := nowMillis()
		for i := 0; i < 200000; i++ {
			fn(long1, long2)
		}
		fmt.Printf("  %s %6d ms\n", name, nowMillis()-start)
	}
	bench("[26]int array", isAnagram)
	bench("map[rune]int ", isAnagramUnicode)

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}

// nowMillis is a tiny helper for the benchmark in main().
func nowMillis() int64 { return time.Now().UnixNano() / 1e6 }

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}
