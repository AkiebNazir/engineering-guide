"""
================================================================================
SOLUTION · LeetCode 355 · Design Twitter                              [Medium]
https://leetcode.com/problems/design-twitter/
================================================================================

THE CORE IDEA
--------------
`getNewsFeed` is "merge the k most-recent-first tweet lists of k users (the
caller + their followees), take the top 10 overall." That is EXACTLY the
merge-k-sorted-lists pattern from _TOPIC_GUIDE.md §6 (also fully developed in
`PyDSA/08_linked_list/014_merge_k_sorted_lists_solution.py`) — each user's own
tweets are already sorted by post order (we append with an increasing global
timestamp), so the news feed is a k-way merge stopped after 10 items.

The key optimization that makes this fast: you never need MORE than the last
10 tweets from any single followee, no matter how many tweets they've ever
posted, because the global answer only keeps 10 total. Pulling only each
list's tail before merging bounds the candidate pool to `10 * (1 + num
followees)` regardless of total tweet history size.

================================================================================
APPROACH 0 · Collect every tweet from every followee, sort, slice (brute)
================================================================================
On every `getNewsFeed` call: gather ALL tweets ever posted by the user and
everyone they follow into one list, sort by timestamp descending, take the
first 10.
    Time:  O(T log T) per call, where T = total tweets across all followed
           users (grows UNBOUNDED as the platform accumulates history —
           this is the trap: cost grows with total tweet count, not with
           the size of the answer).
    Space: O(T) to materialize the merged list.
Correct, and fine for a toy test, but pathological in practice: a user
followed by someone who joined the site years ago and has 50,000 tweets
pays O(50,000 log 50,000) on every single feed refresh even though only the
newest 10 of those 50,000 could ever matter.

================================================================================
APPROACH 1 · k-way heap merge of each followee's tail ✅ (the answer)
================================================================================
Store each user's tweets as a list of `(timestamp, tweetId)` appended in
post order (so it's naturally sorted ascending by time — no per-post sort
needed). On `getNewsFeed`:
  1. For the caller + each followee, take only their LAST 10 tweets (a
     Python slice `lst[-10:]`, O(10) per user, not O(len(lst))).
  2. Feed all those candidates (at most `10 * (1 + num followees)` total)
     through `heapq.nlargest(10, candidates, key=lambda t: t[0])` — this
     internally runs the size-10 max-heap sweep from _TOPIC_GUIDE.md §3.

    Time:  postTweet O(1) amortized (list append).
           follow/unfollow O(1) amortized (set add/discard).
           getNewsFeed O(F * log 10) where F = number of followees (bounded
           work per followee: O(10) slice + O(log 10) heap consideration —
           effectively O(F), completely independent of total tweet history.
    Space: O(F) candidates materialized per call, O(1) extra beyond that.

================================================================================
APPROACH 2 · True incremental k-way merge (heap of "cursors", one per list)
================================================================================
Instead of pre-slicing to the last 10 then re-sorting, run the merge-k-lists
mechanism directly: push one cursor per candidate list (pointing at its most
recent tweet) into a max-heap keyed by timestamp, then repeatedly pop the
global max and push that list's next-older tweet, stopping after 10 pops or
heap-empty. Same asymptotics as Approach 1 for this problem's exact shape (10
is a fixed, tiny constant) — worth naming because it generalizes if the "top
N" limit were a runtime parameter instead of a hardcoded 10, or if lists were
too large to slice cheaply (e.g. tweets stored on disk / paginated).

--------------------------------------------------------------------------------
STEP BY STEP TRACE
--------------------------------------------------------------------------------
postTweet(1, 5)   -> tweets[1] = [(0, 5)]                    (global clock: 0)
getNewsFeed(1)    -> followees of 1 = {1} (self only)
                     candidates = tail of tweets[1] = [(0,5)]
                     nlargest(10, ...) by time -> [(0,5)] -> [5]   matches: [5]

follow(1, 2)      -> follows[1] = {2}
postTweet(2, 6)   -> tweets[2] = [(1, 6)]                    (global clock: 1)
getNewsFeed(1)    -> followees of 1 = {1, 2}
                     candidates = tail(tweets[1]) + tail(tweets[2])
                                = [(0,5)] + [(1,6)] = [(0,5),(1,6)]
                     nlargest(10, key=time) -> sorted desc by time:
                       [(1,6), (0,5)] -> tweetIds [6, 5]      matches: [6, 5]

unfollow(1, 2)    -> follows[1] = {} (only self remains implicitly)
getNewsFeed(1)    -> candidates = tail(tweets[1]) only = [(0,5)]
                     -> [5]                                    matches: [5]

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Operation                        | Approach 0 (brute) | Approach 1 ✅ | Mutates any input? |
|------------------------------------|---------------------|-----------------|----------------------|
| postTweet                          | O(1)                | O(1) amortized  | No (owns its own state) |
| follow / unfollow                  | O(1)                | O(1) amortized  | No                   |
| getNewsFeed                        | O(T log T), T = all history | O(F log 10), F = followee count | No |
| Space (per getNewsFeed call)       | O(T)                | O(F)            | —                    |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- User with no tweets and no followees: `getNewsFeed` returns `[]` —
  candidates list is empty, `nlargest` on an empty iterable returns `[]`.
- Fewer than 10 total candidate tweets exist: `nlargest(10, ...)` gracefully
  returns however many exist, no padding or error.
- User follows themselves: harmless — `followerId == followeeId` just adds
  userId to its own follow set; since the user's own tweets are already
  included unconditionally in `getNewsFeed`, this is a no-op in effect (not
  explicitly forbidden by the constraints, so must not crash).
- `unfollow` called on a pair that was never following: must be a silent
  no-op — using `set.discard` (not `set.remove`) avoids a `KeyError`.
- Exactly 10 candidate tweets across all sources with ties on timestamp:
  can't actually happen here since timestamps come from one strictly
  increasing global counter (unique tweetIds are handled separately by the
  problem's guarantee) — no tie-breaking is needed, but if two events could
  share a timestamp, the tiebreaker would need to be the tweetId or
  insertion order, same lesson as problem 003's tuple-comparison mistake.
- A followee with a very long tweet history (thousands of posts): Approach
  1's `[-10:]` slice touches only the last 10 entries of that user's list,
  not the whole history — this is the whole point of the optimization, see
  the runtime demo below for a measured proof.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Re-sorting or re-scanning a user's ENTIRE tweet history on every
   `getNewsFeed` call instead of slicing just the tail — this is exactly
   Approach 0's trap: it "works" on small test inputs and silently becomes
   the dominant cost once any single user accumulates a large history.
2. Forgetting the caller always sees their OWN tweets in their feed, even
   if they don't explicitly follow themselves — `getNewsFeed` must union
   `{userId}` with `follows[userId]`, not just iterate `follows[userId]`.
3. Using `set.remove` instead of `set.discard` in `unfollow` — raises
   `KeyError` if the pair wasn't following, when the problem implies this
   should be a harmless no-op.
4. Using wall-clock time (`time.time()`) instead of a monotonically
   increasing integer counter for ordering — floating-point timestamps from
   rapid-fire calls in a tight loop can collide or, worse, are not
   guaranteed strictly increasing across machines/threads; a single
   `itertools.count()`-style incrementing int is simpler and exact.
5. Building one global heap of ALL tweets across ALL users up front instead
   of per-user lists — makes `postTweet` cheap but makes filtering to "just
   this user's followees" during `getNewsFeed` require scanning the whole
   heap (no O(1) way to ask a heap "give me only entries matching this
   predicate"), defeating the purpose of a heap.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if the feed size (10) needs to become a runtime parameter N?" —
  Approach 1 generalizes by slicing `[-N:]` per list and calling
  `nlargest(N, ...)`; Approach 2's incremental cursor-heap becomes
  preferable once N is large, since it never over-fetches beyond exactly N
  pops.
- "What if a single user follows 10,000 people?" — Approach 1's
  `getNewsFeed` cost is O(F log 10) = O(F), linear in followee count; at
  that scale you'd typically pre-aggregate/fan-out on write (push each new
  tweet into every follower's precomputed feed cache) to make reads O(1) at
  the cost of more expensive writes — the classic fan-out-on-write vs
  fan-out-on-read tradeoff in real feed systems.
- "How would you support pagination (next 10 older tweets)?" — Approach 2's
  cursor-heap is the natural fit: keep the heap state across calls (or
  reconstruct with an offset) and keep popping instead of stopping at 10.
- "What if tweets can be deleted?" — needs either removing them from the
  per-user list (O(n) scan unless indexed by tweetId) or a lazy-deletion
  tombstone set checked while draining the heap (see _TOPIC_GUIDE.md's
  broader heap-deletion discussion) — plain `heapq` has no O(log n)
  arbitrary delete.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- `PyDSA/08_linked_list/014_merge_k_sorted_lists_solution.py` — the same
  k-way heap merge mechanism, worked through in full for k sorted linked
  lists instead of k per-user tweet lists.
- 12/010 Minimum Interval to Include Each Query — different shape, but also
  uses a heap to avoid re-scanning a growing candidate set per query.
- 12/003 K Closest Points to Origin — same "size-bounded heap merge/filter"
  family, applied to a static array instead of an evolving multi-user store.
================================================================================
"""

