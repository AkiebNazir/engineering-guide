/*
LEVEL 09 (advanced) - fmt.Formatter for custom verb handling, and its silent-output trap

You will learn
  - implementing `Format(f fmt.State, verb rune)` lets a type control EVERY
    verb applied to it (%v, %s, %d, ...), overriding fmt's defaults entirely
  - fmt.State embeds io.Writer plus flag/width/precision accessors (f.Flag('+'),
    f.Width(), f.Precision())
  - THE TRAP: once a type implements Formatter, fmt hands it ALL verbs. If the
    switch inside Format has no case (and no default) for a given verb,
    NOTHING is written - not an error, just silent empty output
  - the fix: add a default case, typically falling back to a verb you do handle

Run: go run ./GoStdLib/02_fmt/level_09_custom_formatter_trap
*/

package main

import "fmt"

// Money stores cents and implements fmt.Formatter, but NAIVELY: it only
// handles 'v' and 'd'. Any other verb silently produces nothing.
type Money int64

func (m Money) Format(f fmt.State, verb rune) {
	switch verb {
	case 'v':
		if f.Flag('+') {
			fmt.Fprintf(f, "USD %.2f", float64(m)/100)
		} else {
			fmt.Fprintf(f, "$%.2f", float64(m)/100)
		}
	case 'd':
		fmt.Fprintf(f, "%d", int64(m))
	}
	// NO default case: any other verb (e.g. %s, %x, %q) writes nothing at all.
}

// FixedMoney is the same idea, fixed: unrecognized verbs fall back to the
// %v form instead of vanishing.
type FixedMoney int64

func (m FixedMoney) Format(f fmt.State, verb rune) {
	switch verb {
	case 'v':
		if f.Flag('+') {
			fmt.Fprintf(f, "USD %.2f", float64(m)/100)
		} else {
			fmt.Fprintf(f, "$%.2f", float64(m)/100)
		}
	case 'd':
		fmt.Fprintf(f, "%d", int64(m))
	default:
		// Fall back to the %v form we already know how to produce, instead
		// of leaving the verb unhandled and writing nothing.
		fmt.Fprintf(f, "%v", FixedMoney(m))
	}
}

func main() {
	m := Money(1234) // $12.34

	// The verbs the naive type DOES handle work fine.
	v := fmt.Sprintf("%v", m)
	if v != "$12.34" {
		panic(fmt.Sprintf("%%v mismatch: got %q, want %q", v, "$12.34"))
	}
	plusV := fmt.Sprintf("%+v", m)
	if plusV != "USD 12.34" {
		panic(fmt.Sprintf("%%+v mismatch: got %q, want %q", plusV, "USD 12.34"))
	}
	d := fmt.Sprintf("%d", m)
	if d != "1234" {
		panic(fmt.Sprintf("%%d mismatch: got %q, want %q", d, "1234"))
	}

	// THE TRAP, demonstrated for real: %s is not handled by the naive switch,
	// so fmt.Sprintf produces an EMPTY string - no error, no panic, nothing.
	naiveS := fmt.Sprintf("%s", m)
	if naiveS != "" {
		panic(fmt.Sprintf("expected the naive Formatter to silently produce empty output for %%s, got %q", naiveS))
	}
	naiveInSentence := fmt.Sprintf("price: [%s]", m)
	if naiveInSentence != "price: []" {
		panic(fmt.Sprintf("expected the missing verb to vanish inline, got %q", naiveInSentence))
	}

	// THE FIX: FixedMoney handles the same case with a default fallback.
	fm := FixedMoney(1234)
	fixedS := fmt.Sprintf("%s", fm)
	if fixedS != "$12.34" {
		panic(fmt.Sprintf("expected fixed Formatter to fall back to %%v form, got %q", fixedS))
	}
	fixedInSentence := fmt.Sprintf("price: [%s]", fm)
	if fixedInSentence != "price: [$12.34]" {
		panic(fmt.Sprintf("expected fixed Formatter to render in sentence, got %q", fixedInSentence))
	}

	fmt.Printf("naive Formatter:  %%v=%s %%+v=%s %%d=%s\n", v, plusV, d)
	fmt.Printf("naive Formatter,  %%s -> %q (BUG: silently empty)\n", naiveS)
	fmt.Printf("naive Formatter,  \"price: [%%s]\" -> %q\n", naiveInSentence)
	fmt.Printf("fixed Formatter,  %%s -> %q (falls back to %%v)\n", fixedS)
	fmt.Println("OK")
}
