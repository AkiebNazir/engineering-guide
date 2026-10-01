"""
FOUNDATION LEVEL 05 - Enums, and the unknown value that will definitely arrive
===============================================================================
An enum is a named set of integers. On the wire it is just a varint, so an
enum field costs the same as an int32 - the names exist only in your code.

That last sentence is the whole lesson. Because only the NUMBER travels, a
newer sender can hand you a number your build has never heard of. This is not
a hypothetical: it happens every time two services are deployed minutes apart.
proto3 handles it gracefully - the unknown number is kept, not rejected, and
re-serialising gives it back untouched - but YOUR code has to expect it.

The two schemas here model exactly that deployment window:
  ../proto/l05_new.proto  knows STATUS_ARCHIVED = 3   (the upgraded service)
  ../proto/l05_old.proto  does not                    (the client, not yet redeployed)

You will learn
  * declaring an enum, and why the zero value must exist and be *_UNSPECIFIED
  * that an enum field is a plain varint on the wire - names are compiled away
  * PROOF: a value of 3 sent by the new schema survives in the old schema
    and round-trips back out unchanged
  * why `if/elif` over enum values without a fallback branch is a latent bug
  * that enum names are per-file, so two schemas can disagree safely

Run it   python 05_enums_and_unknown_values.py
"""
import l05_new_pb2 as new  # knows QUEUED=1, RUNNING=2, ARCHIVED=3
import l05_old_pb2 as old  # knows QUEUED=1, RUNNING=2  ... and nothing else

if __name__ == "__main__":
    print("== 1. an enum is a set of names for integers ==")
    print(f"  STATUS_UNSPECIFIED = {new.STATUS_UNSPECIFIED}")
    print(f"  STATUS_QUEUED      = {new.STATUS_QUEUED}")
    print(f"  STATUS_RUNNING     = {new.STATUS_RUNNING}")
    print(f"  STATUS_ARCHIVED    = {new.STATUS_ARCHIVED}   (new schema only)")
    # Name <-> number lookup goes through the enum wrapper type.
    print(f"  Status.Name(2)            -> {new.Status.Name(2)!r}")
    print(f"  Status.Value('STATUS_QUEUED') -> {new.Status.Value('STATUS_QUEUED')}")
    assert new.STATUS_ARCHIVED == 3 and new.Status.Name(2) == "STATUS_RUNNING"

    print("\n== 2. why the zero value is mandatory ==")
    # proto3 requires the first enum value to be 0, because a plain enum field
    # is a plain scalar (level 04): unset reads as 0. If 0 meant a real state,
    # every message that forgot to set the field would silently claim it.
    job = new.Job(id="j1")
    print(f"  a Job with no status set reads as {new.Status.Name(job.status)!r} (= 0)")
    assert job.status == new.STATUS_UNSPECIFIED
    print("  => naming 0 *_UNSPECIFIED makes 'nobody set this' an explicit,")
    print("     checkable state instead of an accidental default like QUEUED.")

    print("\n== 3. on the wire, an enum is just a number ==")
    running = new.Job(id="j1", status=new.STATUS_RUNNING)
    data = running.SerializeToString()
    print(f"  Job(id='j1', status=STATUS_RUNNING) -> {data.hex()}")
    print("    0a 02 6a31 = field 1, 2 bytes, 'j1'")
    print("    10 02      = field 2, varint 2      <- the NAME is nowhere on the wire")
    assert data.hex() == "0a026a311002"
    assert b"RUNNING" not in data

    print("\n== 4. THE PROOF: an unknown value arrives from a newer schema ==")
    # The upgraded service archives a job and sends it.
    archived = new.Job(id="j1", status=new.STATUS_ARCHIVED)
    wire = archived.SerializeToString()
    print(f"  new schema sends status=3 : {wire.hex()}")

    # The old client parses it. It has never heard of 3. It does NOT crash,
    # and it does NOT reset the field - the number is retained as-is.
    received = old.Job()
    received.ParseFromString(wire)
    print(f"  old schema parses it, no error. received.status = {received.status}")
    assert received.status == 3, "the unknown number is kept verbatim"

    # The old client cannot NAME it, which is the honest outcome.
    try:
        old.Status.Name(received.status)
        raise AssertionError("expected the old schema to be unable to name 3")
    except ValueError:
        print("  old.Status.Name(3) -> ValueError (this build has no name for it)")

    # ...and forwarding it on loses nothing. This is what makes rolling
    # deploys and proxies safe: a middleman that does not understand a value
    # still passes it through byte-for-byte.
    forwarded = received.SerializeToString()
    print(f"  old schema re-serialises  : {forwarded.hex()}")
    assert forwarded == wire, "round trip through the old schema is lossless"
    print("  IDENTICAL to what the new schema sent -> nothing was dropped.")
    round_tripped = new.Job()
    round_tripped.ParseFromString(forwarded)
    assert round_tripped.status == new.STATUS_ARCHIVED
    print(f"  and the new schema reads it back as {new.Status.Name(round_tripped.status)!r}")

    print("\n== 5. the bug this creates in ordinary-looking code ==")

    def describe_badly(status: int) -> str:
        # Looks exhaustive. Is not. Silently mislabels every future value.
        if status == old.STATUS_QUEUED:
            return "waiting"
        elif status == old.STATUS_RUNNING:
            return "in progress"
        return "waiting"  # <- the lie: an unknown status is reported as queued

    def describe_well(status: int) -> str:
        if status == old.STATUS_QUEUED:
            return "waiting"
        if status == old.STATUS_RUNNING:
            return "in progress"
        # The honest branch. Degrade visibly; do not invent a state.
        return f"unrecognised status {status} (this build is older than the sender)"

    print(f"  no fallback   -> {describe_badly(received.status)!r}   <- WRONG, and silent")
    print(f"  with fallback -> {describe_well(received.status)!r}")
    assert describe_badly(received.status) == "waiting"
    assert "unrecognised status 3" in describe_well(received.status)
    print("  => always write the default branch. New enum values WILL arrive, from")
    print("     a service that was deployed four minutes before yours.")

    print("\nOK")
