package main

import (
	"container/heap"
	"fmt"
	"reflect"
	"sort"
)

/*
================================================================================
SOLUTION · LeetCode 347 · Top K Frequent Elements                       [Medium]
https://leetcode.com/problems/top-k-frequent-elements/
================================================================================

THE CORE IDEA
-------------
Split the problem in two and notice they are independent:

    PHASE 1   count       O(n)   — a frequency map. Never the bottleneck.
    PHASE 2   select k    ???    — this is the entire problem.

Then the one insight that unlocks the optimal answer:

    A FREQUENCY IS A SMALL BOUNDED INTEGER.

No value can appear more than n times or fewer than once, so every frequency
lives in [1, n]. Whenever your sort key is a bounded integer, you do not need
comparison sorting at all — you can INDEX BY IT. That is bucket sort, and it
turns O(m log m) into O(n).

    buckets[f] = [every value that appears exactly f times]

Walk the buckets from the top down and take the first k values you meet. You
never compared two frequencies to each other.


================================================================================
APPROACH 1 · Bucket sort by frequency ✅✅ (the O(n) answer)
================================================================================
Frequencies are bounded by n, so index an array by frequency directly.

    Time:  O(n)        Space: O(n)

In Go, a bucket is just a `[]int`. Since zero frequency is impossible, we can
allocate `make([][]int, len(nums)+1)`.

STEP BY STEP for nums = [1,1,1,2,2,3], k = 2:

    freq = {1: 3, 2: 2, 3: 1}       n = 6, so buckets has indices 0..6

    index:    0     1     2     3     4     5     6
    bucket:  [ ]   [3]   [2]   [1]   [ ]   [ ]   [ ]

    walk backwards from index 6:
       f=6 empty · f=5 empty · f=4 empty
       f=3 -> take 1   out=[1]
       f=2 -> take 2   out=[1,2]   len == k, return    ✓

⚠️  BUCKET SIZE MUST BE n+1, NOT n
    A value can appear all n times (`[4,4,4,4]` -> freq 4 with n = 4).

================================================================================
APPROACH 2 · Min-heap of size k ✅ (the standard "top k" answer)
================================================================================
To keep the k LARGEST items, hold a MIN-heap of size k. The smallest of your
current winners sits at the root, which is exactly the one to evict when a
better candidate arrives.

    Time:  O(n + m log k)        Space: O(m + k)

In Go, we use `container/heap`. Since it requires implementing `heap.Interface`,
it's slightly verbose compared to Python, but standard practice.
*/

// topKFrequent is the O(n) bucket sort approach.
func topKFrequent(nums []int, k int) []int {
	// 1. Count frequencies: O(n)
	counts := make(map[int]int)
	for _, num := range nums {
		counts[num]++
	}

	// 2. Bucket by frequency: O(n)
	// Index = frequency. Size n+1 because max possible freq is n.
	buckets := make([][]int, len(nums)+1)
	for num, count := range counts {
		buckets[count] = append(buckets[count], num)
	}

	// 3. Collect top k: O(n)
	var ans []int
	for i := len(buckets) - 1; i > 0; i-- {
		for _, num := range buckets[i] {
			ans = append(ans, num)
			if len(ans) == k {
				return ans
			}
		}
	}
	return ans
}

// -----------------------------------------------------------------------------
// APPROACH 2: Min-Heap
// -----------------------------------------------------------------------------

type Item struct {
	val  int
	freq int
}

type MinHeap []Item

func (h MinHeap) Len() int           { return len(h) }
func (h MinHeap) Less(i, j int) bool { return h[i].freq < h[j].freq }
func (h MinHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *MinHeap) Push(x any)        { *h = append(*h, x.(Item)) }
func (h *MinHeap) Pop() any {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[0 : n-1]
	return x
}

func topKFrequentHeap(nums []int, k int) []int {
	counts := make(map[int]int)
	for _, num := range nums {
		counts[num]++
	}

	h := &MinHeap{}
	heap.Init(h)

	for num, count := range counts {
		heap.Push(h, Item{val: num, freq: count})
		if h.Len() > k {
			heap.Pop(h)
		}
	}

	ans := make([]int, k)
	for i := 0; i < k; i++ {
		// Note: heap pop gives the smallest frequencies first.
		ans[i] = heap.Pop(h).(Item).val
	}
	return ans
}

// =============================================================================
// TESTS
// =============================================================================

func main() {
	cases := []struct {
		nums []int
		k    int
		want []int
	}{
		{[]int{1, 1, 1, 2, 2, 3}, 2, []int{1, 2}},
		{[]int{1}, 1, []int{1}},
		{[]int{1, 2}, 2, []int{1, 2}},
		{[]int{4, 4, 4, 4}, 1, []int{4}},
		{[]int{5, 5, 4, 4, 3, 3, 2, 1}, 3, []int{3, 4, 5}},
		{[]int{-1, -1, -1, 0, 0, 7}, 2, []int{-1, 0}},
	}

	impls := []struct {
		name string
		fn   func([]int, int) []int
	}{
		{"bucket sort", topKFrequent},
		{"min-heap   ", topKFrequentHeap},
	}

	allOK := true
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			got := impl.fn(tc.nums, tc.k)

			// Since order doesn't matter, we sort before comparing.
			gotCopy := append([]int(nil), got...)
			wantCopy := append([]int(nil), tc.want...)
			sort.Ints(gotCopy)
			sort.Ints(wantCopy)

			if !reflect.DeepEqual(gotCopy, wantCopy) {
				ok = false
				fmt.Printf("FAIL: %s\n  Input: %v, k=%d\n  Got:  %v\n  Want: %v\n",
					impl.name, tc.nums, tc.k, got, tc.want)
			}
		}
		if ok {
			fmt.Printf("PASS: %s (%d cases)\n", impl.name, len(cases))
		}
		allOK = allOK && ok
	}

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
