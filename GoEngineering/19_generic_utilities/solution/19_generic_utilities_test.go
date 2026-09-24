package genutil

import (
	"errors"
	"slices"
	"strconv"
	"testing"
)

// label is a named string type used (alongside plain int) to prove Map,
// Filter and Reduce are genuinely parametric — exercised over two
// unrelated element types, not one type wearing a generic label.
type label string

func TestMap(t *testing.T) {
	t.Run("int to string", func(t *testing.T) {
		got := Map([]int{1, 2, 3}, func(n int) string { return strconv.Itoa(n * 2) })
		want := []string{"2", "4", "6"}
		if !slices.Equal(got, want) {
			t.Errorf("Map() = %v, want %v", got, want)
		}
	})

	t.Run("label to length", func(t *testing.T) {
		got := Map([]label{"a", "bb", "ccc"}, func(l label) int { return len(l) })
		want := []int{1, 2, 3}
		if !slices.Equal(got, want) {
			t.Errorf("Map() = %v, want %v", got, want)
		}
	})

	t.Run("nil in nil out", func(t *testing.T) {
		got := Map[int, string](nil, func(n int) string { return "" })
		if got != nil {
			t.Errorf("Map(nil) = %#v, want nil", got)
		}
	})
}

func TestFilter(t *testing.T) {
	tests := []struct {
		name string
		in   []int
		pred func(int) bool
		want []int
	}{
		{"evens", []int{1, 2, 3, 4, 5, 6}, func(n int) bool { return n%2 == 0 }, []int{2, 4, 6}},
		{"none match", []int{1, 3, 5}, func(n int) bool { return n%2 == 0 }, []int{}},
		{"empty input", []int{}, func(n int) bool { return true }, []int{}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel() // safe: tt is per-iteration (Go 1.22+ loop var semantics)
			got := Filter(tt.in, tt.pred)
			if !slices.Equal(got, tt.want) {
				t.Errorf("Filter(%v) = %v, want %v", tt.in, got, tt.want)
			}
		})
	}

	t.Run("nil in nil out", func(t *testing.T) {
		got := Filter[int](nil, func(int) bool { return true })
		if got != nil {
			t.Errorf("Filter(nil) = %#v, want nil", got)
		}
	})
}

func TestReduce(t *testing.T) {
	t.Run("sum via reduce", func(t *testing.T) {
		got := Reduce([]int{1, 2, 3, 4}, 0, func(acc, n int) int { return acc + n })
		if got != 10 {
			t.Errorf("Reduce sum = %d, want 10", got)
		}
	})

	t.Run("concat labels into string", func(t *testing.T) {
		got := Reduce([]label{"a", "b", "c"}, "", func(acc string, l label) string { return acc + string(l) })
		if got != "abc" {
			t.Errorf("Reduce concat = %q, want %q", got, "abc")
		}
	})

	t.Run("empty slice returns init unchanged", func(t *testing.T) {
		got := Reduce([]int(nil), 42, func(acc, n int) int { return acc + n })
		if got != 42 {
			t.Errorf("Reduce(nil) = %d, want 42", got)
		}
	})
}

func TestKeysValues(t *testing.T) {
	m := map[string]int{"a": 1, "b": 2, "c": 3}

	keys := Keys(m)
	slices.Sort(keys)
	wantKeys := []string{"a", "b", "c"}
	if !slices.Equal(keys, wantKeys) {
		t.Errorf("Keys() sorted = %v, want %v", keys, wantKeys)
	}

	values := Values(m)
	slices.Sort(values)
	wantValues := []int{1, 2, 3}
	if !slices.Equal(values, wantValues) {
		t.Errorf("Values() sorted = %v, want %v", values, wantValues)
	}
}

func TestMaxMin(t *testing.T) {
	t.Run("int", func(t *testing.T) {
		max, ok := Max([]int{3, 1, 4, 1, 5, 9, 2, 6})
		if !ok || max != 9 {
			t.Errorf("Max() = (%d, %v), want (9, true)", max, ok)
		}
		min, ok := Min([]int{3, 1, 4, 1, 5, 9, 2, 6})
		if !ok || min != 1 {
			t.Errorf("Min() = (%d, %v), want (1, true)", min, ok)
		}
	})

	t.Run("float64", func(t *testing.T) {
		max, ok := Max([]float64{2.5, -1.1, 3.7})
		if !ok || max != 3.7 {
			t.Errorf("Max() = (%v, %v), want (3.7, true)", max, ok)
		}
	})

	t.Run("empty", func(t *testing.T) {
		if _, ok := Max([]int{}); ok {
			t.Error("Max(empty) ok = true, want false")
		}
		if _, ok := Min([]int{}); ok {
			t.Error("Min(empty) ok = true, want false")
		}
	})
}

