package main

import (
	"fmt"
	"strings"
)

/*
================================================================================
SOLUTION · LeetCode 125 · Valid Palindrome                               [Easy]
https://leetcode.com/problems/valid-palindrome/
================================================================================

THE CORE IDEA
-------------
Converging two pointers. `l` starts at the left end, `r` at the right end.
Each pointer first skips anything that is not a letter or digit, then the two
bytes are compared case-insensitively. A mismatch ends it (false); a match
moves both inward. If they meet, every mirrored pair matched (true).

    l, r := 0, len(s)-1
    for l < r {
        for l < r && !isAlnum(s[l]) { l++ }   // l < r inside is MANDATORY
        for l < r && !isAlnum(s[r]) { r-- }
        if lower(s[l]) != lower(s[r]) { return false }
        l++; r--
    }
    return true

The input is printable ASCII, so byte indexing is safe and no allocation is
needed: O(n) time, O(1) space.


================================================================================
APPROACH 1 · Normalise, then compare with the reverse
================================================================================
Build the cleaned lowercase string with a strings.Builder, then compare it
with its reverse (Go has no s[::-1]; reverse a []byte with a swap loop).
Correct, easy to say first, but O(n) extra space for two new buffers.


================================================================================
APPROACH 2 · Two pointers, in place ✅ (the answer)
================================================================================
Shown above.


================================================================================
APPROACH 3 · The same two pointers, written recursively
================================================================================
The pointer loop is tail-shaped recursion in disguise: check(l, r) is true
if l >= r, false if the ends differ, otherwise check(l+1, r-1).

    var check func(l, r int) bool
    check = func(l, r int) bool {
        if l >= r { return true }               // BASE CASE: met in the middle
        if s[l] != s[r] { return false }
        return check(l+1, r-1)                  // both pointers move inward
    }

Call stack for "racecar" (pure lowercase, no skipping):

    check(0,6) 'r'=='r' -> check(1,5) 'a'=='a' -> check(2,4) 'c'=='c'
      -> check(3,3) l >= r: BASE CASE, returns true
    true bubbles back up through every paused frame unchanged.

It is correct and a classic recursion warm-up, but it costs one stack frame
per PAIR (n/2 frames): Go does no tail-call elimination (topic 09 guide,
2.1), so at n = 2*10^5 that is 10^5 real frames the loop never needs. Say
that out loud when you present it. (Main below runs both.)


================================================================================
STEP BY STEP TRACE: "A man, a plan"
================================================================================
    l=0 'A'  r=12 'n'  -> 'a' vs 'n' differ -> false
(The full "A man, a plan, a canal: Panama" matches all 10 mirrored pairs.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time   Space       Note
    ---------------------------  -----  ----------  ------------------------
    Clean + reverse + compare    O(n)   O(n)        two new buffers
    Two pointers ✅              O(n)   O(1)        each pointer moves <= n
    Recursive two pointers       O(n)   O(n) stack  n/2 frames, no TCO in Go


================================================================================
EDGE CASES
================================================================================
    " " or ".,;:!"   -> true: nothing alphanumeric; the inner loops stop at
                        l == r thanks to their `l < r` guard.
    "0P"             -> false: '0' is a digit, not a letter; lowering 'P'
                        gives 'p', which is not '0'. (A classic wrong answer
                        treats digits as skippable.)
    odd length       -> the middle byte is never compared, and needn't be.


================================================================================
COMMON MISTAKES
================================================================================
1. Dropping `l < r` from the skip loops: on ".,;" l runs past r and indexes
   out of range -- in Go that is a PANIC, not Python's silent s[-1].
2. Using unicode.IsLetter only -- digits count as alphanumeric.
3. Lowering with `c + 32` unconditionally -- corrupts digits and punctuation;
   only shift 'A'..'Z'.
4. Converting to []rune "to be safe" -- unnecessary for ASCII input and it
   allocates 4 bytes per character.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Allow deleting at most one character (LC 680)?
A: On the first mismatch, try skipping s[l] OR s[r] and check the remaining
   window with this same loop -- problem 002.

Q: Full Unicode input?
A: Iterate runes (for the right end, utf8.DecodeLastRuneInString), use
   unicode.IsLetter/IsDigit and unicode.ToLower; case folding across scripts
   is where it gets genuinely hard.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 680  Valid Palindrome II      -- one deletion allowed (problem 002)
    LC 344  Reverse String           -- the same converging pointers, swapping
    LC 234  Palindrome Linked List   -- same check on a list (topic 08)
================================================================================
*/