import heapq
import random
import time
from typing import List


class Twitter:
    FEED_SIZE = 10

    def __init__(self):
        self._clock = 0
        self._tweets: dict = {}   # userId -> list[(timestamp, tweetId)], ascending
        self._follows: dict = {}  # userId -> set[followeeId]

    def postTweet(self, userId: int, tweetId: int) -> None:
        self._tweets.setdefault(userId, []).append((self._clock, tweetId))
        self._clock += 1

    def getNewsFeed(self, userId: int) -> List[int]:
        followees = self._follows.get(userId, set()) | {userId}
        candidates = []
        for uid in followees:
            candidates.extend(self._tweets.get(uid, [])[-self.FEED_SIZE:])
        top = heapq.nlargest(self.FEED_SIZE, candidates, key=lambda t: t[0])
        return [tweet_id for _, tweet_id in top]

    def follow(self, followerId: int, followeeId: int) -> None:
        self._follows.setdefault(followerId, set()).add(followeeId)

    def unfollow(self, followerId: int, followeeId: int) -> None:
        self._follows.get(followerId, set()).discard(followeeId)


# --------------------------------------------------------------------------
# Baseline for the runtime demo: re-collect + re-sort the FULL history of
# every followee on every getNewsFeed call (Approach 0).
# --------------------------------------------------------------------------
class TwitterFullScan:
    FEED_SIZE = 10

    def __init__(self):
        self._clock = 0
        self._tweets: dict = {}
        self._follows: dict = {}

    def postTweet(self, userId: int, tweetId: int) -> None:
        self._tweets.setdefault(userId, []).append((self._clock, tweetId))
        self._clock += 1

    def getNewsFeed(self, userId: int) -> List[int]:
        followees = self._follows.get(userId, set()) | {userId}
        candidates = []
        for uid in followees:
            candidates.extend(self._tweets.get(uid, []))  # FULL history, no tail slice
        candidates.sort(key=lambda t: t[0], reverse=True)
        return [tweet_id for _, tweet_id in candidates[: self.FEED_SIZE]]

    def follow(self, followerId: int, followeeId: int) -> None:
        self._follows.setdefault(followerId, set()).add(followeeId)

    def unfollow(self, followerId: int, followeeId: int) -> None:
        self._follows.get(followerId, set()).discard(followeeId)


