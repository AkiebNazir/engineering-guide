"""
FOUNDATION LEVEL 03 - Repeated fields: protobuf's lists
========================================================
`repeated` is the only collection keyword you need for sequences. It turns a
field into a list of that type, and it works with scalars and with messages.

The interesting part is what happens on the wire, because protobuf has TWO
different encodings for repeated data and picks one for you:
  * repeated NUMBERS are "packed" - one tag, one length, then all the values
    back to back. The tag is paid once for the whole list.
  * repeated STRINGS, BYTES and MESSAGES are not packable - each element gets
    its own tag, because each already needs its own length anyway.
You never choose; proto3 does the right thing. But knowing which is which
explains why a list of 1000 ints is dramatically cheaper than a list of 1000
tiny messages.

You will learn
  * declaring and filling `repeated` fields: append, extend, slicing, del
  * that a repeated field is never "null" - an empty list is the only empty state
  * packed vs unpacked encoding, measured on the same data
  * that repeated MESSAGE elements repeat their tag once per element
  * that order is preserved exactly, and duplicates are allowed

Run it   python 03_repeated_fields.py
"""
import l03_repeated_pb2 as pb

if __name__ == "__main__":
    print("== 1. filling repeated fields ==")
    playlist = pb.Playlist(name="Deep Focus")
    # Repeated scalar fields behave like a Python list, with one exception:
    # you cannot ASSIGN to them (`playlist.tags = [...]` raises), because the
    # message owns the container. You mutate it in place instead.
    playlist.tags.append("instrumental")
    playlist.tags.extend(["long", "no-vocals"])
    playlist.ratings.extend([5, 4, 5, 5, 3])
    # Repeated MESSAGE fields get .add(), which builds the element in place
    # and returns it so you can fill it.
    playlist.tracks.add(title="Aqueous Transmission", seconds=447)
    playlist.tracks.add(title="Weightless", seconds=488)

    print(f"  name    : {playlist.name!r}")
    print(f"  tags    : {list(playlist.tags)}")
    print(f"  ratings : {list(playlist.ratings)}")
    print(f"  tracks  : {[(t.title, t.seconds) for t in playlist.tracks]}")
    assert len(playlist.tracks) == 2 and len(playlist.ratings) == 5

    try:
        playlist.tags = ["nope"]
        raise AssertionError("expected direct assignment to be rejected")
    except AttributeError:
        print("  playlist.tags = [...] -> AttributeError (mutate in place instead)")

    print("\n== 2. list operations behave as you expect ==")
    print(f"  tags[0]          -> {playlist.tags[0]!r}")
    print(f"  tags[-1]         -> {playlist.tags[-1]!r}")
    print(f"  len(ratings)     -> {len(playlist.ratings)}")
    print(f"  5 in ratings     -> {5 in playlist.ratings}")
    del playlist.tags[1]
    print(f"  after del tags[1]-> {list(playlist.tags)}")
    assert list(playlist.tags) == ["instrumental", "no-vocals"]
    # Order is preserved exactly and duplicates are kept - a repeated field is
    # a LIST, not a set. Nothing is sorted or de-duplicated for you.
    assert list(playlist.ratings) == [5, 4, 5, 5, 3]

    print("\n== 3. there is no 'null list' ==")
    # An unset repeated field is simply empty, and costs zero bytes. There is
    # no way to distinguish "no tags" from "an empty list of tags", and no
    # need to: they mean the same thing. This removes a whole class of bug.
    empty = pb.Playlist(name="x")
    print(f"  unset repeated field : {list(empty.tags)} , len {len(empty.tags)}")
    assert list(empty.tags) == [] and len(empty.SerializeToString()) == 3  # just name

    print("\n== 4. packed (numbers) vs unpacked (strings/messages) ==")
    # Encode ONLY the ratings, then ONLY the tags, so the sizes are comparable.
    nums = pb.Playlist()
    nums.ratings.extend([5, 4, 5, 5, 3])
    packed = nums.SerializeToString()
    print(f"  repeated int32 [5,4,5,5,3] -> {len(packed)} bytes: {packed.hex()}")
    print("    1a = 'field 3, length-delimited'; 05 = five bytes follow; then 05 04 05 05 03.")
    print("    ONE tag for the whole list - that is what 'packed' means.")
    assert packed.hex() == "1a050504050503"

    strs = pb.Playlist()
    strs.tags.extend(["aa", "bb", "cc"])
    unpacked = strs.SerializeToString()
    print(f"\n  repeated string [aa,bb,cc] -> {len(unpacked)} bytes: {unpacked.hex()}")
    print("    12 02 6161 | 12 02 6262 | 12 02 6363  - the tag 0x12 repeats per element.")
    assert unpacked.hex() == "120261611202626212026363"

    msgs = pb.Playlist()
    msgs.tracks.add(title="a", seconds=1)
    msgs.tracks.add(title="b", seconds=2)
    print(f"\n  repeated Track (2 elements) -> {len(msgs.SerializeToString())} bytes: "
          f"{msgs.SerializeToString().hex()}")
    print("    22 05 <track> | 22 05 <track>  - same story: one tag + one length each.")

    # The practical consequence, measured: 100 small numbers vs 100 small messages.
    many_nums, many_msgs = pb.Playlist(), pb.Playlist()
    many_nums.ratings.extend(range(100))
    for i in range(100):
        many_msgs.tracks.add(seconds=i)
    n, m = len(many_nums.SerializeToString()), len(many_msgs.SerializeToString())
    print(f"\n  100 packed int32s      : {n:>3} bytes  (~{n / 100:.2f} bytes/element)")
    print(f"  100 one-field messages : {m:>3} bytes  (~{m / 100:.2f} bytes/element)")
    print("  => prefer repeated scalars over repeated wrapper messages in hot paths.")
    assert n < m

    print("\n== 5. round trip ==")
    data = playlist.SerializeToString()
    back = pb.Playlist()
    back.ParseFromString(data)
    assert back == playlist
    assert [t.title for t in back.tracks] == ["Aqueous Transmission", "Weightless"]
    print(f"  {len(data)} bytes -> decoded {len(back.tracks)} tracks, "
          f"{len(back.ratings)} ratings, order intact")

    print("\nOK")
