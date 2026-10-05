/*
LAB 01 (basic) - Protobuf in Go: marshal, unmarshal, getters, clone
===================================================================
You will learn
  - generated types are pointers to structs (*pb.User); NEVER copy them by value
    (they contain internal state and a no-copy lock; `go vet` will warn you)
  - proto.Marshal / proto.Unmarshal, and reading the raw bytes
  - GETTERS are nil-safe:  u.GetAddress().GetCity()  never panics, even if Address is nil
  - proto3 defaults and PRESENCE:  optional scalars are pointers (*int32): nil means "not set"
  - proto.Clone (deep copy), proto.Equal (NOT ==), proto.Merge, proto.Size
  - unknown fields survive a round trip
  - errors: garbage bytes give an error, never a panic

Generated code: golang/pb/demo.pb.go (made by ../generate.sh from proto/demo.proto)

Run it   go run ./Protobuf/labs/golang/01_marshal_unmarshal_basics
*/
package main

import (
	"fmt"
	"time"

	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/known/timestamppb"

	"dsapractice/api/Protobuf/labs/golang/pb"
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	fmt.Println("== 1. marshal / unmarshal ==")
	u := &pb.User{Id: 150, Name: "Ana", Email: "a@x.io", Role: pb.Role_ROLE_ADMIN, Tags: []string{"go", "proto"}}
	data, err := proto.Marshal(u)
	must(err == nil, "marshal")
	fmt.Printf("  %d bytes: % x\n", len(data), data)
	must(proto.Size(u) == len(data), "Size predicts the length without encoding")

	var back pb.User // start from the zero value; Unmarshal REPLACES the contents
	must(proto.Unmarshal(data, &back) == nil, "unmarshal")
	fmt.Println("  decoded:", back.GetId(), back.GetName(), back.GetRole(), back.GetTags())
	must(proto.Equal(u, &back), "round trip")

	fmt.Println("\n== 2. nil-safe getters ==")
	empty := &pb.User{}
	fmt.Printf("  empty.Address == nil: %v ; empty.GetAddress().GetCity() = %q (no panic)\n",
		empty.Address == nil, empty.GetAddress().GetCity())
	// empty.Address.City  <- this WOULD panic with a nil pointer dereference

	fmt.Println("\n== 3. presence: optional scalars are pointers ==")
	noAge, zeroAge := &pb.User{}, &pb.User{Age: proto.Int32(0)} // proto.Int32 builds a *int32
	fmt.Printf("  unset age: Age==nil %v | age=0: Age==nil %v, value %d\n", noAge.Age == nil, zeroAge.Age == nil, zeroAge.GetAge())
	must(noAge.Age == nil && zeroAge.Age != nil, "optional tracks presence")
	a, _ := proto.Marshal(noAge)
	b, _ := proto.Marshal(zeroAge)
	fmt.Printf("  wire: unset -> %d bytes, age=0 -> %d bytes (% x)\n", len(a), len(b), b)
	must(len(a) == 0 && len(b) == 2, "presence on the wire")
	plain, _ := proto.Marshal(&pb.User{Id: 0, Name: ""})
	fmt.Printf("  a plain int64 id=0 serialises to %d bytes: zero and unset are indistinguishable\n", len(plain))

	fmt.Println("\n== 4. copy, compare, merge ==")
	clone := proto.Clone(u).(*pb.User) // deep copy
	clone.Tags[0] = "CHANGED"
	fmt.Println("  original tags after editing the clone:", u.Tags)
	must(u.Tags[0] == "go", "clone is deep")
	must(!proto.Equal(u, clone), "Equal sees the difference")
	// u == clone would compare POINTERS; never compare messages with ==
	proto.Merge(clone, &pb.User{Name: "Merged", Tags: []string{"x"}}) // scalars overwrite, repeated append
	fmt.Println("  after Merge:", clone.GetName(), clone.GetTags())
	must(len(clone.Tags) == 3, "repeated fields append on merge")

	fmt.Println("\n== 5. well-known Timestamp ==")
	u.CreatedAt = timestamppb.New(time.Date(2026, 9, 21, 10, 30, 0, 0, time.UTC))
	fmt.Println("  created_at:", u.GetCreatedAt().AsTime().Format("2006-01-02 15:04 MST"))

	fmt.Println("\n== 6. unknown fields survive ==")
	future := append(data[:len(data):len(data)], 0xA0, 0x06, 0x01) // field 100 (varint 1): not in our schema
	var v pb.User
	must(proto.Unmarshal(future, &v) == nil, "parse with unknown field")
	again, _ := proto.Marshal(&v)
	fmt.Printf("  parsed OK, re-marshalled bytes identical to input: %v\n", string(again) == string(future))
	must(string(again) == string(future), "unknown fields preserved")

	fmt.Println("\n== 7. bad input is an error, not a panic ==")
	for name, bad := range map[string][]byte{
		"truncated string": {0x12, 0x05, 'a', 'b'},
		"invalid tag":      {0x00},
		"bad varint":       {0x08, 0xff, 0xff},
	} {
		var x pb.User
		err := proto.Unmarshal(bad, &x)
		fmt.Printf("  %-17s -> error: %v\n", name, err != nil)
		must(err != nil, name)
	}
	fmt.Println("\nOK")
}