def run_tests():
    tw = Twitter()
    tw.postTweet(1, 5)
    assert tw.getNewsFeed(1) == [5]
    tw.follow(1, 2)
    tw.postTweet(2, 6)
    assert tw.getNewsFeed(1) == [6, 5]
    tw.unfollow(1, 2)
    assert tw.getNewsFeed(1) == [5]

    # more-than-10 tweets: only the 10 most recent, newest first
    tw2 = Twitter()
    for t in range(15):
        tw2.postTweet(1, t)
    assert tw2.getNewsFeed(1) == list(range(14, 4, -1))

    # own tweets always visible even without following self
    tw3 = Twitter()
    tw3.postTweet(1, 100)
    tw3.postTweet(2, 200)
    assert tw3.getNewsFeed(1) == [100]
    tw3.follow(1, 2)
    assert set(tw3.getNewsFeed(1)) == {100, 200}

    # unfollow never-followed pair: silent no-op, no crash
    tw4 = Twitter()
    tw4.unfollow(1, 2)  # must not raise
    assert tw4.getNewsFeed(1) == []

    # self-follow is harmless
    tw5 = Twitter()
    tw5.postTweet(1, 9)
    tw5.follow(1, 1)
    assert tw5.getNewsFeed(1) == [9]

    # cross-check against the full-scan baseline on a randomized scenario
    random.seed(3)
    fast, slow = Twitter(), TwitterFullScan()
    next_tweet_id = 0
    for _ in range(500):
        op = random.choice(["post", "follow", "unfollow", "feed"])
        u1, u2 = random.randint(1, 5), random.randint(1, 5)
        if op == "post":
            fast.postTweet(u1, next_tweet_id)
            slow.postTweet(u1, next_tweet_id)
            next_tweet_id += 1
        elif op == "follow":
            fast.follow(u1, u2)
            slow.follow(u1, u2)
        elif op == "unfollow":
            fast.unfollow(u1, u2)
            slow.unfollow(u1, u2)
        else:
            assert fast.getNewsFeed(u1) == slow.getNewsFeed(u1)

    # --- measured runtime demo: tail-slice heap merge vs full-history scan ---
    # One followee with a huge tweet history; the feed only ever needs the
    # newest 10 of it, no matter how large the history grows.
    heavy_fast, heavy_slow = Twitter(), TwitterFullScan()
    heavy_fast.follow(1, 2)
    heavy_slow.follow(1, 2)
    n_history = 200_000
    for t in range(n_history):
        heavy_fast.postTweet(2, t)
        heavy_slow.postTweet(2, t)

    n_calls = 300
    t0 = time.perf_counter()
    for _ in range(n_calls):
        fast_feed = heavy_fast.getNewsFeed(1)
    fast_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(n_calls):
        slow_feed = heavy_slow.getNewsFeed(1)
    slow_time = time.perf_counter() - t0

    assert fast_feed == slow_feed, "both approaches must agree on the feed"

    print(f"Followee history size={n_history}, {n_calls} getNewsFeed calls (this machine):")
    print(f"  tail-slice + nlargest:  {fast_time*1000:8.2f} ms")
    print(f"  full-history scan+sort: {slow_time*1000:8.2f} ms")
    print(f"  tail-slice is {slow_time / fast_time:.1f}x faster")
    assert fast_time < slow_time, (
        "expected the tail-slice heap merge to beat scanning full history per call"
    )

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
