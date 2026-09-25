/*
FOUNDATION LEVEL 07 - oneof: making an impossible state unrepresentable
========================================================================
A `oneof` groups several fields and guarantees that at most ONE of them is
set. It is the schema saying "a payment is by card OR by bank OR by wallet,
never two at once" - and then making it impossible to violate.

In Go, this is represented by an interface (`isPayment_Method`) and a set of
wrapper structs (`*Payment_CardToken`, `*Payment_BankIban`, `*Payment_WalletId`).
This ensures compile-time safety: you physically cannot set two members at once
in the same struct.

You will learn
  * declaring a oneof, and that its members keep ordinary unique field numbers
  * type switching on the oneof interface to safely route logic
  * PROOF: setting a second member means replacing the interface implementation
  * that a oneof is a generated-code feature, not a wire-format feature
  * the one real gotcha: a oneof member has presence even when set to its default

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

func main() {
	fmt.Println("== 1. nothing is set at first ==")
	empty := &l07.Payment{AmountCents: 500}
	fmt.Printf("  empty.Method == nil -> %v\n", empty.Method == nil)
	must(empty.Method == nil, "no method set initially")
	// The getters safely return defaults even when the oneof is unset.
	fmt.Printf("  empty.GetCardToken() -> %q\n", empty.GetCardToken())
	must(empty.GetCardToken() == "" && empty.GetBankIban() == "" && empty.GetWalletId() == "", "getters return defaults")
	fmt.Println("  all three getters return \"\" - but none of them is SET")

	fmt.Println("\n== 2. setting one member ==")
	payment := &l07.Payment{
		AmountCents: 1999,
		Method:      &l07.Payment_CardToken{CardToken: "tok_abc123"},
	}
	fmt.Printf("  payment.GetCardToken() -> %q\n", payment.GetCardToken())
	must(payment.GetCardToken() == "tok_abc123", "card token is set")

	fmt.Println("\n== 3. THE BEHAVIOUR: setting a second member clears the first ==")
	before := mustMarshal(payment)
	fmt.Printf("  before: card_token=%q  bytes=%x\n", payment.GetCardToken(), before)
	fmt.Println("    12 0a 746f6b5f616263313233 = 'field 2, 10 bytes, tok_abc123'")

	// In Go, since Method is an interface, assigning a new wrapper overwrites the old one entirely.
	payment.Method = &l07.Payment_BankIban{BankIban: "NO9386011117947"}
	after := mustMarshal(payment)
	fmt.Printf("  after setting BankIban:\n")
	fmt.Printf("    card_token -> %q   <- GONE\n", payment.GetCardToken())
	fmt.Printf("    bytes=%x\n", after)
	must(payment.GetCardToken() == "", "the previous member was cleared for us")
	must(payment.GetBankIban() == "NO9386011117947", "new member is set")
	
	// And it is genuinely gone from the wire, not merely hidden: tag 2 is absent.
	must(!bytes.Contains(after, []byte{0x12, 0x0a}), "tag 2 is absent")
	fmt.Println("    tag 2 is absent from the bytes entirely - the card token is not")
	fmt.Println("    hidden or overwritten, it was removed before encoding.")

	fmt.Println("\n== 4. a oneof is generated-code magic, not wire magic ==")
	// Proof: hand-craft bytes containing TWO members. The wire format has no
	// way to forbid this - there is no "oneof" marker in the encoding at all.
	forged := append(
		append([]byte{0x12, 10}, []byte("tok_abc123")...),
		append([]byte{0x1a, 15}, []byte("NO9386011117947")...)...,
	)
	fmt.Printf("  hand-forged bytes with BOTH tag 2 and tag 3 (%d bytes)\n", len(forged))
	parsed := &l07.Payment{}
	must(proto.Unmarshal(forged, parsed) == nil, "parses without complaint")
	fmt.Printf("  parsed fine. BankIban -> %q\n", parsed.GetBankIban())
	fmt.Printf("  card_token -> %q\n", parsed.GetCardToken())
	
	// The documented rule: LAST one on the wire wins.
	must(parsed.GetBankIban() == "NO9386011117947", "last field wins")
	must(parsed.GetCardToken() == "", "first field is cleared")
	fmt.Println("  => the rule is 'last field on the wire wins'. The guarantee lives in")
	fmt.Println("     the generated struct/interface and the parser, not in the byte layout.")

	fmt.Println("\n== 5. the gotcha: a member set to its DEFAULT is still set ==")
	zeroWallet := &l07.Payment{
		AmountCents: 1,
		Method:      &l07.Payment_WalletId{WalletId: ""}, // explicitly empty!
	}
	zeroWalletBytes := mustMarshal(zeroWallet)
	fmt.Printf("  Payment{WalletId: ''} -> bytes=%x\n", zeroWalletBytes)
	must(bytes.Contains(zeroWalletBytes, []byte{0x22, 0x00}), "tag 4, length 0 is on the wire")
	fmt.Println("    the bytes contain 22 00 = 'field 4, length 0' - it IS on the wire,")
	fmt.Println("    exactly like an `optional` field (level 04). Membership grants presence.")
	fmt.Println("  so checking `if p.GetWalletId() != \"\"` is a BUG.")

	fmt.Println("\n== 6. branching on a oneof properly ==")
	route := func(p *l07.Payment) string {
		switch m := p.Method.(type) {
		case *l07.Payment_CardToken:
			return "charge card " + m.CardToken
		case *l07.Payment_BankIban:
			return "debit account " + m.BankIban
		case *l07.Payment_WalletId:
			return "debit wallet '" + m.WalletId + "'"
		case nil:
			return "no payment method supplied"
		default:
			return "unknown payment method"
		}
	}

	cases := []*l07.Payment{
		{AmountCents: 100, Method: &l07.Payment_CardToken{CardToken: "tok_x"}},
		{AmountCents: 100, Method: &l07.Payment_BankIban{BankIban: "NO93"}},
		zeroWallet,
		{AmountCents: 100},
	}

	for _, caseVal := range cases {
		fmt.Printf("  %T -> %s\n", caseVal.Method, route(caseVal))
	}
	must(route(cases[0]) == "charge card tok_x", "route card")
	must(route(cases[3]) == "no payment method supplied", "route none")

	fmt.Println("\n== 7. why this beats a validator ==")
	fmt.Println("  The alternative is three nullable fields plus a hand-written check")
	fmt.Println("  in every producer and consumer, in every language, forever. A oneof")
	fmt.Println("  moves that invariant into the schema, so the illegal state cannot be")
	fmt.Println("  built - not 'is rejected', but cannot be expressed.")

	fmt.Println("\nOK")
}
