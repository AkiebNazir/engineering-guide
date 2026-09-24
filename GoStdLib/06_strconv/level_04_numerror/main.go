/*
LEVEL 04 (advanced) - error handling: *strconv.NumError, ErrSyntax and ErrRange

You will learn
  - Atoi/ParseInt/ParseFloat/ParseBool all return *strconv.NumError on failure
  - NumError carries Func (which function failed), Num (the bad input string),
    and Err (the underlying strconv.ErrSyntax or strconv.ErrRange)
  - inspecting it for real with errors.As, and telling the two failure kinds
    apart with errors.Is

Run: go run ./GoStdLib/06_strconv/level_04_numerror
*/

package main

import (
	"errors"
	"fmt"
	"strconv"
)

func main() {
	// --- A syntax error: the input isn't a number at all. ---
	_, err := strconv.Atoi("12x")
	var syntaxErr *strconv.NumError
	if !errors.As(err, &syntaxErr) {
		panic(fmt.Sprintf("expected *strconv.NumError, got %T: %v", err, err))
	}
	if syntaxErr.Func != "Atoi" {
		panic(fmt.Sprintf("NumError.Func = %q, expected %q", syntaxErr.Func, "Atoi"))
	}
	if syntaxErr.Num != "12x" {
		panic(fmt.Sprintf("NumError.Num = %q, expected %q", syntaxErr.Num, "12x"))
	}
	if !errors.Is(syntaxErr.Err, strconv.ErrSyntax) {
		panic(fmt.Sprintf("expected ErrSyntax, got %v", syntaxErr.Err))
	}
	fmt.Printf("syntax error: Func=%s Num=%q Err=%v\n", syntaxErr.Func, syntaxErr.Num, syntaxErr.Err)

	// --- A range error: syntactically valid, but too big for the bit size. ---
	_, err = strconv.ParseInt("99999999999", 10, 8) // way over int8's range
	var rangeErr *strconv.NumError
	if !errors.As(err, &rangeErr) {
		panic(fmt.Sprintf("expected *strconv.NumError, got %T: %v", err, err))
	}
	if !errors.Is(rangeErr.Err, strconv.ErrRange) {
		panic(fmt.Sprintf("expected ErrRange, got %v", rangeErr.Err))
	}
	fmt.Printf("range error:  Func=%s Num=%q Err=%v\n", rangeErr.Func, rangeErr.Num, rangeErr.Err)

	// --- ParseFloat and ParseBool follow the exact same NumError contract. ---
	_, err = strconv.ParseFloat("not-a-float", 64)
	var floatErr *strconv.NumError
	if !errors.As(err, &floatErr) || !errors.Is(floatErr.Err, strconv.ErrSyntax) {
		panic(fmt.Sprintf("expected ParseFloat syntax NumError, got %v", err))
	}

	_, err = strconv.ParseBool("maybe")
	var boolErr *strconv.NumError
	if !errors.As(err, &boolErr) || !errors.Is(boolErr.Err, strconv.ErrSyntax) {
		panic(fmt.Sprintf("expected ParseBool syntax NumError, got %v", err))
	}

	fmt.Println("all four parse functions produced inspectable *strconv.NumError values")
	fmt.Println("OK")
}
