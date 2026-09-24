"""
================================================================================
LLD 005 · Splitwise (Expense Sharing)                              [Tier 1]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement the core of an expense-sharing app like Splitwise.

The interviewer says: "Design Splitwise." These are the agreed requirements.

REQUIREMENTS
------------
  1. Money is integer cents.
  2. add_expense(paid_by, amount_cents, participants, split=None, description="")
     -> Expense. `split` defaults to EqualSplit(). The payer may or may not be
     among the participants. Errors: UnknownUser; InvalidSplit for amount <= 0,
     empty or duplicate participants.
  3. Split strategies — split(amount_cents, participants) -> {user: cents}:
        EqualSplit()
        ExactSplit({user: cents})         must sum to the amount
        PercentSplit({user: percent})     percents may be int, float or str
                                          like "33.33"; must sum to exactly 100
        ShareSplit({user: weight})        proportional to integer weights
     Rules for all of them:
        * shares sum to EXACTLY the amount;
        * the split's users must be exactly the participants, else InvalidSplit;
        * negative values -> InvalidSplit;
        * rounding: floor each exact share, then give the leftover cents one
          each to the largest fractional parts; ties go to whoever is listed
          first in `participants`.
  4. balance(user) -> cents (positive = is owed). balances() -> {user: cents}.
  5. debts() -> {(debtor, creditor): cents}, NET per pair (never both
     directions), only positive entries.
  6. record_payment(from_user, to_user, cents): from_user pays to_user.
  7. simplify(strategy=None) -> [Payment(debtor, creditor, cents)] that zeroes
     every balance.
        GreedySettlement   largest debtor pays largest creditor (default)
        OptimalSettlement  the minimum possible number of payments

  Out of scope: currencies, groups, notifications.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * How do three people split 10.00 without losing or inventing a cent?
  * Is the split type an enum with if/elif, or something else? Why?
  * What invariant must the ledger always satisfy?
  * Is greedy settlement minimal? What's the complexity of the true minimum?

FOLLOW-UPS TO PREPARE
---------------------
  groups · multiple currencies · editing an expense · several payers ·
  recurring expenses · storing the ledger in a database.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Expense:
    id: int
    description: str
    paid_by: str
    amount_cents: int
    shares: dict[str, int]


@dataclass(frozen=True, slots=True)
class Payment:
    debtor: str
    creditor: str
    cents: int


class SplitError(Exception): ...
class InvalidSplit(SplitError): ...
class UnknownUser(SplitError): ...


class EqualSplit:
    def split(self, amount_cents: int, participants: list[str]) -> dict[str, int]:
        raise NotImplementedError


class ExactSplit:
    def __init__(self, amounts: dict[str, int]) -> None:
        raise NotImplementedError


class PercentSplit:
    def __init__(self, percents: dict[str, float | int | str]) -> None:
        raise NotImplementedError


class ShareSplit:
    def __init__(self, weights: dict[str, int]) -> None:
        raise NotImplementedError


class GreedySettlement:
    def settle(self, balances: dict[str, int]) -> list[Payment]:
        raise NotImplementedError


class OptimalSettlement:
    def settle(self, balances: dict[str, int]) -> list[Payment]:
        raise NotImplementedError


class ExpenseManager:
    def __init__(self) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def add_user(self, user: str) -> None:
        raise NotImplementedError

    def add_expense(self, paid_by: str, amount_cents: int, participants: list[str],
                    split=None, description: str = "") -> Expense:
        raise NotImplementedError

    def record_payment(self, from_user: str, to_user: str, cents: int) -> None:
        raise NotImplementedError

    def balance(self, user: str) -> int:
        raise NotImplementedError

    def balances(self) -> dict[str, int]:
        raise NotImplementedError

    def debts(self) -> dict[tuple[str, str], int]:
        raise NotImplementedError

    def simplify(self, strategy=None) -> list[Payment]:
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


def _manager(*users: str) -> ExpenseManager:
    m = ExpenseManager()
    for u in users:
        m.add_user(u)
    return m


def _settles(balances: dict[str, int], payments: list[Payment]) -> bool:
    left = dict(balances)
    for p in payments:
        if p.cents <= 0:
            return False
        left[p.debtor] += p.cents
        left[p.creditor] -= p.cents
    return all(v == 0 for v in left.values())


def run_tests() -> bool:
    all_ok = True
    print("--- splits sum exactly ---")
    all_ok &= _check("equal 1000 / 3 -> 334, 333, 333 (extra cent to first listed)",
                     EqualSplit().split(1000, ["A", "B", "C"]) == {"A": 334, "B": 333, "C": 333})
    all_ok &= _check("percent 33.33/33.33/33.34 of 1000 -> 333, 333, 334",
                     PercentSplit({"A": "33.33", "B": 33.33, "C": 33.34}).split(1000, ["A", "B", "C"])
                     == {"A": 333, "B": 333, "C": 334})
    all_ok &= _check("shares 1:2:3 of 1000 -> 167, 333, 500",
                     ShareSplit({"A": 1, "B": 2, "C": 3}).split(1000, ["A", "B", "C"])
                     == {"A": 167, "B": 333, "C": 500})
    all_ok &= _check("exact shares not summing to total -> InvalidSplit",
                     _raises(InvalidSplit, lambda: ExactSplit({"A": 500, "B": 400}).split(1000, ["A", "B"])))
    all_ok &= _check("percents summing to 99 -> InvalidSplit",
                     _raises(InvalidSplit, lambda: PercentSplit({"A": 50, "B": 49}).split(1000, ["A", "B"])))
    all_ok &= _check("split naming people who aren't participants -> InvalidSplit",
                     _raises(InvalidSplit, lambda: ExactSplit({"A": 1000}).split(1000, ["B"])))

    print("\n--- ledger balances and pairwise debts ---")
    m = _manager("ann", "bob", "cat")
    m.add_expense("ann", 3000, ["ann", "bob", "cat"], description="dinner")
    all_ok &= _check("ann paid 3000 for three: ann +2000, bob -1000, cat -1000",
                     m.balances() == {"ann": 2000, "bob": -1000, "cat": -1000})
    m.add_expense("bob", 600, ["ann", "bob"], ExactSplit({"ann": 300, "bob": 300}))
    all_ok &= _check("bob paid 600 split with ann: pair nets to bob owes ann 700",
                     m.debts() == {("bob", "ann"): 700, ("cat", "ann"): 1000})
    m.record_payment("cat", "ann", 1000)
    all_ok &= _check("cat pays ann 1000 -> cat settled", m.balance("cat") == 0 and ("cat", "ann") not in m.debts())
    all_ok &= _check("sum of balances is zero", sum(m.balances().values()) == 0)
    m.add_expense("ann", 500, ["bob"])
    all_ok &= _check("payer need not be a participant: bob owes ann 1200", m.debts()[("bob", "ann")] == 1200)
    m.add_expense("cat", 900, ["cat"])
    all_ok &= _check("payer as only participant creates no debt", m.balance("cat") == 0)
    all_ok &= _check("unknown user", _raises(UnknownUser, lambda: m.add_expense("zed", 100, ["ann"])))
    all_ok &= _check("non-positive amount", _raises(InvalidSplit, lambda: m.add_expense("ann", 0, ["bob"])))

    print("\n--- simplify ---")
    m = _manager("A", "B", "C")
    m.add_expense("B", 1000, ["A"])          # A owes B 10
    m.add_expense("C", 1000, ["B"])          # B owes C 10
    all_ok &= _check("chain A->B->C collapses to one payment A->C",
                     m.simplify() == [Payment("A", "C", 1000)])
    balances = {"a": -500, "b": 500, "c": -300, "d": 300, "e": -700, "f": 400, "g": 300}
    greedy, best = GreedySettlement().settle(balances), OptimalSettlement().settle(balances)
    all_ok &= _check(f"both plans zero every balance (greedy {len(greedy)}, optimal {len(best)} payments)",
                     _settles(balances, greedy) and _settles(balances, best))
    all_ok &= _check("optimal finds the 3 independent groups -> 4 payments", len(best) == 4)
    return all_ok
# ================================================================= END TESTS ==


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
