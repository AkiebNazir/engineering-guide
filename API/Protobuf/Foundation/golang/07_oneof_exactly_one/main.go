/*
FOUNDATION LEVEL 07 - oneof: making an impossible state unrepresentable
========================================================================
A `oneof` groups several fields and guarantees that at most ONE of them is
set. It is the schema saying "a payment is by card OR by bank OR by wallet,
never two at once" - and then making it impossible to violate, in every
generated language, instead of hoping every service validates it.

Go expresses this more literally than most languages. protoc-gen-go turns the
oneof into ONE struct field, `Method`, whose type is a sealed interface
(isPayment_Method). Each member gets its own tiny wrapper struct that
implements it:

	Method = &l07.Payment_CardToken{CardToken: "tok_abc123"}
	Method = &l07.Payment_BankIban{BankIban: "NO9386011117947"}

A single interface field can only hold one wrapper at a time, so "two members
set" is not something you can even type. Assigning a second member does not
raise an error - it REPLACES the first. That is deliberate, but it means a
careless `if` chain that assigns two members keeps only the last one, with no
complaint.

../../proto/l07_oneof.proto is Payment{amount_cents=1, oneof method {
card_token=2, bank_iban=3, wallet_id=4 }}.

You will learn
  - declaring a oneof, and that its members keep ordinary unique field numbers
  - the Go shape: one interface field + one wrapper struct per member
  - PROOF: assigning a second member replaces the first, in memory and on the wire
  - that a oneof is a generated-code feature, not a wire-format feature
  - the one real gotcha: a member set to its default is still SET
  - a type switch is how you branch on a oneof - and why it needs a default

Run it   go run ./Protobuf/Foundation/golang/07_oneof_exactly_one
*/
package main