func TestSum(t *testing.T) {
	if got := Sum([]int{1, 2, 3, 4}); got != 10 {
		t.Errorf("Sum(ints) = %d, want 10", got)
	}
	if got := Sum([]float64{1.5, 2.5}); got != 4.0 {
		t.Errorf("Sum(floats) = %v, want 4.0", got)
	}
	if got := Sum([]int{}); got != 0 {
		t.Errorf("Sum(empty) = %d, want 0", got)
	}
}

func TestResult(t *testing.T) {
	t.Run("ok branch", func(t *testing.T) {
		r := Ok(42)
		if !r.IsOk() {
			t.Fatal("IsOk() = false, want true")
		}
		if r.Error() != nil {
			t.Errorf("Error() = %v, want nil", r.Error())
		}
		if got := r.Unwrap(); got != 42 {
			t.Errorf("Unwrap() = %d, want 42", got)
		}
		if got := r.UnwrapOr(-1); got != 42 {
			t.Errorf("UnwrapOr() = %d, want 42", got)
		}
	})

	t.Run("err branch", func(t *testing.T) {
		wantErr := errors.New("boom")
		r := Err[int](wantErr)
		if r.IsOk() {
			t.Fatal("IsOk() = true, want false")
		}
		if !errors.Is(r.Error(), wantErr) {
			t.Errorf("Error() = %v, want %v", r.Error(), wantErr)
		}
		if got := r.UnwrapOr(-1); got != -1 {
			t.Errorf("UnwrapOr() = %d, want -1", got)
		}
	})

	t.Run("unwrap panics on error result", func(t *testing.T) {
		defer func() {
			if recover() == nil {
				t.Error("Unwrap() on error Result did not panic")
			}
		}()
		Err[int](errors.New("boom")).Unwrap()
	})

	t.Run("ResultMap transforms ok, propagates err", func(t *testing.T) {
		ok := ResultMap(Ok(21), func(n int) int { return n * 2 })
		if !ok.IsOk() || ok.Unwrap() != 42 {
			t.Errorf("ResultMap(Ok) = %+v, want Ok(42)", ok)
		}

		wantErr := errors.New("boom")
		failed := ResultMap(Err[int](wantErr), func(n int) string { return "unreachable" })
		if failed.IsOk() {
			t.Fatal("ResultMap(Err) IsOk() = true, want false")
		}
		if !errors.Is(failed.Error(), wantErr) {
			t.Errorf("ResultMap(Err).Error() = %v, want %v", failed.Error(), wantErr)
		}
	})

	t.Run("AndThen chains ok, short-circuits err", func(t *testing.T) {
		double := func(n int) Result[int] { return Ok(n * 2) }
		got := Ok(5).AndThen(double).AndThen(double)
		if got.Unwrap() != 20 {
			t.Errorf("AndThen chain = %d, want 20", got.Unwrap())
		}

		wantErr := errors.New("boom")
		short := Err[int](wantErr).AndThen(double)
		if short.IsOk() || !errors.Is(short.Error(), wantErr) {
			t.Errorf("AndThen on Err = %+v, want unchanged Err(%v)", short, wantErr)
		}
	})
}

func TestOption(t *testing.T) {
	t.Run("some branch", func(t *testing.T) {
		o := Some("hi")
		if !o.IsSome() {
			t.Fatal("IsSome() = false, want true")
		}
		if got := o.Unwrap(); got != "hi" {
			t.Errorf("Unwrap() = %q, want %q", got, "hi")
		}
	})

	t.Run("none branch", func(t *testing.T) {
		o := None[string]()
		if o.IsSome() {
			t.Fatal("IsSome() = true, want false")
		}
		if got := o.UnwrapOr("fallback"); got != "fallback" {
			t.Errorf("UnwrapOr() = %q, want %q", got, "fallback")
		}
	})

	t.Run("zero value is None", func(t *testing.T) {
		var o Option[int]
		if o.IsSome() {
			t.Error("zero-value Option.IsSome() = true, want false")
		}
	})

	t.Run("unwrap panics on none", func(t *testing.T) {
		defer func() {
			if recover() == nil {
				t.Error("Unwrap() on None did not panic")
			}
		}()
		None[int]().Unwrap()
	})

	t.Run("OptionMap transforms some, propagates none", func(t *testing.T) {
		some := OptionMap(Some(21), func(n int) int { return n * 2 })
		if !some.IsSome() || some.Unwrap() != 42 {
			t.Errorf("OptionMap(Some) = %+v, want Some(42)", some)
		}

		none := OptionMap(None[int](), func(n int) string { return "unreachable" })
		if none.IsSome() {
			t.Error("OptionMap(None) IsSome() = true, want false")
		}
	})
}
