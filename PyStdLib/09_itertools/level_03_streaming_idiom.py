"""
LEVEL 03 (core) - Combining chain + islice into a small streaming idiom
===========================================================================
You will learn
  * treating multiple paginated sources as one lazy stream with chain
  * pulling just a "page" out of that stream with islice, without concatenating lists
  * this is how you'd page through several data sources without loading all of them

Run: python level_03_streaming_idiom.py
"""
from itertools import chain, islice


def fetch_page(page_number: int) -> list[int]:
    """Pretend paginated API: each 'page' is 5 numbers, page 1 starts at 1."""
    start = (page_number - 1) * 5 + 1
    return list(range(start, start + 5))


def paged_source(max_pages: int):
    """A single lazy stream over several 'pages', without pre-fetching all of them."""
    for page_number in range(1, max_pages + 1):
        yield from fetch_page(page_number)


if __name__ == "__main__":
    # chain lets three already-fetched pages act like one continuous stream
    page1, page2, page3 = fetch_page(1), fetch_page(2), fetch_page(3)
    stream = chain(page1, page2, page3)
    assert list(stream) == list(range(1, 16))

    # islice pulls exactly the 7 items we want, spanning across page boundaries,
    # without ever building the full concatenated list ourselves
    seven_items = list(islice(paged_source(max_pages=10), 7))
    assert seven_items == [1, 2, 3, 4, 5, 6, 7]

    # skip the first 12 and take the next 3 -- straddles pages 3/4
    middle_slice = list(islice(paged_source(max_pages=10), 12, 15))
    assert middle_slice == [13, 14, 15]

    # combine explicitly: chain two independent generators, then islice the result
    combined_stream = chain(paged_source(max_pages=2), paged_source(max_pages=2))
    first_of_each = list(islice(combined_stream, 0, 20, 5))   # every 5th item = first of each page
    assert first_of_each == [1, 6, 1, 6]   # two independent 2-page streams back to back

    print("OK")
