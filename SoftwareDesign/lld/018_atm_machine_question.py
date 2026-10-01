"""
================================================================================
LLD 018 · ATM Machine                                               [Tier 2]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design the software inside a single ATM: card in, PIN, check balance,
withdraw cash. The bank's ledger is a separate system the ATM talks to over
a port — this machine never touches an account balance directly, only
through that port.

The interviewer says: "Design one ATM, not the network of machines or the
bank's core ledger." These are the agreed requirements.

REQUIREMENTS
------------
  1. One session at a time, in this order:
       insert_card(card_id)              IDLE -> CARD_INSERTED
       enter_pin(pin)                    CARD_INSERTED -> AUTHENTICATED (on success)
       balance() / withdraw(amount)      only while AUTHENTICATED
       eject_card()                      back to IDLE
     Any call made in the wrong state raises InvalidOperation and changes
     nothing.
  2. Wrong PIN: raises AuthenticationFailed and stays in CARD_INSERTED so the
     caller can retry. After max_pin_attempts (default 3) wrong PINs in one
     session, the state becomes CARD_RETAINED and that call raises
     CardRetained instead. CARD_RETAINED accepts no further card-facing
     calls until a technician calls service_reset().
  3. withdraw(amount): amount must be a positive multiple of the machine's
     smallest note, else InvalidAmount, and nothing is called on the bank.
     Otherwise: debit the bank first, THEN try to dispense the cash. If the
     bank can't cover it, InsufficientFunds propagates and the machine was
     never touched. If the bank succeeds but the *machine* can't make that
     exact amount out of the notes it has left, credit the bank back for the
     same amount (compensation) and raise InsufficientCash — the customer's
     balance must be exactly what it was before the attempt.
  4. Cash lives in denomination cassettes (e.g. {100: 2, 50: 1, 20: 3, 10: 5,
     5: 2}). withdraw returns the exact notes given, largest denomination
     first, e.g. {100: 2, 20: 1}. It must never partially dispense: either
     the full amount comes out or none of it does, and the cassette counts
     only change on success.
  Out of scope: multiple concurrent ATMs (each machine serves one customer
  at a time; concurrency belongs to the bank's own port implementation),
  deposits, receipts, card networks.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * A state machine that actually forbids illegal call orders, not a
    class that trusts the caller.
  * The bank as an injected port (an interface), never a concrete class the
    ATM constructs itself — see `08_application_architecture_in_code.md` §3.
  * Recognising that "debit, then dispense" is TWO systems with no shared
    transaction, so a mid-way failure needs an explicit compensating action
    — see `06_error_handling_and_failure_design.md` §9.
  * Cash dispensing as a chain of denomination handlers (Chain of
    Responsibility, `04_design_patterns_in_practice.md` §11), each one
    taking what it can and passing the rest down — and computing the split
    as a dry-run BEFORE committing any cassette, so a request that can't be
    made exactly never touches inventory at all.
  * Telling this apart from `003_vending_machine`: a vending machine makes
    *change* for whatever was inserted (any amount can be reached with
    coins); an ATM must dispense the *exact requested amount* in notes, and
    it answers to an external ledger it doesn't own.

FOLLOW-UPS TO PREPARE
----------------------
  daily withdrawal limits · deposits (cash/cheque, provisional credit) ·
  card capture / fraud rules · offline mode with a reconciliation queue ·
  multi-currency cassettes · receipt printer as another chained device.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
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
        raise NotImplementedError

    def balance(self, account_id: str) -> int:
        raise NotImplementedError

    def debit(self, account_id: str, amount: int) -> None:
        raise NotImplementedError

    def credit(self, account_id: str, amount: int) -> None:
        raise NotImplementedError


class DenominationHandler:
    """One link in the cassette chain: handles what it can, passes the rest on."""

    def __init__(self, denomination: int, count: int,
                 next_handler: "DenominationHandler | None" = None) -> None:
        raise NotImplementedError

    def preview(self, amount: int) -> tuple[dict[int, int], int]:
        """Dry run: (notes this chain WOULD give, amount left unpaid). No mutation."""
        raise NotImplementedError

    def commit(self, notes: dict[int, int]) -> None:
        """Deducts exactly the notes a prior preview() said were available."""
        raise NotImplementedError

    def total(self) -> int:
        raise NotImplementedError

    def smallest_denomination(self) -> int:
        raise NotImplementedError


class CashDispenser:
    def __init__(self, denominations: dict[int, int]) -> None:
        # YOUR CODE HERE — build the DenominationHandler chain, largest first.
        raise NotImplementedError

    def dispense(self, amount: int) -> dict[int, int]:
        """Atomic: full amount or none. Raises InsufficientCash on failure."""
        raise NotImplementedError

    def total(self) -> int:
        raise NotImplementedError

    def smallest_denomination(self) -> int:
        raise NotImplementedError


class ATM:
    def __init__(self, bank: Bank, dispenser: CashDispenser, max_pin_attempts: int = 3) -> None:
        raise NotImplementedError

    @property
    def state(self) -> State:
        raise NotImplementedError

    def insert_card(self, card_id: str) -> None:
        raise NotImplementedError

    def enter_pin(self, pin: str) -> None:
        raise NotImplementedError

    def balance(self) -> int:
        raise NotImplementedError

    def withdraw(self, amount: int) -> dict[int, int]:
        raise NotImplementedError

    def eject_card(self) -> None:
        raise NotImplementedError

    def service_reset(self) -> None:
        """Technician action: clears CARD_RETAINED back to IDLE."""
        raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
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


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
