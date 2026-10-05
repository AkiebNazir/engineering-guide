"""
================================================================================
QUESTION · LeetCode 295 · Find Median from Data Stream                  [Hard]
https://leetcode.com/problems/find-median-from-data-stream/
================================================================================

The median is the middle value in an ordered integer list. If the size of
the list is even, the median is the average of the two middle values.

    - For example, for arr = [2,3,4], the median is 3.
    - For example, for arr = [2,3], the median is (2 + 3) / 2 = 2.5.

Implement the MedianFinder class:
    - MedianFinder()        initializes the object.
    - void addNum(int num)  adds num to the data structure.
    - double findMedian()   returns the median of all elements so far.

Example:
    Input:
        addNum(1)
        addNum(2)
        findMedian()  -> 1.5
        addNum(3)
        findMedian()  -> 2.0

Constraints:
    -10^5 <= num <= 10^5
    There will be at least one element before findMedian is called.
    At most 5 * 10^4 calls total to addNum and findMedian.

Follow up:
    - If all integers in the stream are in the range [0, 100], how would you
      optimize?
    - If 99% of all integers are in the range [0, 100], how would you
      optimize?
"""


class MedianFinder:
    def __init__(self):
        # YOUR CODE HERE
        pass

    def addNum(self, num: int) -> None:
        # YOUR CODE HERE
        pass

    def findMedian(self) -> float:
        # YOUR CODE HERE
        pass


def run_tests():
    mf = MedianFinder()
    mf.addNum(1)
    mf.addNum(2)
    assert mf.findMedian() == 1.5
    mf.addNum(3)
    assert mf.findMedian() == 2.0

    mf2 = MedianFinder()
    for n in [5, 15, 1, 3]:
        mf2.addNum(n)
    # sorted: 1,3,5,15 -> median (3+5)/2 = 4.0
    assert mf2.findMedian() == 4.0

    mf3 = MedianFinder()
    mf3.addNum(-1)
    assert mf3.findMedian() == -1.0
    mf3.addNum(-2)
    assert mf3.findMedian() == -1.5
    mf3.addNum(-3)
    assert mf3.findMedian() == -2.0

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
