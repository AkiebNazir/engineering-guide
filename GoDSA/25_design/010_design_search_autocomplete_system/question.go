package main

/*
================================================================================
LeetCode 642 · Design Search Autocomplete System                          [Hard]
https://leetcode.com/problems/design-search-autocomplete-system/
Topic: 25 · Design
================================================================================

PROBLEM
-------
Design a search autocomplete system for a search engine. Users type a
sentence ONE CHARACTER AT A TIME (each character delivered via a separate
`input` call), ending with a special character `'#'`.

Implement the `AutocompleteSystem` class:

    AutocompleteSystem(sentences,
                        times)    Initializes with historical `sentences`
                                  and their corresponding hot-degrees
                                  `times[i]` (how many times sentences[i]
                                  has been searched before).
    input(c) -> list[str]        `c` is a lowercase English letter, ' '
                                  (space), or '#'.
                                  - If `c == '#'`, the CURRENTLY TYPED
                                    sentence is complete: save it to
                                    historical data (increment its
                                    hot-degree by 1, or add it fresh at
                                    hot-degree 1 if never seen before),
                                    reset the typed buffer, and return [].
                                  - Otherwise, append `c` to the currently
                                    typed buffer and return the TOP 3
                                    historical sentences that have this
                                    buffer as a PREFIX, sorted by
                                    hot-degree DESCENDING, ties broken by
                                    ASCII/lexicographic order ASCENDING.
                                    If fewer than 3 match, return all of
                                    them (possibly none).


EXAMPLES
--------
Example 1:
    Input:
        ["AutocompleteSystem", "input", "input", "input", "input"]
        [[["i love you", "island", "iroman", "i love leetcode"],
          [5, 3, 2, 2]],
         ["i"], [" "], ["a"], ["#"]]
    Output:
        [null,
         ["i love you", "island", "i love leetcode"],
         ["i love you", "i love leetcode"],
         [],
         []]

    Explanation:
        sys = AutocompleteSystem(
            ["i love you", "island", "iroman", "i love leetcode"],
            [5, 3, 2, 2])
        sys.input("i")    # prefix "i" matches all 4 sentences; top 3 by
                           # hot-degree: "i love you"(5), "island"(3),
                           # then "iroman"(2) and "i love leetcode"(2) TIE
                           # at 2 -> lexicographic breaks the tie ->
                           # "i love leetcode" < "iroman" -> returns
                           # ["i love you", "island", "i love leetcode"]
        sys.input(" ")    # buffer="i ", matches "i love you"(5),
                           # "i love leetcode"(2) -> both
        sys.input("a")    # buffer="i a", no sentence has this prefix -> []
        sys.input("#")    # buffer "i a" is SAVED as a new sentence at
                           # hot-degree 1, buffer resets -> []


CONSTRAINTS
-----------
    n == sentences.length == times.length
    1 <= n <= 100
    1 <= sentences[i].length <= 100
    1 <= times[i] <= 50
    `c` is a lowercase English letter, a blank space ' ', or '#'.
    Each tested sentence (across all `input` calls before a `#`) will
    have a length in the range [1, 200].
    At most 5000 calls will be made to `input`.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is a design problem around a TRIE, extended past the "does this
prefix exist" question (topic 13's core trie problems) into "give me the
TOP-K completions of this prefix, ranked by a stored score." The
straightforward brute-force approach (scan every historical sentence on
every keystroke, filter by prefix, sort) is honest and simple but does
O(total sentences) work per CHARACTER typed, regardless of how few
sentences actually share that prefix.

The trie-based improvement: at EVERY trie node (i.e. every prefix ever
seen), store a small index — `sentence -> hot_degree` for every complete
sentence that passes through this node — so querying a typed prefix is
just "walk to this node (O(prefix length)), then rank only ITS index"
instead of scanning every sentence in the whole system.


WHAT TO THINK ABOUT
--------------------
1. The system has ONE piece of "live" state across calls: the currently
   typed buffer (and, for the trie approach, the current trie node
   reached by that buffer so far). This state PERSISTS across `input`
   calls until a `'#'` resets it — a common bug treats each `input` call
   as independent.

2. If at any point the typed buffer stops matching ANY historical prefix
   (walked off the trie, or a brute-force scan finds zero candidates),
   ALL subsequent `input` calls (until the next `'#'`) must also return
   `[]` — there is no possible completion for an even-longer version of a
   prefix nothing matches.

3. `'#'` does TWO things: saves the JUST-TYPED buffer as a searched
   sentence (bumping its hot-degree, or creating it at hot-degree 1 if
   new), AND resets the typed-buffer state for the next sentence — get
   the ORDER of these two right (save the OLD buffer before resetting it).

4. Ranking: hot-degree DESCENDING is the primary key, LEXICOGRAPHIC
   ASCENDING is the tiebreaker — sorting by `(-hot_degree, sentence)`
   naturally encodes both directions in one sort key.


PROGRESSIVE HINTS
------------------
Hint 1: Build a trie from the initial `(sentences, times)` pairs. At every
        node along EACH sentence's path, record that sentence's
        hot-degree in a small per-node index (`node.counts[sentence] =
        hot_degree`) — not just at the final/leaf node.

Hint 2: Track the "current node" alongside the "current buffer" as
        instance state. Each non-`'#'` `input(c)` call: move
        `current_node = current_node.children.get(c)` (or `None` if it
        doesn't exist), append `c` to the buffer, then read off
        `current_node.counts` (or `[]` if `current_node is None`), sort by
        `(-hot_degree, sentence)`, return the top 3.

Hint 3: On `'#'`: re-insert the completed buffer into the trie from
        `self.root` (creating any missing nodes, incrementing that
        sentence's count by 1 at every node along the path — including
        newly created ones), THEN reset `current_node = self.root` and
        `buffer = ""`.


COMPLEXITY TARGET
------------------
    input(c), non-'#':  O(1) navigation + O(k log k) for ranking, where
                         k = number of sentences sharing the CURRENT
                         prefix (not the total sentence count)
    input('#'):          O(sentence length) to re-insert
    Space:                O(sum over all sentences of sentence_length^2)
                         worst case (each sentence's hot-degree is stored
                         at every one of its own prefix nodes) — an
                         explicit space/time trade the trie makes.
================================================================================
*/

// TODO: Implement the stub
