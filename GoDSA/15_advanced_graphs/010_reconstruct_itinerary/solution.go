package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 332 · Reconstruct Itinerary                         [Hard]
https://leetcode.com/problems/reconstruct-itinerary/
================================================================================

PROBLEM
-------
You are given a list of airline tickets where tickets[i] = [fromi, toi]
represent the departure and the arrival airports of one flight. Reconstruct
the itinerary in order and return it.

All of the tickets belong to a man who departs from "JFK", thus, the
itinerary must begin with "JFK". If there are multiple valid itineraries,
you should return the itinerary that has the smallest LEXICAL order when
read as a single string.

For example, the itinerary ["JFK", "LGA"] has a smaller lexical order than
["JFK", "LGB"].

You may assume all tickets form at least one valid itinerary. You must use
ALL the tickets exactly once.


EXAMPLES
--------
Example 1:
    Input:  tickets = [["MUC","LHR"],["JFK","MUC"],["SFO","SJC"],["LHR","SFO"]]
    Output: ["JFK","MUC","LHR","SFO","SJC"]

Example 2:
    Input:  tickets = [["JFK","SFO"],["JFK","ATL"],["SFO","ATL"],
                       ["ATL","JFK"],["ATL","SFO"]]
    Output: ["JFK","ATL","JFK","SFO","ATL","SFO"]
    Explanation: Another possible reconstruction is
    ["JFK","SFO","ATL","JFK","ATL","SFO"] but it is larger lexical order.


CONSTRAINTS
-----------
    1 <= tickets.length <= 300
    tickets[i].length == 2
    fromi.length == 3
    toi.length == 3
    fromi and toi consist of uppercase English letters.
    fromi != toi


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Use every ticket exactly once" means visiting every EDGE exactly once,
not every node -- this is an EULERIAN PATH, not a topological order (topic
guide Part 7's closing note). The classic algorithm is Hierholzer's:
DFS greedily, always picking the LEXICALLY SMALLEST unused outgoing edge,
until you hit a dead end (no more unused edges from the current city) --
then that dead-end city IS the last stop in a valid full circuit, and it
gets prepended to the result. This "prepend at the dead end" step is the
part that makes naive greedy DFS wrong on its own (see progressive hints).

PROGRESSIVE HINTS
------------------
Hint 1: Sort each city's list of destinations so ties break
        lexicographically smallest first.
Hint 2: A GREEDY DFS that always takes the smallest available edge can get
        stuck at a dead end that ISN'T the true final destination, having
        used up tickets a valid full itinerary still needed. Try
        constructing a small example where greedy-and-stop fails.
Hint 3: Hierholzer's algorithm: DFS as far as possible, and only APPEND a
        city to the result once you can go NO FURTHER from it (a dead
        end). The result built this way comes out BACKWARDS -- reverse it
        at the end.
Hint 4: Implement iteratively with an explicit stack, not recursion --
        with up to 300 tickets, a chain-shaped itinerary could exceed
        Python's recursion limit.

COMPLEXITY TARGET
------------------
    Time:  O(E log E) -- E tickets, dominated by sorting each city's
           destination list
    Space: O(E)
================================================================================
*/

func main() {
	fmt.Println("Solution for Reconstruct Itinerary not implemented yet")
}
