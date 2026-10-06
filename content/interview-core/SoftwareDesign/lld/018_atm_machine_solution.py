"""
================================================================================
SOLUTION · LLD 018 · ATM Machine                                    [Tier 2]
================================================================================

THE CORE IDEA
--------------
Two things make this different from `003_vending_machine`, and both are the
point of the exercise:

    1. THE LEDGER IS SOMEONE ELSE'S.  A vending machine owns its own cash box.
       An ATM's money lives in the bank's account, reached only through a
       `Bank` PORT (an interface). The ATM never imports a concrete bank
       class — see `08_application_architecture_in_code.md` §3. That single
       decision is what forces the next one:

    2. DEBIT AND DISPENSE ARE TWO SYSTEMS WITH NO SHARED TRANSACTION.  You
       cannot begin a database transaction that also holds a physical cash
       cassette. So the design has to accept that "debit the bank" can
       succeed while "dispense the cash" fails a moment later — and must
       have an explicit COMPENSATING action (credit the bank back) for that
       case, instead of pretending it can't happen
       (`06_error_handling_and_failure_design.md` §9).

Cash dispensing itself is CHAIN OF RESPONSIBILITY
(`04_design_patterns_in_practice.md` §11): the $100 cassette takes what it
can of the request and hands the remainder to the $50 cassette, which hands
its remainder to the $20 cassette, and so on. Two passes make it atomic:
`preview()` walks the chain read-only and reports what WOULD be given and
what's left unpaid; only if nothing is left unpaid does `dispense()` walk the
chain again calling `commit()`, which is the only method that mutates a
cassette's count. A request that can't be made exactly touches no inventory
at all — the same "compute first, mutate only on success" discipline
`003_vending_machine`'s `ChangeMaker` uses, applied to a chain instead of a
single strategy call.

One more thing worth saying out loud in the interview: standard note
denominations (100, 50, 20, 10, 5, 1, ...) form a "canonical" coin system,
so greedy largest-first is always optimal — no DP fallback needed the way
`003`'s `BoundedChange` sometimes needs one for arbitrary coin sets.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. insert_card -> enter_pin -> balance()/withdraw() -> eject_card, in that
     order; any call out of order raises InvalidOperation and changes nothing.
  2. Wrong PIN: AuthenticationFailed, stays retryable. max_pin_attempts wrong
     PINs in one session: CARD_RETAINED, needs service_reset().
  3. withdraw: validate the amount, THEN debit the bank, THEN dispense.
     Bank shortfall -> InsufficientFunds, machine untouched. Machine can't
     make the exact amount -> credit the bank back, then InsufficientCash.
  4. Cassettes are per-denomination counts; dispense is atomic and
     largest-denomination-first.
  Out of scope: concurrent ATMs, deposits, receipts, card networks.


================================================================================
ENTITIES AND INVARIANTS
================================================================================
    State               enum: the session state machine
    Bank                port: authenticate / balance / debit / credit
    DenominationHandler chain link: preview (pure) then commit (mutates)
                        INVARIANT: total() only ever decreases via commit(),
                        and commit() is only ever called with a split that a
                        preview() on the SAME state already proved exact
    CashDispenser       owns the chain; dispense() = preview, then commit
                        only if the full amount was covered
    ATM                 INVARIANT: a debit with no matching dispense success
                        is always followed by a credit for the same amount
                        before the exception reaches the caller — the
                        customer's balance is never left short


================================================================================
SESSION STATE MACHINE
================================================================================
    IDLE --insert_card--> CARD_INSERTED --enter_pin (ok)--> AUTHENTICATED
      ^                        |  ^                              |
      |                        |  | enter_pin (wrong, attempts    | balance()
      |                        |  | remain): AuthenticationFailed | withdraw()
      |                        |  '------------------------------'    |
      |                        |                                      |
      |                        v enter_pin (wrong, attempts used up)  |
      |                   CARD_RETAINED <---- CardRetained raised     |
      |                        |                                      |
      |                        | service_reset()                      |
      '------------------------'                                      |
      '-----------------------------  eject_card() -------------------'

Every method other than insert_card/service_reset checks the CURRENT state
before doing anything, so an out-of-order call is rejected before it can
have a side effect — there is no "oops, half-authenticated" state to reason
about.


================================================================================
COMPENSATION TRACE · account balance 1000, cassettes {100: 1, 20: 1}, withdraw(40)
================================================================================
    step                          bank balance   cassette total   ATM raises
    start                         1000           120              -
    validate 40 (multiple of 20)  1000           120              -
    bank.debit(acc, 40)           960            120              -
    dispenser.dispense(40):
      preview: 100-handler can't use a $100 for 40, passes 40 down
      preview: 20-handler has one $20, uses it, 20 STILL unpaid, chain ends
      -> InsufficientCash (preview only; no commit happened)            -
    ATM catches it, bank.credit(acc, 40)  1000    120              -
    ATM re-raises                 1000           120              InsufficientCash

The customer sees a declined withdrawal and their original balance — not a
transaction that silently vanished 40 units of currency.


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Debit-then-dispense (not dispense-then-debit): a real cash cassette can't
    be asked "would you succeed?" without also being far more complex
    hardware than a database read. Debiting first, with a compensating
    credit on failure, is the same shape as any two-system write without a
    shared transaction — the general case chapter `06` covers, here made
    concrete.
  * `preview()`/`commit()` split on the dispenser is a LOCAL optimisation
    that happens to avoid ever leaving a cassette half-drained — it does not
    remove the need for compensation at the bank level, because the bank and
    the dispenser are still two different systems.
  * PIN attempts live on the ATM (per session), not the bank: the bank could
    layer its own fraud rules on top, but "this physical machine keeps the
    card after 3 tries" is this machine's own policy.
  * `Bank` is a `Protocol`, constructed nowhere inside `ATM` — swapping in a
    real HTTP-backed bank client requires zero changes to `ATM` or its tests.
  * No locking inside `ATM`: one machine, one customer, one session at a
    time, by construction — see "out of scope" above.


================================================================================
COMPLEXITY
================================================================================
    insert_card / enter_pin / eject_card / balance   O(1)
    withdraw                                         O(D) chain walk twice
                                                       (D = number of
                                                       denominations, small
                                                       and constant in
                                                       practice)
    Space                                            O(D) for the cassette
                                                       chain and counts


================================================================================
EDGE CASES
================================================================================
  * Exact multiple of the smallest note but not constructible from what's
    left (see the compensation trace above) -> InsufficientCash + compensation.
  * The 3rd wrong PIN raises CardRetained, not AuthenticationFailed — the
    caller must not be told "try again" when there is no again.
  * service_reset() only makes sense from CARD_RETAINED in this design;
    calling it from IDLE would be a silent no-op, so it's restricted to
    exactly the state it exists to fix.
  * Zero and negative amounts, and amounts smaller than the smallest note,
    are all InvalidAmount before the bank is ever called.
  * withdraw() after eject_card() is InvalidOperation, same as before any
    card was ever inserted — the session leaves no residue.


================================================================================
COMMON MISTAKES
================================================================================
  1. Debiting and dispensing with no compensation path — "the bank call
     succeeded, so we're done" ignores that the physical machine is a
     second point of failure.
  2. Checking "is there enough cash IN TOTAL" instead of "can this EXACT
     amount be made" — 120 total cash does not mean 40 is dispensable.
  3. Mutating cassette counts during preview() instead of only on commit(),
     which leaves the machine short after a request that ultimately failed.
  4. Letting a wrong PIN silently reset the attempt counter, turning
     CARD_RETAINED into a security control nobody can trigger.
  5. Putting bank-account logic inside the ATM class "for now" — it can't be
     unit-tested without a real bank, and it couples the machine to one
     bank's schema.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Daily withdrawal limits -> another check between validate and debit,
    backed by the bank (it must survive across sessions/machines).
  * Deposits -> credit first? No — count the cash first (another chain,
    reversed), THEN credit, so you never credit currency you didn't receive.
  * The compensating credit itself fails (network partition mid-recovery) ->
    the classic saga problem: log the pending compensation durably and retry
    it out-of-band; never let it depend on the same request succeeding twice.
  * Multi-currency -> CashDispenser becomes one per currency; ATM picks by a
    strategy on the card/account.
  * Offline mode -> queue debits locally with idempotency keys
    (`06_error_handling_and_failure_design.md` §8), reconcile when the link
    returns.


================================================================================
RELATED
================================================================================
  lld/003_vending_machine       State pattern, money in cents, greedy +
                                 bounded change — read this one first; ATM
                                 keeps the state machine and drops the coin
                                 math for a chain and an external ledger.
  04_design_patterns_in_practice.md  §11 Chain of Responsibility
  06_error_handling_and_failure_design.md  §9 Partial failure and compensation
  08_application_architecture_in_code.md  §3 Ports, §8 dependency injection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class State(Enum):
    IDLE = "idle"
    CARD_INSERTED = "card_inserted"
    AUTHENTICATED = "authenticated"
    CARD_RETAINED = "card_retained"


class ATMError(Exception): ...


class InvalidOperation(ATMError): ...      # wrong state for this call


class AuthenticationFailed(ATMError): ...  # wrong PIN; attempts remain


class CardRetained(ATMError): ...          # too many wrong PINs this session


class InvalidAmount(ATMError): ...         # <= 0, or not a multiple of the smallest note


class InsufficientFunds(ATMError): ...     # bank-side: the account doesn't have it


class InsufficientCash(ATMError): ...      # machine-side: can't make that exact amount


class Bank(Protocol):
    def authenticate(self, card_id: str, pin: str) -> str:
        """Returns the account_id on success. Raises AuthenticationFailed."""
        ...

    def balance(self, account_id: str) -> int: ...

    def debit(self, account_id: str, amount: int) -> None:
        """Raises InsufficientFunds; balance unchanged on failure."""
        ...

    def credit(self, account_id: str, amount: int) -> None: ...


@dataclass
class FakeBank:
    """A bank double for tests: fixed card->account->pin mapping, real balances."""
    card_accounts: dict[str, str]
    pins: dict[str, str]
    balances: dict[str, int] = field(default_factory=dict)
    debit_calls: list[tuple[str, int]] = field(default_factory=list)
    credit_calls: list[tuple[str, int]] = field(default_factory=list)

    def authenticate(self, card_id: str, pin: str) -> str:
        account_id = self.card_accounts.get(card_id)
        if account_id is None or self.pins.get(card_id) != pin:
            raise AuthenticationFailed(f"bad credentials for {card_id!r}")
        return account_id

    def balance(self, account_id: str) -> int:
        return self.balances[account_id]

    def debit(self, account_id: str, amount: int) -> None:
        if self.balances[account_id] < amount:
            raise InsufficientFunds(f"{account_id} has {self.balances[account_id]}, needs {amount}")
        self.balances[account_id] -= amount
        self.debit_calls.append((account_id, amount))

    def credit(self, account_id: str, amount: int) -> None:
        self.balances[account_id] += amount
        self.credit_calls.append((account_id, amount))


class DenominationHandler:
    """One link in the cassette chain: handles what it can, passes the rest on."""

    def __init__(self, denomination: int, count: int,
                 next_handler: "DenominationHandler | None" = None) -> None:
        self.denomination = denomination
        self.count = count
        self.next_handler = next_handler

    def preview(self, amount: int) -> tuple[dict[int, int], int]:
        take = min(self.count, amount // self.denomination)
        notes = {self.denomination: take} if take else {}
        remaining = amount - take * self.denomination
        if remaining and self.next_handler is not None:
            downstream, remaining = self.next_handler.preview(remaining)
            notes.update(downstream)
        return notes, remaining

    def commit(self, notes: dict[int, int]) -> None:
        used = notes.get(self.denomination, 0)
        if used:
            self.count -= used
        if self.next_handler is not None:
            self.next_handler.commit(notes)

    def total(self) -> int:
        rest = self.next_handler.total() if self.next_handler is not None else 0
        return self.denomination * self.count + rest

    def smallest_denomination(self) -> int:
        return self.next_handler.smallest_denomination() if self.next_handler is not None else self.denomination


class CashDispenser:
    def __init__(self, denominations: dict[int, int]) -> None:
        if not denominations:
            raise ValueError("a dispenser needs at least one denomination")
        chain: DenominationHandler | None = None
        for denom in sorted(denominations):          # ascending: each new node becomes the new head,
            chain = DenominationHandler(denom, denominations[denom], chain)   # so the LARGEST ends up first
        self._head: DenominationHandler = chain  # type: ignore[assignment]

    def dispense(self, amount: int) -> dict[int, int]:
        notes, remaining = self._head.preview(amount)
        if remaining:
            raise InsufficientCash(f"cannot make {amount} from the cassettes on hand")
        self._head.commit(notes)
        return notes

    def total(self) -> int:
        return self._head.total()

    def smallest_denomination(self) -> int:
        return self._head.smallest_denomination()


class ATM:
    def __init__(self, bank: Bank, dispenser: CashDispenser, max_pin_attempts: int = 3) -> None:
        self._bank = bank
        self._dispenser = dispenser
        self._max_pin_attempts = max_pin_attempts
        self._state = State.IDLE
        self._card_id: str | None = None
        self._account_id: str | None = None
        self._pin_attempts = 0

    @property
    def state(self) -> State:
        return self._state

    def _require(self, *states: State) -> None:
        if self._state not in states:
            raise InvalidOperation(f"cannot do this in state {self._state.value}")

    def insert_card(self, card_id: str) -> None:
        self._require(State.IDLE)
        self._card_id = card_id
        self._account_id = None
        self._pin_attempts = 0
        self._state = State.CARD_INSERTED

    def enter_pin(self, pin: str) -> None:
        self._require(State.CARD_INSERTED)
        try:
            self._account_id = self._bank.authenticate(self._card_id, pin)  # type: ignore[arg-type]
        except AuthenticationFailed:
            self._pin_attempts += 1
            if self._pin_attempts >= self._max_pin_attempts:
                self._state = State.CARD_RETAINED
                raise CardRetained(f"card {self._card_id} retained after {self._pin_attempts} attempts") from None
            raise
        self._state = State.AUTHENTICATED

    def balance(self) -> int:
        self._require(State.AUTHENTICATED)
        return self._bank.balance(self._account_id)  # type: ignore[arg-type]

    def withdraw(self, amount: int) -> dict[int, int]:
        self._require(State.AUTHENTICATED)
        smallest = self._dispenser.smallest_denomination()
        if amount <= 0 or amount % smallest != 0:
            raise InvalidAmount(f"{amount} must be a positive multiple of {smallest}")
        account_id = self._account_id
        assert account_id is not None
        self._bank.debit(account_id, amount)          # may raise InsufficientFunds; nothing to undo
        try:
            return self._dispenser.dispense(amount)
        except InsufficientCash:
            self._bank.credit(account_id, amount)      # compensate: give it right back
            raise

    def eject_card(self) -> None:
        self._require(State.CARD_INSERTED, State.AUTHENTICATED)
        self._card_id = None
        self._account_id = None
        self._state = State.IDLE

    def service_reset(self) -> None:
        self._require(State.CARD_RETAINED)
        self._card_id = None
        self._account_id = None
        self._pin_attempts = 0
        self._state = State.IDLE


# ===================================================================== TESTS ==
def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _raises(exc, fn) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def _bank() -> FakeBank:
    return FakeBank(
        card_accounts={"card-1": "acc-1", "card-2": "acc-2"},
        pins={"card-1": "1234", "card-2": "0000"},
        balances={"acc-1": 1000, "acc-2": 40},
    )


def run_tests() -> bool:
    all_ok = True
    print("--- happy path: the chain across several denominations ---")
    bank = _bank()
    dispenser = CashDispenser({100: 2, 50: 1, 20: 3, 10: 5, 5: 4})
    atm = ATM(bank, dispenser)
    atm.insert_card("card-1")
    atm.enter_pin("1234")
    all_ok &= _check("authenticated", atm.state is State.AUTHENTICATED)
    all_ok &= _check("balance comes from the bank", atm.balance() == 1000)
    notes = atm.withdraw(370)
    all_ok &= _check("largest-denomination-first split across the whole chain",
                     notes == {100: 2, 50: 1, 20: 3, 10: 5, 5: 2})
    all_ok &= _check("bank was debited exactly once for 370", bank.debit_calls == [("acc-1", 370)])
    all_ok &= _check("cassette totals reflect exactly what was dispensed", dispenser.total() == 380 - 370)
    atm.eject_card()
    all_ok &= _check("ejecting returns to IDLE", atm.state is State.IDLE)

    print("\n--- wrong-order calls change nothing ---")
    fresh = ATM(_bank(), CashDispenser({20: 5}))
    all_ok &= _check("enter_pin before insert_card", _raises(InvalidOperation, lambda: fresh.enter_pin("1234")))
    all_ok &= _check("withdraw before authenticating", _raises(InvalidOperation, lambda: fresh.withdraw(20)))
    fresh.insert_card("card-1")
    all_ok &= _check("insert_card twice", _raises(InvalidOperation, lambda: fresh.insert_card("card-2")))
    all_ok &= _check("balance before authenticating", _raises(InvalidOperation, fresh.balance))

    print("\n--- PIN attempts and card retention ---")
    bank2 = _bank()
    atm2 = ATM(bank2, CashDispenser({20: 5}), max_pin_attempts=3)
    atm2.insert_card("card-1")
    all_ok &= _check("1st wrong PIN: recoverable", _raises(AuthenticationFailed, lambda: atm2.enter_pin("0000")))
    all_ok &= _check("still CARD_INSERTED after one miss", atm2.state is State.CARD_INSERTED)
    all_ok &= _check("2nd wrong PIN: still recoverable", _raises(AuthenticationFailed, lambda: atm2.enter_pin("1111")))
    all_ok &= _check("3rd wrong PIN: card retained", _raises(CardRetained, lambda: atm2.enter_pin("9999")))
    all_ok &= _check("state is CARD_RETAINED", atm2.state is State.CARD_RETAINED)
    all_ok &= _check("machine refuses further cards until serviced",
                     _raises(InvalidOperation, lambda: atm2.insert_card("card-2")))
    atm2.service_reset()
    all_ok &= _check("service_reset clears it", atm2.state is State.IDLE)
    atm2.insert_card("card-1")
    atm2.enter_pin("1234")
    all_ok &= _check("the account still works after a reset", atm2.state is State.AUTHENTICATED)

    print("\n--- invalid amounts never touch the bank ---")
    bank3 = _bank()
    atm3 = ATM(bank3, CashDispenser({20: 5}))
    atm3.insert_card("card-1")
    atm3.enter_pin("1234")
    all_ok &= _check("zero", _raises(InvalidAmount, lambda: atm3.withdraw(0)))
    all_ok &= _check("negative", _raises(InvalidAmount, lambda: atm3.withdraw(-20)))
    all_ok &= _check("not a multiple of the smallest note (20)", _raises(InvalidAmount, lambda: atm3.withdraw(15)))
    all_ok &= _check("none of that called the bank", bank3.debit_calls == [])

    print("\n--- insufficient FUNDS: the bank says no; the machine is never touched ---")
    bank4 = _bank()
    atm4 = ATM(bank4, CashDispenser({20: 5}))   # card-2 / acc-2 has balance 40
    atm4.insert_card("card-2")
    atm4.enter_pin("0000")
    all_ok &= _check("withdrawing more than the balance", _raises(InsufficientFunds, lambda: atm4.withdraw(60)))
    all_ok &= _check("balance is untouched", bank4.balances["acc-2"] == 40)
    all_ok &= _check("no compensation needed — nothing was ever debited", bank4.credit_calls == [])

    print("\n--- insufficient CASH: debited, then compensated ---")
    bank5 = _bank()
    # 100s and 20s only: 40 is coverable (2x20), but 40 needs exactly one 20 and
    # the machine has just ONE 20 note plus a 100 it can't use for a 40 request.
    dispenser5 = CashDispenser({100: 1, 20: 1})
    atm5 = ATM(bank5, dispenser5)
    atm5.insert_card("card-1")
    atm5.enter_pin("1234")
    before = bank5.balances["acc-1"]
    all_ok &= _check("machine can't make exact change even though 120 total cash sits inside it",
                     _raises(InsufficientCash, lambda: atm5.withdraw(40)))
    all_ok &= _check("the bank WAS debited once", bank5.debit_calls == [("acc-1", 40)])
    all_ok &= _check("...then credited back the same amount (compensation)",
                     bank5.credit_calls == [("acc-1", 40)])
    all_ok &= _check("net effect on the customer's balance is zero", bank5.balances["acc-1"] == before)
    all_ok &= _check("nothing was actually dispensed: cassette totals unchanged", dispenser5.total() == 120)

    print("\n--- atomic dispensing: partial matches never leave the chain half-drained ---")
    d = CashDispenser({50: 1, 20: 1})
    all_ok &= _check("70 is exactly 50+20", d.dispense(70) == {50: 1, 20: 1})
    d2 = CashDispenser({50: 1, 20: 1})
    all_ok &= _check("30 can't be made (50 too big, only one 20)", _raises(InsufficientCash, lambda: d2.dispense(30)))
    all_ok &= _check("failed dispense touched nothing", d2.total() == 70)
    return all_ok
# ================================================================= END TESTS ==


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO: a full session, several withdrawals, cassette total always reconciles ---")
    bank = _bank()
    bank.balances["acc-1"] = 100_000
    dispenser = CashDispenser({100: 20, 50: 20, 20: 30, 10: 30, 5: 20})
    start_total = dispenser.total()
    atm = ATM(bank, dispenser)
    atm.insert_card("card-1")
    atm.enter_pin("1234")
    dispensed_total = 0
    import random
    rng = random.Random(42)
    withdrawals = 0
    for _ in range(200):
        amount = rng.choice(range(5, 500, 5))
        try:
            notes = atm.withdraw(amount)
        except (InsufficientCash, InsufficientFunds):
            continue
        given = sum(denom * count for denom, count in notes.items())
        assert given == amount, "dispensed value must equal the request exactly"
        dispensed_total += given
        withdrawals += 1
    reconciled = dispenser.total() == start_total - dispensed_total
    print(f"      {withdrawals} withdrawals over {start_total} starting cash; "
          f"dispensed {dispensed_total}; cassette total {dispenser.total()} "
          f"(expected {start_total - dispensed_total})")
    all_ok &= _check("cassette total always equals starting cash minus everything actually handed out",
                     reconciled)
    all_ok &= _check("bank's outstanding debits match what was actually dispensed",
                     sum(a for _, a in bank.debit_calls) - sum(a for _, a in bank.credit_calls) == dispensed_total)

    print("\n--- DEMO: 1,000 forced compensations never leak or lose a unit of currency ---")
    bank2 = _bank()
    bank2.balances["acc-1"] = 10_000
    dispenser2 = CashDispenser({50: 1})   # can only ever dispense exactly 50
    atm2 = ATM(bank2, dispenser2)
    atm2.insert_card("card-1")
    atm2.enter_pin("1234")
    failures = 0
    for _ in range(1000):
        try:
            atm2.withdraw(100)             # never satisfiable with a single 50-note cassette
        except InsufficientCash:
            failures += 1
        dispenser2 = dispenser2            # cassette never mutates on failure; re-check below
    all_ok &= _check("every one of 1000 requests failed and compensated",
                     failures == 1000 and bank2.balances["acc-1"] == 10_000)
    all_ok &= _check("debit/credit pairs are exactly balanced",
                     len(bank2.debit_calls) == 1000 and len(bank2.credit_calls) == 1000
                     and sum(a for _, a in bank2.debit_calls) == sum(a for _, a in bank2.credit_calls))
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
