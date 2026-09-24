/*
LEVEL 08 (advanced) - interop: strings + strconv, parse then reformat

You will learn
  - strings.Split to break a delimited numeric string into tokens
  - strconv.Atoi to parse each token, with real error handling
  - strings.Builder + strconv.Itoa to build the reformatted result back up
    without any += concatenation

Run: go run ./GoStdLib/05_strings/level_08_interop_strconv
*/

package main

import (
	"fmt"
	"strconv"
	"strings"
)

// sumAndFormat parses "n1;n2;n3" into ints, and returns both their sum and a
// re-joined "n1+n2+n3=sum" string built with strings.Builder.
func sumAndFormat(csv string) (sum int, formatted string, err error) {
	tokens := strings.Split(csv, ";")
	var b strings.Builder
	for i, tok := range tokens {
		n, convErr := strconv.Atoi(strings.TrimSpace(tok))
		if convErr != nil {
			return 0, "", fmt.Errorf("token %d (%q): %w", i, tok, convErr)
		}
		sum += n
		if i > 0 {
			b.WriteString("+")
		}
		b.WriteString(strconv.Itoa(n))
	}
	b.WriteString("=")
	b.WriteString(strconv.Itoa(sum))
	return sum, b.String(), nil
}

func main() {
	sum, formatted, err := sumAndFormat("4; 15 ;23;8")
	if err != nil {
		panic(fmt.Sprintf("sumAndFormat failed: %v", err))
	}
	if sum != 50 {
		panic(fmt.Sprintf("sum = %d, expected 50", sum))
	}
	if formatted != "4+15+23+8=50" {
		panic(fmt.Sprintf("formatted = %q, expected %q", formatted, "4+15+23+8=50"))
	}

	_, _, err = sumAndFormat("4;oops;8")
	if err == nil {
		panic("expected an error for a non-numeric token")
	}

	fmt.Printf("%s\n", formatted)
	fmt.Println("OK")
}