func isAlnum(c byte) bool {
	return ('a' <= c && c <= 'z') || ('A' <= c && c <= 'Z') || ('0' <= c && c <= '9')
}

func lower(c byte) byte {
	if 'A' <= c && c <= 'Z' {
		return c + ('a' - 'A')
	}
	return c
}

// isPalindrome is the interview answer: converging two pointers.
// Time O(n), space O(1).
func isPalindrome(s string) bool {
	l, r := 0, len(s)-1
	for l < r {
		for l < r && !isAlnum(s[l]) {
			l++
		}
		for l < r && !isAlnum(s[r]) {
			r--
		}
		if lower(s[l]) != lower(s[r]) {
			return false
		}
		l++
		r--
	}
	return true
}

// isPalindromeClean builds the normalised string and compares with its reverse.
// Time O(n), space O(n).
func isPalindromeClean(s string) bool {
	var b strings.Builder
	for i := 0; i < len(s); i++ {
		if isAlnum(s[i]) {
			b.WriteByte(lower(s[i]))
		}
	}
	clean := []byte(b.String())
	for i, j := 0, len(clean)-1; i < j; i, j = i+1, j-1 {
		if clean[i] != clean[j] {
			return false
		}
	}
	return true
}

// isPalindromeRecursive is the same two-pointer check written as recursion,
// with the same skip rules. One stack frame per step.
func isPalindromeRecursive(s string) bool {
	var check func(l, r int) bool
	check = func(l, r int) bool {
		if l >= r {
			return true // BASE CASE: the pointers met
		}
		if !isAlnum(s[l]) {
			return check(l+1, r)
		}
		if !isAlnum(s[r]) {
			return check(l, r-1)
		}
		if lower(s[l]) != lower(s[r]) {
			return false
		}
		return check(l+1, r-1)
	}
	return check(0, len(s)-1)
}

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}

func main() {
	cases := []struct {
		s    string
		want bool
	}{
		{"A man, a plan, a canal: Panama", true},
		{"race a car", false},
		{" ", true},
		{".,;:!", true},
		{"0P", false},
		{"racecar", true},
		{"hello", false},
		{"a", true},
		{"ab_a", true},
	}
	allOK := true

	fmt.Println("--- correctness: loop, clean+reverse, recursive ---")
	for _, c := range cases {
		got := isPalindrome(c.s)
		ok := got == c.want && isPalindromeClean(c.s) == c.want && isPalindromeRecursive(c.s) == c.want
		allOK = allOK && ok
		fmt.Printf("%s  %-34q -> %-5v (want %v)\n", status(ok), c.s, got, c.want)
	}

	fmt.Println("\n--- max-size input (2*10^5 bytes): loop vs recursion ---")
	big := strings.Repeat("ab", 50_000) + strings.Repeat("ba", 50_000)
	okLoop := isPalindrome(big)
	okRec := isPalindromeRecursive(big)
	allOK = allOK && okLoop && okRec
	fmt.Printf("%s  loop: %v (O(1) space)\n", status(okLoop), okLoop)
	fmt.Printf("%s  recursive: %v (~10^5 stack frames; Go's growable stack absorbs\n", status(okRec), okRec)
	fmt.Println("      it, but it is memory the loop never spends)")

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
