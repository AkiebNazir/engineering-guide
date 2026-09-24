/*
LAB 02 (basic) - oneof, maps and enums in Go
============================================
You will learn
  - oneof becomes an INTERFACE field. You set it with a wrapper type and read it with a type switch:
    u.Contact = &pb.User_Phone{Phone: "+47 555"}
    switch c := u.GetContact().(type) { case *pb.User_Phone: ...; case *pb.User_Slack: ...; case nil: ... }
  - setting one member replaces the other - impossible states cannot be represented
  - maps: fine to read and write like Go maps, BUT the wire order is random unless you ask for
    Deterministic marshalling (matters for hashing, caching, signing, golden tests)
  - enums are int32 with a String() method; unknown numbers are kept, never rejected
  - name <-> number lookups:  pb.Role_name, pb.Role_value
  - why the zero enum value must be `*_UNSPECIFIED`: it is what "forgot to set it" looks like

Run it   go run ./Protobuf/labs/golang/02_oneof_maps_enums
*/
package main

import (
	"bytes"
	"fmt"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/labs/golang/pb"
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func describeContact(u *pb.User) string {
	switch c := u.GetContact().(type) { // the interface holds exactly one of the wrapper types, or nil
	case *pb.User_Phone:
		return "call " + c.Phone
	case *pb.User_Slack:
		return "slack " + c.Slack
	case nil:
		return "no contact method"
	default:
		return "unknown (a newer schema added a member we do not know)"
	}
}

func main() {
	fmt.Println("== 1. oneof ==")
	u := &pb.User{Name: "Ana"}
	fmt.Println("  unset          ->", describeContact(u))
	u.Contact = &pb.User_Phone{Phone: "+47 555 0100"}
	fmt.Println("  phone set      ->", describeContact(u))
	u.Contact = &pb.User_Slack{Slack: "@ana"} // REPLACES the phone
	fmt.Println("  slack assigned ->", describeContact(u), "| GetPhone() =", fmt.Sprintf("%q", u.GetPhone()))
	must(u.GetPhone() == "" && u.GetSlack() == "@ana", "oneof holds one member")
	data, _ := proto.Marshal(u)
	var back pb.User
	proto.Unmarshal(data, &back)
	must(describeContact(&back) == "slack @ana", "oneof round trip")

	fmt.Println("\n== 2. maps ==")
	u.Attrs = map[string]string{"team": "core", "region": "eu-west"}
	u.Attrs["tier"] = "gold"
	delete(u.Attrs, "team")
	fmt.Println("  attrs:", u.Attrs, "| missing key ->", fmt.Sprintf("%q", u.Attrs["nope"]))
	var nilMap pb.User
	fmt.Println("  reading a nil map is fine:", len(nilMap.Attrs), "| WRITING to it panics - allocate first")

	fmt.Println("\n== 3. map ordering on the wire ==")
	big := &pb.User{Attrs: map[string]string{}}
	for i := 0; i < 20; i++ {
		big.Attrs[fmt.Sprintf("key-%02d", i)] = "v"
	}
	distinctDefault, distinctDet := map[string]bool{}, map[string]bool{}
	for i := 0; i < 200; i++ {
		a, _ := proto.MarshalOptions{}.Marshal(big)
		b, _ := proto.MarshalOptions{Deterministic: true}.Marshal(big)
		distinctDefault[string(a)], distinctDet[string(b)] = true, true
	}
	fmt.Printf("  200 marshals of the SAME message -> %d different byte strings by default, %d with Deterministic\n",
		len(distinctDefault), len(distinctDet))
	must(len(distinctDefault) > 1 && len(distinctDet) == 1, "map order is random unless Deterministic")
	fmt.Println("  => hash/sign/cache-key serialised messages ONLY with Deterministic (and note: even that is")
	fmt.Println("     stable within one binary version, not a cross-language canonical form).")

	fmt.Println("\n== 4. enums ==")
	r := pb.Role_ROLE_ADMIN
	fmt.Printf("  %v = %d ; name lookup: %v ; value lookup: %d\n", r, r, pb.Role_name[2], pb.Role_value["ROLE_USER"])
	fmt.Println("  zero value:", pb.User{}.Role, "(that is what 'forgot to set' looks like)")
	unknown := pb.Role(7) // a number from a FUTURE schema
	fmt.Printf("  unknown value prints as %q and is kept on the wire\n", unknown.String())
	wire, _ := proto.Marshal(&pb.User{Role: unknown})
	var got pb.User
	must(proto.Unmarshal(wire, &got) == nil && got.Role == unknown, "unknown enum survives")
	re, _ := proto.Marshal(&got)
	must(bytes.Equal(re, wire), "unknown enum re-marshals identically")
	fmt.Println("  => a `switch` over an enum needs a `default:` branch. New values WILL arrive.")

	fmt.Println("\n== 5. field-number economy (why 1-15 are precious) ==")
	hot, _ := proto.Marshal(&pb.User{Rating: 1.5})        // field 15: one-byte tag
	cold, _ := proto.Marshal(&pb.User{Avatar: []byte{1}}) // field 16: two-byte tag
	fmt.Printf("  double at field 15: %d bytes (1 tag + 8) ; 1-byte bytes at field 16: %d bytes (2 tag + 1 len + 1)\n", len(hot), len(cold))
	must(len(hot) == 9 && len(cold) == 4, "tag sizes")
	fmt.Println("\nOK")
}
