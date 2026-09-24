"""
================================================================================
QUESTION · LeetCode 355 · Design Twitter                              [Medium]
https://leetcode.com/problems/design-twitter/
================================================================================

Design a simplified version of Twitter where users can post tweets, follow/
unfollow another user, and is able to see the 10 most recent tweet IDs in the
user's news feed.

Implement the `Twitter` class:

- `Twitter()` — initializes the object.
- `void postTweet(int userId, int tweetId)` — composes a new tweet with ID
  `tweetId` by the user `userId`. Each call to this function will be made
  with a UNIQUE `tweetId`.
- `List<Integer> getNewsFeed(int userId)` — retrieves the 10 most recent
  tweet IDs in the user's news feed. Each item in the news feed must be
  posted by users the user follows OR by the user themself. Tweets must be
  ordered from most recent to least recent.
- `void follow(int followerId, int followeeId)` — the user with ID
  `followerId` started following the user with ID `followeeId`.
- `void unfollow(int followerId, int followeeId)` — the user with ID
  `followerId` started NOT following the user with ID `followeeId`.

Example:
    Input:
        ["Twitter", "postTweet", "getNewsFeed", "follow", "postTweet",
         "getNewsFeed", "unfollow", "getNewsFeed"]
        [[], [1, 5], [1], [1, 2], [2, 6], [1], [1, 2], [1]]
    Output:
        [null, null, [5], null, null, [6, 5], null, [5]]
    Explanation:
        Twitter twitter = new Twitter();
        twitter.postTweet(1, 5);        // user 1 posts tweet 5
        twitter.getNewsFeed(1);         // -> [5]
        twitter.follow(1, 2);           // user 1 follows user 2
        twitter.postTweet(2, 6);        // user 2 posts tweet 6
        twitter.getNewsFeed(1);         // -> [6, 5] (6 is more recent)
        twitter.unfollow(1, 2);         // user 1 unfollows user 2
        twitter.getNewsFeed(1);         // -> [5]

Constraints:
    1 <= userId, followerId, followeeId <= 500
    0 <= tweetId <= 10^4
    All the tweets have UNIQUE ids.
    At most 3 * 10^4 calls will be made to postTweet, getNewsFeed, follow,
    and unfollow.
"""

from typing import List


class Twitter:
    def __init__(self):
        # YOUR CODE HERE
        pass

    def postTweet(self, userId: int, tweetId: int) -> None:
        # YOUR CODE HERE
        pass

    def getNewsFeed(self, userId: int) -> List[int]:
        # YOUR CODE HERE
        pass

    def follow(self, followerId: int, followeeId: int) -> None:
        # YOUR CODE HERE
        pass

    def unfollow(self, followerId: int, followeeId: int) -> None:
        # YOUR CODE HERE
        pass


def run_tests():
    tw = Twitter()
    tw.postTweet(1, 5)
    assert tw.getNewsFeed(1) == [5]
    tw.follow(1, 2)
    tw.postTweet(2, 6)
    assert tw.getNewsFeed(1) == [6, 5]
    tw.unfollow(1, 2)
    assert tw.getNewsFeed(1) == [5]

    # more-than-10 tweets: only the 10 most recent
    tw2 = Twitter()
    for t in range(15):
        tw2.postTweet(1, t)
    assert tw2.getNewsFeed(1) == list(range(14, 4, -1))

    # self-follow is not required to be blocked; user always sees own tweets
    tw3 = Twitter()
    tw3.postTweet(1, 100)
    tw3.postTweet(2, 200)
    assert tw3.getNewsFeed(1) == [100]
    tw3.follow(1, 2)
    assert set(tw3.getNewsFeed(1)) == {100, 200}

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