import (
	"bytes"
	"fmt"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l07"
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

// which is the Go spelling of Python's WhichOneof: ask the reflection API
// which member of the named oneof is populated. Application code normally
// uses a type switch (section 6); this is handy for printing and asserting.
func which(p *l07.Payment) string {
	oneof := p.ProtoReflect().Descriptor().Oneofs().ByName("method")
	field := p.ProtoReflect().WhichOneof(oneof)
	if field == nil {
		return "<none>"
	}
	return string(field.Name())
}

// route branches on the oneof the idiomatic Go way: a type switch over the
// wrapper types. The `default` branch is not decoration - see the comment.
func route(p *l07.Payment) string {
	switch m := p.GetMethod().(type) {
	case *l07.Payment_CardToken:
		return "charge card " + m.CardToken
	case *l07.Payment_BankIban:
		return "debit account " + m.BankIban
	case *l07.Payment_WalletId:
		return fmt.Sprintf("debit wallet %q", m.WalletId)
	case nil:
		return "no payment method supplied"
	default:
		// Unreachable with THIS build of the schema. But if a future version
		// adds `string voucher_code = 5;` to the oneof, an older build that
		// receives it sees the bytes as an UNKNOWN field and Method is nil -
		// so it lands in `case nil` above, not here. This branch guards
		// against a newer generated package being linked in without the
		// switch being updated. Cheap insurance; keep it.
		return fmt.Sprintf("unhandled payment method %T", m)
	}
}

func main() {
	fmt.Println("== 1. nothing is set at first ==")
	empty := &l07.Payment{AmountCents: 500}
	fmt.Printf("  Method field -> %v   which -> %s\n", empty.GetMethod(), which(empty))
	must(empty.GetMethod() == nil, "an untouched oneof is nil")
	// All members still read as their defaults - the nil-safe getters never
	// panic, and reading does not set anything.
	must(empty.GetCardToken() == "" && empty.GetBankIban() == "" && empty.GetWalletId() == "",
		"every member reads as its default")
	fmt.Println("  all three getters return \"\" - but none of the members is SET")

	fmt.Println("\n== 2. setting one member ==")
	// You set a oneof by assigning a WRAPPER to the one interface field.
	payment := &l07.Payment{
		AmountCents: 1999,
		Method:      &l07.Payment_CardToken{CardToken: "tok_abc123"},
	}
	fmt.Printf("  Method = %T\n", payment.GetMethod())
	fmt.Printf("  which  -> %s\n", which(payment))
	must(which(payment) == "card_token", "card_token is the set member")
	must(payment.GetCardToken() == "tok_abc123", "and its getter returns the value")
	// Go has no separate struct field per member - CardToken, BankIban and
	// WalletId exist only as getters on Payment and as fields of the wrappers.
	fmt.Println("  there is no Payment.CardToken field to assign - the ONE field is")
	fmt.Println("  Method, and only a wrapper type fits in it.")

	fmt.Println("\n== 3. THE BEHAVIOUR: setting a second member replaces the first ==")
	before := mustMarshal(payment)
	fmt.Printf("  before: card_token=%q  bytes=%x\n", payment.GetCardToken(), before)
	fmt.Println("    ...12 0a 746f6b5f616263313233 = 'field 2, 10 bytes, tok_abc123'")

	payment.Method = &l07.Payment_BankIban{BankIban: "NO9386011117947"} // no error, no warning
	after := mustMarshal(payment)
	fmt.Println("  after assigning a BankIban wrapper:")
	fmt.Printf("    which        -> %s\n", which(payment))
	fmt.Printf("    GetCardToken -> %q   <- GONE\n", payment.GetCardToken())
	fmt.Printf("    bytes=%x\n", after)
	must(which(payment) == "bank_iban", "bank_iban is now the member")
	must(payment.GetCardToken() == "", "the previous member was replaced")
	// And it is genuinely gone from the wire, not merely hidden: tag 2 is absent.
	must(!bytes.Contains(after, []byte{0x12, 0x0a}), "tag 2 is not on the wire")
	must(!bytes.Contains(after, []byte("tok_abc123")), "nor is the token")
	fmt.Println("    tag 2 is absent from the bytes entirely - the card token was not")
	fmt.Println("    hidden, it was never encoded. The old wrapper is simply garbage now.")

	fmt.Println("\n== 4. a oneof is generated-code magic, not wire magic ==")
	// Proof: hand-craft bytes containing TWO members. The wire format has no
	// way to forbid this - there is no "oneof" marker in the encoding at all.
	var forged []byte
	forged = append(forged, 0x12, 10)
	forged = append(forged, "tok_abc123"...)
	forged = append(forged, 0x1a, 15)
	forged = append(forged, "NO9386011117947"...)
	fmt.Printf("  hand-forged bytes with BOTH tag 2 and tag 3 (%d bytes)\n", len(forged))
	parsed := &l07.Payment{}
	must(proto.Unmarshal(forged, parsed) == nil, "accepted without complaint")
	fmt.Printf("  parsed fine. which -> %s, GetCardToken -> %q\n", which(parsed), parsed.GetCardToken())
	// The documented rule: LAST one on the wire wins. The parser walks the
	// bytes in order and each member it meets overwrites Method.
	must(which(parsed) == "bank_iban", "last member on the wire wins")
	must(parsed.GetCardToken() == "", "the earlier member was discarded")
	fmt.Println("  => the rule is 'last field on the wire wins'. The guarantee lives in")
	fmt.Println("     the generated code and the parser, not in the byte layout.")
	fmt.Println("     Practical upshot: a oneof costs NO extra wire bytes - this Payment")
	fmt.Println("     encodes exactly as a plain string field would.")

	fmt.Println("\n== 5. the gotcha: a member set to its DEFAULT is still set ==")
	zeroWallet := &l07.Payment{AmountCents: 1, Method: &l07.Payment_WalletId{WalletId: ""}}
	zeroBytes := mustMarshal(zeroWallet)
	fmt.Printf("  Method=&Payment_WalletId{WalletId: \"\"} -> which = %s, bytes=%x\n",
		which(zeroWallet), zeroBytes)
	must(which(zeroWallet) == "wallet_id", "an empty wallet id is still the set member")
	must(bytes.Contains(zeroBytes, []byte{0x22, 0x00}), "tag 4, length 0, is on the wire")
	fmt.Println("    the bytes contain 22 00 = 'field 4, length 0' - it IS on the wire,")
	fmt.Println("    exactly like an `optional` field (level 04). Membership grants presence.")
	fmt.Println("  so this is a BUG:")
	fmt.Println("      if p.GetWalletId() != \"\" { ... }   // false for a deliberately-empty id")
	fmt.Println("  and this is correct:")
	fmt.Println("      if _, ok := p.GetMethod().(*l07.Payment_WalletId); ok { ... }")

	fmt.Println("\n== 6. branching on a oneof properly: a type switch ==")
	cases := []*l07.Payment{
		{AmountCents: 100, Method: &l07.Payment_CardToken{CardToken: "tok_x"}},
		{AmountCents: 100, Method: &l07.Payment_BankIban{BankIban: "NO93"}},
		zeroWallet,
		{AmountCents: 100},
	}
	for _, c := range cases {
		fmt.Printf("  %-12s -> %s\n", which(c), route(c))
	}
	must(route(cases[0]) == "charge card tok_x", "card routed")
	must(route(cases[3]) == "no payment method supplied", "none routed")
	// Clearing the group is just assigning nil to the one field.
	cases[0].Method = nil
	must(which(cases[0]) == "<none>", "nil clears the group")
	fmt.Println("  p.Method = nil clears the group, whichever member was set")

	fmt.Println("\n== 7. why this beats a validator ==")
	fmt.Println("  The alternative is three plain string fields plus a hand-written check")
	fmt.Println("  in every producer and consumer, in every language, forever. A oneof")
	fmt.Println("  moves that invariant into the schema, so the illegal state cannot be")
	fmt.Println("  built - not 'is rejected', but cannot be expressed. In Go you can see")
	fmt.Println("  it in the type system itself: there is one field, and it holds one thing.")

	fmt.Println("\nOK")
}
