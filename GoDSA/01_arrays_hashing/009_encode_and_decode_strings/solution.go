package main

import (
	"fmt"
	"reflect"
	"strconv"
	"strings"
)

/*
================================================================================
SOLUTION · LeetCode 271 · Encode and Decode Strings                     [Medium]
https://leetcode.com/problems/encode-and-decode-strings/
================================================================================

THE CORE IDEA
-------------
This is not an algorithms problem — it is a PROTOCOL DESIGN problem. There is
no clever trick and no complexity to optimise. There is exactly one question:

    HOW DOES THE DECODER KNOW WHERE ONE STRING ENDS AND THE NEXT BEGINS?

The obvious idea is a separator:
    ["neet","code"]  ->  "neet#code"  ->  split on "#"  ->  ["neet","code"]  ✓

Now read the constraint again, because it is the entire problem:
    strs[i] contains ANY possible characters out of 256 valid ASCII

So the input may legitimately contain your separator:
    ["ne#et","code"] ->  "ne#et#code"  -> split("#") -> ["ne","et","code"]  ✗
                                                          3 strings, not 2

There is no safe delimiter when the alphabet is unrestricted.

The fix is to stop searching for a magic character and change the SHAPE of the
encoding. Prefix each string with its length, and use a delimiter only to separate
the length from the payload.

    "4#neet4#code"

The decoder reads digits until "#", parses the length L, and takes the next L
bytes as the string, IGNORING any "#" characters within the payload.


================================================================================
APPROACH 1 · Length-Prefix (The standard protocol)
================================================================================
For each string, encode as: `fmt.Sprintf("%d#%s", len(s), s)`.
To decode, read until `#`, convert to integer L, read L bytes, and repeat.

Time:  O(N) for both encode and decode (N = total characters)
Space: O(N) to hold the output strings

In Go, we should use `strings.Builder` for efficient concatenation.

================================================================================
APPROACH 2 · Escaping (Alternative)
================================================================================
Pick a separator, say `#`. To prevent collisions, replace any literal `#` in
the input with `##`. Then separate strings with ` # `.
This is how CSV works, but length-prefix is faster and safer to implement from
scratch in an interview.
*/

// Encode length-prefixes every string.
func encode(strs []string) string {
	var sb strings.Builder
	for _, s := range strs {
		sb.WriteString(strconv.Itoa(len(s)))
		sb.WriteByte('#')
		sb.WriteString(s)
	}
	return sb.String()
}

// Decode parses the length, jumps that many bytes, and repeats.
func decode(s string) []string {
	var ans []string
	i := 0
	for i < len(s) {
		// Find the delimiter marking the end of the length
		j := i
		for s[j] != '#' {
			j++
		}
		
		// Parse the length
		l, _ := strconv.Atoi(s[i:j])
		
		// The payload starts immediately after the '#'
		start := j + 1
		end := start + l
		
		ans = append(ans, s[start:end])
		i = end
	}
	return ans
}

// =============================================================================
// TESTS
// =============================================================================

func main() {
	cases := [][]string{
		{"neet", "code", "love", "you"},
		{"we", "say", ":", "yes"},
		{},           // empty list
		{""},         // list with one empty string
		{"", ""},     // list with two empty strings
		{"#", "##"},  // strings consisting only of the delimiter
		{"123#456"},  // string containing what looks like a prefix
	}

	allOK := true
	for _, tc := range cases {
		encoded := encode(tc)
		decoded := decode(encoded)
		
		// For an empty slice, deep equal needs nil or empty checks,
		// but since we allocate nil slice in decode, it might differ from empty test literal.
		// We'll normalize nil slices to empty for comparison.
		if len(tc) == 0 && len(decoded) == 0 {
			fmt.Printf("PASS: [] -> %q -> []\n", encoded)
			continue
		}
		
		if !reflect.DeepEqual(decoded, tc) {
			allOK = false
			fmt.Printf("FAIL: Input: %q\n  Encoded: %q\n  Decoded: %q\n", tc, encoded, decoded)
		} else {
			fmt.Printf("PASS: %q -> %q -> %q\n", tc, encoded, decoded)
		}
	}

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
