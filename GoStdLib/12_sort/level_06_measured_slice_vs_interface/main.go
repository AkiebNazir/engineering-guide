/*
LEVEL 06 (measured) - sort.Slice (reflection-based) vs sort.Sort on a typed Interface

You will learn
  - sort.Slice accepts interface{} and uses reflection internally to build a
    generic Swap over whatever slice you passed - convenient, but not free
  - sort.Sort against a hand-written sort.Interface (level 5's pattern) uses
    your concrete Len/Less/Swap directly - no reflection involved
  - this level actually times both, sorting the SAME data shape repeatedly,
    with time.Now()/time.Since, and reports the real numbers from this run

Run: go run ./GoStdLib/12_sort/level_06_measured_slice_vs_interface
*/

package main

import (
	"fmt"
	"math/rand"
	"sort"
	"time"
)

type byAge []int

func (b byAge) Len() int           { return len(b) }
func (b byAge) Less(i, j int) bool { return b[i] < b[j] }
func (b byAge) Swap(i, j int)      { b[i], b[j] = b[j], b[i] }

func makeShuffled(n int, seed int64) []int {
	r := rand.New(rand.NewSource(seed))
	data := make([]int, n)
	for i := range data {
		data[i] = r.Intn(n)
	}
	return data
}

func main() {
	const size = 5000
	const iterations = 200
	seed := int64(42)

	startSlice := time.Now()
	for i := 0; i < iterations; i++ {
		data := makeShuffled(size, seed+int64(i))
		sort.Slice(data, func(a, b int) bool { return data[a] < data[b] })
	}
	elapsedSlice := time.Since(startSlice)

	startInterface := time.Now()
	for i := 0; i < iterations; i++ {
		data := byAge(makeShuffled(size, seed+int64(i)))
		sort.Sort(data)
	}
	elapsedInterface := time.Since(startInterface)

	// Correctness check independent of timing: both approaches must actually sort.
	check := makeShuffled(size, seed)
	sort.Slice(check, func(a, b int) bool { return check[a] < check[b] })
	if !sort.IntsAreSorted(check) {
		panic("sort.Slice result is not actually sorted")
	}
	checkTyped := byAge(makeShuffled(size, seed))
	sort.Sort(checkTyped)
	if !sort.IsSorted(checkTyped) {
		panic("sort.Sort result is not actually sorted")
	}

	fmt.Printf("size=%d iterations=%d  sort.Slice=%v  sort.Sort(typed)=%v\n", size, iterations, elapsedSlice, elapsedInterface)
	if elapsedInterface < elapsedSlice {
		fmt.Println("this run: the typed sort.Interface (no reflection) was faster, as skipping reflection predicts")
	} else {
		fmt.Println("this run: sort.Slice was as fast or faster here - report the honest number, not the assumption")
	}
	fmt.Println("OK")
}
