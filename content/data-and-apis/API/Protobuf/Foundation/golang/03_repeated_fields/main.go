/*
FOUNDATION LEVEL 03 - Repeated fields: protobuf's lists
========================================================
`repeated` is the only collection keyword you need for sequences. It turns a
field into a list of that type, and it works with scalars and with messages.
In Go a repeated field is simply a slice, so everything you already know
about slices applies.

The interesting part is what happens on the wire, because protobuf has TWO
different encodings for repeated data and picks one for you:

  - repeated NUMBERS are "packed" - one tag, one length, then all the values
    back to back. The tag is paid once for the whole list.
  - repeated STRINGS, BYTES and MESSAGES are not packable - each element gets
    its own tag, because each already needs its own length anyway.

You never choose; proto3 does the right thing. But knowing which is which
explains why a list of 1000 ints is dramatically cheaper than a list of 1000
tiny messages.

You will learn
  - declaring and filling `repeated` fields, which are Go slices
  - that a repeated field is never "null" - an empty slice is the only empty state
  - packed vs unpacked encoding, measured on the same data
  - that repeated MESSAGE elements repeat their tag once per element
  - that order is preserved exactly, and duplicates are allowed

Run it   go run ./Protobuf/Foundation/golang/03_repeated_fields
*/
package main

import (
	"fmt"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l03"
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func mustMarshal(m proto.Message) []byte {
	data, err := proto.Marshal(m)
	must(err == nil, "marshal")
	return data
}

func main() {
	fmt.Println("== 1. filling repeated fields ==")
	// A repeated field is a plain Go slice: []string, []int32, []*l03.Track.
	// Nothing special is needed to build one.
	playlist := &l03.Playlist{
		Name: "Deep Focus",
		Tags: []string{"instrumental"},
	}
	playlist.Tags = append(playlist.Tags, "long", "no-vocals")
	playlist.Ratings = append(playlist.Ratings, 5, 4, 5, 5, 3)
	// Repeated MESSAGE fields are slices of POINTERS, so each element is built
	// with & like any other message.
	playlist.Tracks = append(playlist.Tracks,
		&l03.Track{Title: "Aqueous Transmission", Seconds: 447},
		&l03.Track{Title: "Weightless", Seconds: 488},
	)

	fmt.Printf("  Name    : %q\n", playlist.GetName())
	fmt.Printf("  Tags    : %v\n", playlist.GetTags())
	fmt.Printf("  Ratings : %v\n", playlist.GetRatings())
	fmt.Print("  Tracks  : ")
	for i, track := range playlist.GetTracks() {
		if i > 0 {
			fmt.Print(", ")
		}
		fmt.Printf("%s (%ds)", track.GetTitle(), track.GetSeconds())
	}
	fmt.Println()
	must(len(playlist.GetTracks()) == 2 && len(playlist.GetRatings()) == 5, "element counts")

	fmt.Println("\n== 2. they are slices, so slice operations work ==")
	fmt.Printf("  Tags[0]            -> %q\n", playlist.GetTags()[0])
	fmt.Printf("  len(Ratings)       -> %d\n", len(playlist.GetRatings()))
	// Deleting the element at index 1, the usual Go way.
	playlist.Tags = append(playlist.Tags[:1], playlist.Tags[2:]...)
	fmt.Printf("  after deleting [1] -> %v\n", playlist.GetTags())
	must(len(playlist.GetTags()) == 2 && playlist.GetTags()[1] == "no-vocals", "deletion")
	// Order is preserved exactly and duplicates are kept - a repeated field is
	// a LIST, not a set. Nothing is sorted or de-duplicated for you.
	must(fmt.Sprint(playlist.GetRatings()) == "[5 4 5 5 3]", "order and duplicates preserved")
	fmt.Println("  order is exact and duplicates are kept: it is a list, not a set")

	fmt.Println("\n== 3. there is no 'null list' ==")
	// An unset repeated field is a nil slice, which behaves identically to an
	// empty one for len/range/append, and costs zero bytes. There is no way to
	// distinguish "no tags" from "an empty list of tags", and no need to.
	empty := &l03.Playlist{Name: "x"}
	fmt.Printf("  unset repeated field: %v , len %d , nil? %v\n",
		empty.GetTags(), len(empty.GetTags()), empty.GetTags() == nil)
	fmt.Println("  ranging over it is safe, and len() is 0 - a nil slice needs no guard")
	must(len(mustMarshal(empty)) == 3, "only the name is encoded") // tag+len+"x"

	fmt.Println("\n== 4. packed (numbers) vs unpacked (strings/messages) ==")
	// Encode ONLY the ratings, then ONLY the tags, so the sizes are comparable.
	nums := &l03.Playlist{Ratings: []int32{5, 4, 5, 5, 3}}
	packed := mustMarshal(nums)
	fmt.Printf("  repeated int32 [5 4 5 5 3] -> %d bytes: %x\n", len(packed), packed)
	fmt.Println("    1a = 'field 3, length-delimited'; 05 = five bytes follow; then 05 04 05 05 03.")
	fmt.Println("    ONE tag for the whole list - that is what 'packed' means.")
	must(fmt.Sprintf("%x", packed) == "1a050504050503", "packed layout")

	strs := &l03.Playlist{Tags: []string{"aa", "bb", "cc"}}
	unpacked := mustMarshal(strs)
	fmt.Printf("\n  repeated string [aa bb cc] -> %d bytes: %x\n", len(unpacked), unpacked)
	fmt.Println("    12 02 6161 | 12 02 6262 | 12 02 6363  - the tag 0x12 repeats per element.")
	must(fmt.Sprintf("%x", unpacked) == "120261611202626212026363", "unpacked layout")

	msgs := &l03.Playlist{Tracks: []*l03.Track{{Title: "a", Seconds: 1}, {Title: "b", Seconds: 2}}}
	msgBytes := mustMarshal(msgs)
	fmt.Printf("\n  repeated Track (2 elements) -> %d bytes: %x\n", len(msgBytes), msgBytes)
	fmt.Println("    22 05 <track> | 22 05 <track>  - same story: one tag + one length each.")

	// The practical consequence, measured: 100 small numbers vs 100 small messages.
	manyNums, manyMsgs := &l03.Playlist{}, &l03.Playlist{}
	for i := int32(0); i < 100; i++ {
		manyNums.Ratings = append(manyNums.Ratings, i)
		manyMsgs.Tracks = append(manyMsgs.Tracks, &l03.Track{Seconds: i})
	}
	n, m := len(mustMarshal(manyNums)), len(mustMarshal(manyMsgs))
	fmt.Printf("\n  100 packed int32s      : %3d bytes  (~%.2f bytes/element)\n", n, float64(n)/100)
	fmt.Printf("  100 one-field messages : %3d bytes  (~%.2f bytes/element)\n", m, float64(m)/100)
	fmt.Println("  => prefer repeated scalars over repeated wrapper messages in hot paths.")
	must(n < m, "packed scalars beat wrapper messages")

	fmt.Println("\n== 5. round trip ==")
	data := mustMarshal(playlist)
	back := &l03.Playlist{}
	must(proto.Unmarshal(data, back) == nil, "unmarshal")
	must(proto.Equal(back, playlist), "repeated values survive encode/decode exactly")
	must(back.GetTracks()[0].GetTitle() == "Aqueous Transmission", "first track, in order")
	fmt.Printf("  %d bytes -> decoded %d tracks, %d ratings, order intact\n",
		len(data), len(back.GetTracks()), len(back.GetRatings()))

	fmt.Println("\nOK")
}
