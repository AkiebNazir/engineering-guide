"""
FOUNDATION LEVEL 07 - oneof: making an impossible state unrepresentable
========================================================================
A `oneof` groups several fields and guarantees that at most ONE of them is
set. It is the schema saying "a payment is by card OR by bank OR by wallet,
never two at once" - and then making it impossible to violate, in every
generated language, instead of hoping every service validates it.

The mechanism is worth understanding because it surprises people: setting a
second member does not raise an error. It SILENTLY CLEARS the first. That is
deliberate - assignment always succeeds, and the invariant is maintained by
construction - but it means a careless `if` chain that sets two members keeps
only the last one, with no complaint.

You will learn
  * declaring a oneof, and that its members keep ordinary unique field numbers
  * WhichOneof() - asking which member is set, and getting None when none is
  * PROOF: setting a second member clears the first, on the wire and in memory
  * that a oneof is a generated-code feature, not a wire-format feature
  * the one real gotcha: a oneof member has presence even when set to its default
  * why this beats "three nullable columns plus a validator"

Run it   python 07_oneof_exactly_one.py
"""
import l07_oneof_pb2 as pb

if __name__ == "__main__":
    print("== 1. nothing is set at first ==")
    empty = pb.Payment(amount_cents=500)
    # WhichOneof returns the NAME of the set member, or None. This is the only
    # correct way to branch on a oneof.
    print(f"  WhichOneof('method') -> {empty.WhichOneof('method')}")
    assert empty.WhichOneof("method") is None
    # All members still read as their defaults - reading does not set anything.
    assert (empty.card_token, empty.bank_iban, empty.wallet_id) == ("", "", "")
    print("  all three members read as '' - but none of them is SET")

    print("\n== 2. setting one member ==")
    payment = pb.Payment(amount_cents=1999, card_token="tok_abc123")
    print(f"  WhichOneof('method') -> {payment.WhichOneof('method')!r}")
    print(f"  HasField('card_token') -> {payment.HasField('card_token')}")
    print(f"  HasField('bank_iban')  -> {payment.HasField('bank_iban')}")
    assert payment.WhichOneof("method") == "card_token"
    assert payment.HasField("card_token") and not payment.HasField("bank_iban")
    # Note that HasField works on a oneof MEMBER even though it is a plain
    # string - membership in a oneof grants presence (see level 04's table).

    print("\n== 3. THE BEHAVIOUR: setting a second member clears the first ==")
    before = payment.SerializeToString()
    print(f"  before: card_token={payment.card_token!r}  bytes={before.hex()}")
    print("    12 0a 746f6b5f616263313233 = 'field 2, 10 bytes, tok_abc123'")

    payment.bank_iban = "NO9386011117947"        # no error, no warning
    after = payment.SerializeToString()
    print(f"  after setting bank_iban:")
    print(f"    WhichOneof('method') -> {payment.WhichOneof('method')!r}")
    print(f"    card_token           -> {payment.card_token!r}   <- GONE")
    print(f"    bytes={after.hex()}")
    assert payment.WhichOneof("method") == "bank_iban"
    assert payment.card_token == "", "the previous member was cleared for us"
    assert not payment.HasField("card_token")
    # And it is genuinely gone from the wire, not merely hidden: tag 2 is absent.
    assert bytes.fromhex("120a") not in after
    assert b"tok_abc123" not in after
    print("    tag 2 is absent from the bytes entirely - the card token is not")
    print("    hidden or overwritten, it was removed before encoding.")

    print("\n== 4. a oneof is generated-code magic, not wire magic ==")
    # Proof: hand-craft bytes containing TWO members. The wire format has no
    # way to forbid this - there is no "oneof" marker in the encoding at all.
    forged = (bytes.fromhex("12") + bytes([10]) + b"tok_abc123"
              + bytes.fromhex("1a") + bytes([15]) + b"NO9386011117947")
    print(f"  hand-forged bytes with BOTH tag 2 and tag 3 ({len(forged)} bytes)")
    parsed = pb.Payment()
    parsed.ParseFromString(forged)        # accepted without complaint
    print(f"  parsed fine. WhichOneof -> {parsed.WhichOneof('method')!r}")
    print(f"  card_token -> {parsed.card_token!r}")
    # The documented rule: LAST one on the wire wins. The parser applies the
    # same "set clears the others" logic as it walks the bytes in order.
    assert parsed.WhichOneof("method") == "bank_iban"
    assert parsed.card_token == ""
    print("  => the rule is 'last field on the wire wins'. The guarantee lives in")
    print("     the generated setters and the parser, not in the byte layout.")
    print("     Practical upshot: a oneof does NOT need any extra wire budget -")
    print(f"     this Payment costs the same as a plain string field would.")

    print("\n== 5. the gotcha: a member set to its DEFAULT is still set ==")
    # This is where a naive truthiness check goes wrong.
    zero_wallet = pb.Payment(amount_cents=1, wallet_id="")   # explicitly empty!
    print(f"  Payment(wallet_id='')  -> WhichOneof = {zero_wallet.WhichOneof('method')!r}, "
          f"bytes={zero_wallet.SerializeToString().hex()}")
    assert zero_wallet.WhichOneof("method") == "wallet_id"
    assert bytes.fromhex("2200") in zero_wallet.SerializeToString()  # tag 4, length 0
    print("    the bytes contain 22 00 = 'field 4, length 0' - it IS on the wire,")
    print("    exactly like an `optional` field (level 04). Membership grants presence.")
    print("  so this is a BUG:")
    print("      if p.wallet_id:  ...   # False for a deliberately-empty wallet id")
    print("  and this is correct:")
    print("      if p.WhichOneof('method') == 'wallet_id':  ...")

    print("\n== 6. branching on a oneof properly ==")

    def route(p: pb.Payment) -> str:
        which = p.WhichOneof("method")
        if which == "card_token":
            return f"charge card {p.card_token}"
        if which == "bank_iban":
            return f"debit account {p.bank_iban}"
        if which == "wallet_id":
            return f"debit wallet {p.wallet_id!r}"
        # Always handle "none set" - and note a NEW member added to the oneof
        # in a future schema version lands here too, on an older build.
        return "no payment method supplied"

    cases = [
        pb.Payment(amount_cents=100, card_token="tok_x"),
        pb.Payment(amount_cents=100, bank_iban="NO93"),
        zero_wallet,
        pb.Payment(amount_cents=100),
    ]
    for case in cases:
        print(f"  {str(case.WhichOneof('method')):<12} -> {route(case)}")
    assert route(cases[0]).startswith("charge card")
    assert route(cases[3]) == "no payment method supplied"

    # ClearField on the GROUP name clears whichever member was set.
    cases[0].ClearField("method")
    assert cases[0].WhichOneof("method") is None
    print("  ClearField('method') clears the group, whichever member was set")

    print("\n== 7. why this beats a validator ==")
    print("  The alternative is three nullable fields plus a hand-written check")
    print("  in every producer and consumer, in every language, forever. A oneof")
    print("  moves that invariant into the schema, so the illegal state cannot be")
    print("  built - not 'is rejected', but cannot be expressed.")

    print("\nOK")
