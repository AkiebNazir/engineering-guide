package main

import (
	"fmt"
	"math/rand"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 146 · LRU Cache                                     [Medium]
https://leetcode.com/problems/lru-cache/
================================================================================

THE CORE IDEA
--------------
O(1) Get/Put needs a map AND a doubly linked list (topic guide Part 10):
a map alone has no notion of order; a singly linked list can't unlink an
arbitrary node in O(1) without a predecessor reference, which only a doubly
linked list gives for free. The map stores *dNode pointers, so promoting or
evicting a key mutates the SAME node the map already references.

Two sentinel nodes (head, tail) eliminate every empty-list / single-node
special case in remove/insertFront — this topic's Part 2 dummy idiom,
doubled up for a doubly linked list.


================================================================================
APPROACH 1 · container/list (standard-library shortcut, priced not coded)
================================================================================
Go's container/list is a general-purpose doubly linked list with stable
*Element handles — legitimate for this exact use case (topic guide Part 8
names LRU explicitly as where it "shines"). Every Value is `any`, so reading
it back costs a type assertion. Not coded here because hand-rolling a
2-field dNode is simpler and what interviewers expect to see, but worth
naming as "the standard-library alternative."


================================================================================
APPROACH 2 · Doubly linked list + hashmap ✅ (the answer)
================================================================================
    type dNode struct {
        key, val   int
        prev, next *dNode
    }
    type LRUCache struct {
        capacity   int
        cache      map[int]*dNode
        head, tail *dNode
    }

remove(n) unlinks n given only n itself (n carries its own prev/next).
insertFront(n) splices n in right after head — "most recent."
Get promotes on hit; Put updates+promotes on existing key, or inserts (and
evicts the node before tail if full) on a new key.

    Time: O(1) per Get/Put.     Space: O(capacity).


================================================================================
APPROACH 3 · Naive map + slice-based order (what NOT to do, priced and coded)
================================================================================
A plain map for values, plus a separate []int slice tracking recency order,
where every touch does a linear scan-and-remove from the slice (shifting
every element after it) followed by an append.

    Time: O(n) per Get/Put — the slice removal is the culprit.
    Space: O(capacity).

This is the "obvious first attempt" that fails the O(1) follow-up. The
benchmark below measures the cost as capacity grows.


================================================================================
STEP BY STEP TRACE — capacity=2
================================================================================
    Put(1,1)  cache={1}          MRU-front order: [1]
    Put(2,2)  cache={1,2}        MRU-front order: [2,1]
    Get(1)    hit, promote 1     MRU-front order: [1,2]   returns 1
    Put(3,3)  full, evict LRU=2  MRU-front order: [3,1]
    Get(2)    miss                returns -1
    Put(4,4)  full, evict LRU=1  MRU-front order: [4,3]
    Get(1)    miss                returns -1
    Get(3)    hit, promote 3      MRU-front order: [3,4]   returns 3
    Get(4)    hit, promote 4      MRU-front order: [4,3]   returns 4

    head <-> [1] <-> [2] <-> tail     (right after Put(1,1), Put(2,2))
    head <-> [1] <-> [2] <-> tail     (after Get(1): 1 already at front, no-op reorder)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time (Get/Put)   Space         Note
    ----------------------------  ---------------  ------------  ---------------------------
    container/list                O(1)             O(capacity)   stdlib, `any` + assertions
    Doubly linked list + map ✅   O(1)             O(capacity)   the answer
    map + slice (naive)          O(n)             O(capacity)   the anti-pattern


================================================================================
EDGE CASES
================================================================================
    capacity == 1              every Put after the first evicts immediately
    Get on empty cache          must return -1, not panic
    Put on an EXISTING key      must update value AND promote to MRU
    repeated Get on same key    must not corrupt the list (idempotent reorder)
    Put overflowing by exactly 1  evicts exactly one key, the true LRU


================================================================================
COMMON MISTAKES
================================================================================
1. Updating only the map or only the linked list on eviction — they must
   always agree on membership (topic guide Part 8, mistake 8).
2. Forgetting Put on an existing key must ALSO promote it, not just
   overwrite the value.
3. Reaching for a singly linked list to "save a field," then discovering
   remove needs a predecessor reference it can't provide in O(1).
4. Skipping sentinel nodes and hand-checking `n == c.head` / `n == c.tail`
   everywhere — reintroduces the special-casing sentinels exist to remove.
5. Mixing up which end is MRU vs LRU mid-implementation — compiles fine,
   inverts cache behavior silently.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: TTL eviction in addition to LRU? -> store an expiry per node; lazy
   check-and-evict on access, or a secondary min-heap keyed by expiry.
Q: LFU instead of LRU (LC 460)? -> frequency counter per key + a doubly
   linked list PER frequency bucket, plus a pointer to the current min
   frequency.
Q: Thread safety? -> one coarse-grained lock around Get/Put; the whole
   point of O(1) ops is the critical section is already tiny.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 460  LFU Cache
    LC 705  Design HashSet     — the map half in isolation
    LC 641  Design Circular Deque — doubly linked list, no map
================================================================================
*/

type dNode struct {
	key, val   int
	prev, next *dNode
}

// LRUCache is the interview answer: doubly linked list + hashmap. O(1) Get/Put.
type LRUCache struct {
	capacity   int
	cache      map[int]*dNode
	head, tail *dNode // sentinels
}

func Constructor(capacity int) LRUCache {
	head, tail := &dNode{}, &dNode{}
	head.next = tail
	tail.prev = head
	return LRUCache{
		capacity: capacity,
		cache:    make(map[int]*dNode, capacity),
		head:     head,
		tail:     tail,
	}
}

// remove unlinks n from wherever it currently sits — O(1), since n carries
// its own prev/next (this is exactly why the list must be DOUBLY linked).
func (c *LRUCache) remove(n *dNode) {
	n.prev.next = n.next
	n.next.prev = n.prev
}

// insertFront splices n in right after the head sentinel — "most recent."
func (c *LRUCache) insertFront(n *dNode) {
	n.prev = c.head
	n.next = c.head.next
	c.head.next.prev = n
	c.head.next = n
}

func (c *LRUCache) Get(key int) int {
	n, ok := c.cache[key]
	if !ok {
		return -1
	}
	c.remove(n)
	c.insertFront(n) // touching promotes to MRU
	return n.val
}

func (c *LRUCache) Put(key, value int) {
	if n, ok := c.cache[key]; ok {
		n.val = value
		c.remove(n)
		c.insertFront(n)
		return
	}
	if len(c.cache) == c.capacity {
		lru := c.tail.prev // node just before the tail sentinel
		c.remove(lru)
		delete(c.cache, lru.key) // evict from BOTH structures
	}
	n := &dNode{key: key, val: value}
	c.cache[key] = n
	c.insertFront(n)
}

// ------------------------------------------------------------------------
// Alternatives / oracles.
// ------------------------------------------------------------------------

// NaiveLRUCache: map + slice, O(n) per op via linear scan/shift. Priced
// on purpose to demonstrate what the O(1) follow-up rules out.
type NaiveLRUCache struct {
	capacity int
	values   map[int]int
	order    []int // front = LRU, back = MRU
}

func NewNaiveLRUCache(capacity int) *NaiveLRUCache {
	return &NaiveLRUCache{capacity: capacity, values: make(map[int]int)}
}

func (c *NaiveLRUCache) removeFromOrder(key int) {
	for i, k := range c.order { // O(n) scan
		if k == key {
			c.order = append(c.order[:i], c.order[i+1:]...) // O(n) shift
			return
		}
	}
}

func (c *NaiveLRUCache) Get(key int) int {
	v, ok := c.values[key]
	if !ok {
		return -1
	}
	c.removeFromOrder(key)
	c.order = append(c.order, key)
	return v
}

func (c *NaiveLRUCache) Put(key, value int) {
	if _, ok := c.values[key]; ok {
		c.removeFromOrder(key)
	} else if len(c.values) == c.capacity {
		lruKey := c.order[0]
		c.order = c.order[1:] // O(n) shift
		delete(c.values, lruKey)
	}
	c.values[key] = value
	c.order = append(c.order, key)
}

func main() {
	allOK := true

	// ------------------------------------------------------------------
	// Correctness: LeetCode's canonical example.
	// ------------------------------------------------------------------
	fmt.Println("--- correctness: LeetCode canonical example ---")
	cache := Constructor(2)
	cache.Put(1, 1)
	cache.Put(2, 2)
	got := []int{
		cache.Get(1),
	}
	cache.Put(3, 3)
	got = append(got, cache.Get(2))
	cache.Put(4, 4)
	got = append(got, cache.Get(1), cache.Get(3), cache.Get(4))
	want := []int{1, -1, -1, 3, 4}
	ok := equalInts(got, want)
	allOK = allOK && ok
	fmt.Printf("%s  got=%v want=%v\n", status(ok), got, want)

	// ------------------------------------------------------------------
	// get-promotes-to-MRU, put-on-existing-key updates-and-promotes.
	// ------------------------------------------------------------------
	fmt.Println("\n--- Get promotes to MRU; Put on existing key updates AND promotes ---")
	c := Constructor(2)
	c.Put(1, 1)
	c.Put(2, 2)
	c.Get(1) // promote 1
	c.Put(3, 3) // evicts 2, not 1
	ok = c.Get(2) == -1 && c.Get(1) == 1 && c.Get(3) == 3
	allOK = allOK && ok
	fmt.Printf("%s  Get(1) before Put(3,3) saved key 1 from eviction\n", status(ok))

	c2 := Constructor(2)
	c2.Put(1, 1)
	c2.Put(2, 2)
	c2.Put(1, 100) // update existing key, must ALSO promote
	c2.Put(3, 3)   // should evict 2, not 1
	ok = c2.Get(2) == -1 && c2.Get(1) == 100 && c2.Get(3) == 3
	allOK = allOK && ok
	fmt.Printf("%s  Put(1,100) on existing key updates value AND promotes\n", status(ok))

	// ------------------------------------------------------------------
	// Capacity=1 edge case.
	// ------------------------------------------------------------------
	fmt.Println("\n--- capacity=1 edge case ---")
	c1 := Constructor(1)
	c1.Put(1, 10)
	ok = c1.Get(1) == 10
	c1.Put(2, 20) // evicts 1 immediately
	ok = ok && c1.Get(1) == -1 && c1.Get(2) == 20
	allOK = allOK && ok
	fmt.Printf("%s  capacity=1: every Put after the first evicts immediately\n", status(ok))

	// ------------------------------------------------------------------
	// Randomized cross-check vs the naive implementation.
	// ------------------------------------------------------------------
	fmt.Println("\n--- randomized cross-check vs naive map+slice oracle (2000 ops, capacity=50) ---")
	rng := rand.New(rand.NewSource(7))
	ours := Constructor(50)
	oracle := NewNaiveLRUCache(50)
	mismatch := false
	for i := 0; i < 2000; i++ {
		key := rng.Intn(100)
		if rng.Float64() < 0.5 {
			if ours.Get(key) != oracle.Get(key) {
				mismatch = true
			}
		} else {
			val := rng.Intn(100000)
			ours.Put(key, val)
			oracle.Put(key, val)
		}
	}
	allOK = allOK && !mismatch
	fmt.Printf("%s  2000 randomized ops, no mismatch vs naive oracle\n", status(!mismatch))

	// ------------------------------------------------------------------
	// BENCHMARK — O(1) linked+hashmap vs O(n) naive map+slice, as cache
	// size grows. Real measured numbers.
	// ------------------------------------------------------------------
	fmt.Println("\n--- benchmark: O(1) linked+hashmap vs O(n) naive map+slice ---")
	fmt.Printf("  %10s %8s %22s %18s %10s\n", "capacity", "ops", "linked+hashmap", "naive slice", "slowdown")
	for _, capacity := range []int{100, 500, 2000} {
		nOps := 4000
		type op struct {
			isGet bool
			k, v  int
		}
		r := rand.New(rand.NewSource(1))
		ops := make([]op, nOps)
		for i := range ops {
			ops[i] = op{isGet: r.Float64() < 0.3, k: r.Intn(capacity * 2), v: r.Intn(100000)}
		}

		fast := Constructor(capacity)
		t0 := time.Now()
		for _, o := range ops {
			if o.isGet {
				fast.Get(o.k)
			} else {
				fast.Put(o.k, o.v)
			}
		}
		fastDur := time.Since(t0)

		slow := NewNaiveLRUCache(capacity)
		t0 = time.Now()
		for _, o := range ops {
			if o.isGet {
				slow.Get(o.k)
			} else {
				slow.Put(o.k, o.v)
			}
		}
		slowDur := time.Since(t0)

		slowdown := float64(slowDur) / float64(fastDur)
		fmt.Printf("  %10d %8d %22v %18v %9.1fx\n", capacity, nOps, fastDur, slowDur, slowdown)
	}

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}

func equalInts(a, b []int) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}
