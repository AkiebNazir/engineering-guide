"""
LEVEL 01 (basic) - Treating several iterables as one with itertools.chain
=============================================================================
You will learn
  * the problem chain solves: looping over multiple sequences as if they were one
  * chain() doesn't build a combined list -- it's a lazy iterator
  * chain.from_iterable() for when the sequences are already inside one iterable

Run: python level_01_chain_basics.py
"""
from itertools import chain

if __name__ == "__main__":
    morning = ["wake up", "coffee"]
    afternoon = ["lunch", "meetings"]
    evening = ["dinner", "sleep"]

    # chain() lets you loop over all three lists as if they were one sequence,
    # without first copying them into a combined list like morning + afternoon + evening
    combined = chain(morning, afternoon, evening)
    assert list(combined) == ["wake up", "coffee", "lunch", "meetings", "dinner", "sleep"]

    # it's a single-use ITERATOR, not a list -- consuming it drains it
    exhausted = chain([1, 2], [3, 4])
    first_pass = list(exhausted)
    second_pass = list(exhausted)
    assert first_pass == [1, 2, 3, 4]
    assert second_pass == []   # already consumed -- nothing left

    # from_iterable() flattens one level: an iterable OF iterables
    schedule = [morning, afternoon, evening]
    flattened = list(chain.from_iterable(schedule))
    assert flattened == list(chain(morning, afternoon, evening))

    print("OK")
