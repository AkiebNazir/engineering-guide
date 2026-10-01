/*
LEVEL 07 (advanced) - the Stringer interface: fmt calls String() automatically

You will learn
  - fmt.Stringer is `interface { String() string }` - defined in fmt but you
    never import it to satisfy it, you just add the method
  - %v, %s, Println, and Printf all call String() automatically when the value
    implements it, instead of falling back to the default representation
  - a POINTER-receiver String() is only in a *T's method set, not a plain T's -
    passing the value (not the address) silently skips String() entirely

Run: go run ./GoStdLib/02_fmt/level_07_stringer_interface
*/

package main

import "fmt"

// Temperature implements Stringer with a VALUE receiver, so both Temperature
// and *Temperature satisfy fmt.Stringer.
type Temperature float64

func (t Temperature) String() string {
	return fmt.Sprintf("%.1f°C", float64(t))
}

// Status implements Stringer with a POINTER receiver - only *Status
// satisfies fmt.Stringer, a plain Status value does not.
type Status int

const (
	StatusPending Status = iota
	StatusDone
)

func (s *Status) String() string {
	switch *s {
	case StatusPending:
		return "pending"
	case StatusDone:
		return "done"
	default:
		return "unknown"
	}
}

func main() {
	t := Temperature(21.567)

	// %v and %s both call String() automatically.
	vForm := fmt.Sprintf("%v", t)
	sForm := fmt.Sprintf("%s", t)
	want := "21.6°C"
	if vForm != want {
		panic(fmt.Sprintf("%%v should use String(): got %q, want %q", vForm, want))
	}
	if sForm != want {
		panic(fmt.Sprintf("%%s should use String(): got %q, want %q", sForm, want))
	}

	// Confirm it really is our String(), not a coincidence of numeric formatting:
	// %v on the raw float64 conversion looks completely different.
	rawForm := fmt.Sprintf("%v", float64(t))
	if rawForm == want {
		panic("test is broken: raw float64 formatting should NOT equal the Stringer output")
	}

	// Pointer-receiver Stringer: *Status satisfies fmt.Stringer.
	done := StatusDone
	pointerForm := fmt.Sprintf("%v", &done)
	if pointerForm != "done" {
		panic(fmt.Sprintf("expected *Status to use String(): got %q", pointerForm))
	}

	// THE TRAP (demonstrated, not just described): the plain VALUE does not
	// satisfy fmt.Stringer (String has a pointer receiver), so fmt falls back
	// to its default integer formatting instead of calling String().
	valueForm := fmt.Sprintf("%v", done)
	if valueForm != "1" {
		panic(fmt.Sprintf("expected plain Status value to fall back to default int form %q, got %q", "1", valueForm))
	}
	if valueForm == pointerForm {
		panic("test is broken: value form should differ from pointer form here")
	}

	var _ fmt.Stringer = Temperature(0) // compiles: value receiver
	var _ fmt.Stringer = &done          // compiles: pointer receiver
	// var _ fmt.Stringer = done        // would NOT compile: Status has no String() in its own method set

	fmt.Println("Temperature (value receiver):", t)
	fmt.Println("*Status     (pointer, via String()):", &done)
	fmt.Println("Status      (value, no String() in method set):", done)
	fmt.Println("OK")
}
