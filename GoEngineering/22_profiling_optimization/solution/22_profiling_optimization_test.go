package solution

import (
	"fmt"
	"math/rand"
	"reflect"
	"testing"
)

// sink prevents the compiler from proving a benchmark's result is unused
// and eliminating the call entirely — without this, `go test -bench` can
// silently benchmark nothing once the optimizer inlines and dead-code
// eliminates an unused return value.
var sink []Stat

func TestSummarizeNaiveBasic(t *testing.T) {
	records := []Record{
		{ID: "a", Tags: []string{"x"}, Values: []float64{1, 2, 3}},
		{ID: "b", Tags: []string{"y"}, Values: []float64{10}},
		{ID: "a", Tags: []string{"z"}, Values: []float64{4}},
	}
	got := SummarizeNaive(records)
	want := []Stat{
		{ID: "a", Count: 4, Sum: 10, Mean: 2.5, Max: 4},
		{ID: "b", Count: 1, Sum: 10, Mean: 10, Max: 10},
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("SummarizeNaive = %+v, want %+v", got, want)
	}
}

func TestSummarizeOptimizedBasic(t *testing.T) {
	records := []Record{
		{ID: "a", Tags: []string{"x"}, Values: []float64{1, 2, 3}},
		{ID: "b", Tags: []string{"y"}, Values: []float64{10}},
		{ID: "a", Tags: []string{"z"}, Values: []float64{4}},
	}
	got := SummarizeOptimized(records)
	want := []Stat{
		{ID: "a", Count: 4, Sum: 10, Mean: 2.5, Max: 4},
		{ID: "b", Count: 1, Sum: 10, Mean: 10, Max: 10},
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("SummarizeOptimized = %+v, want %+v", got, want)
	}
}

func TestSummarizeEmpty(t *testing.T) {
	if got := SummarizeNaive(nil); len(got) != 0 {
		t.Fatalf("SummarizeNaive(nil) = %+v, want empty", got)
	}
	if got := SummarizeOptimized(nil); len(got) != 0 {
		t.Fatalf("SummarizeOptimized(nil) = %+v, want empty", got)
	}
}

// TestNaiveAndOptimizedAgree is the property that actually matters: the
// optimized rewrite must be observably indistinguishable from the naive
// version in OUTPUT, differing only in cost. Randomized rather than a
// single fixture so this isn't just checking one hand-picked case.
func TestNaiveAndOptimizedAgree(t *testing.T) {
	rng := rand.New(rand.NewSource(42))
	for trial := 0; trial < 200; trial++ {
		records := genRandomRecords(rng, rng.Intn(50), rng.Intn(10)+1)
		naive := SummarizeNaive(records)
		opt := SummarizeOptimized(records)
		if !reflect.DeepEqual(naive, opt) {
			t.Fatalf("trial %d: naive and optimized disagree\nnaive=%+v\nopt=%+v\nrecords=%+v",
				trial, naive, opt, records)
		}
	}
}

// genRandomRecords generates n records drawn from numIDs distinct IDs, so
// grouping actually collapses multiple records per ID (exercising the
// accumulation path, not just the single-record case).
func genRandomRecords(rng *rand.Rand, n, numIDs int) []Record {
	records := make([]Record, 0, n)
	for i := 0; i < n; i++ {
		id := fmt.Sprintf("id-%d", rng.Intn(numIDs))
		numValues := rng.Intn(5)
		values := make([]float64, numValues)
		for j := range values {
			values[j] = rng.Float64()*200 - 100 // includes negatives, exercises Max init
		}
		numTags := rng.Intn(3)
		tags := make([]string, numTags)
		for j := range tags {
			tags[j] = fmt.Sprintf("tag%d", rng.Intn(5))
		}
		records = append(records, Record{ID: id, Tags: tags, Values: values})
	}
	return records
}

// benchRecords builds a fixed, realistic-shaped input once, outside the
// timed loop, per testing.B best practice: setup cost must not be counted
// against either implementation's per-op numbers.
func benchRecords() []Record {
	rng := rand.New(rand.NewSource(1))
	return genRandomRecordsFixedShape(rng, 1000, 20, 10)
}

func genRandomRecordsFixedShape(rng *rand.Rand, n, numIDs, valuesPerRecord int) []Record {
	records := make([]Record, 0, n)
	for i := 0; i < n; i++ {
		id := fmt.Sprintf("id-%d", rng.Intn(numIDs))
		values := make([]float64, valuesPerRecord)
		for j := range values {
			values[j] = rng.Float64() * 100
		}
		tags := []string{"alpha", "beta", "gamma"}
		records = append(records, Record{ID: id, Tags: tags, Values: values})
	}
	return records
}

func BenchmarkSummarizeNaive(b *testing.B) {
	records := benchRecords()
	b.ReportAllocs()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		sink = SummarizeNaive(records)
	}
}

func BenchmarkSummarizeOptimized(b *testing.B) {
	records := benchRecords()
	b.ReportAllocs()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		sink = SummarizeOptimized(records)
	}
}
