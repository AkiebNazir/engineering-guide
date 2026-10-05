"""
================================================================================
QUESTION · LeetCode 2013 · Detect Squares                          [Medium]
https://leetcode.com/problems/detect-squares/
================================================================================

You are given a stream of points on the X-Y plane. Design an algorithm
that:
    - Adds new points from the stream into a data structure. Duplicate
      points are allowed and should be treated as separate points.
    - Given a query point, counts the number of ways to choose three
      points from the data structure such that the three points and the
      query point form an axis-aligned square with positive area.

Implement the `DetectSquares` class:
    - `DetectSquares()` Initializes the object with an empty data structure.
    - `void add(int[] point)` Adds a new point `point = [x, y]` to the data
      structure.
    - `int count(int[] point)` Counts the number of ways to form axis-
      aligned squares with point `point = [x, y]` as described above.

Example:
    Input:
        ["DetectSquares", "add", "add", "add", "count", "count", "add", "count"]
        [[], [[3,10]], [[11,2]], [[3,2]], [[11,10]], [[14,8]], [[11,2]], [[11,10]]]
    Output:
        [null, null, null, null, 1, 0, null, 2]

    Explanation:
        DetectSquares detectSquares = new DetectSquares();
        detectSquares.add([3, 10]);
        detectSquares.add([11, 2]);
        detectSquares.add([3, 2]);
        detectSquares.count([11, 10]); // Returns 1: [3,10],[11,2],[3,2],[11,10]
                                         // forms one square.
        detectSquares.count([14, 8]);  // Returns 0: no square found using
                                         // any of the points as described.
        detectSquares.add([11, 2]);    // Duplicate point is allowed.
        detectSquares.count([11, 10]); // Returns 2: two squares found using
                                         // (3,10),(11,2),(3,2),(11,10) and
                                         // ([3,10],[11,2] duplicate,[3,2],
                                         // [11,10]).

Constraints:
    point.length == 2
    0 <= x, y <= 1000
    At most 3000 calls in total will be made to add and count.
================================================================================
"""


class DetectSquares:
    def __init__(self):
        # YOUR CODE HERE
        pass

    def add(self, point: list[int]) -> None:
        # YOUR CODE HERE
        pass

    def count(self, point: list[int]) -> int:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    pass


if __name__ == "__main__":
    run_tests()
