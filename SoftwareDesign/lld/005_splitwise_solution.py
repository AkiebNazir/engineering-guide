"""
================================================================================
SOLUTION · LLD 005 · Splitwise (Expense Sharing)                   [Tier 1]
================================================================================

THE CORE IDEA
--------------
Three separable pieces, and each has one trap:

    1. SPLITTING an amount  -> SplitStrategy (equal / exact / percent / shares)
       Trap: rounding. 1000 cents / 3 is 333.33... The shares MUST sum to exactly
       the amount, deterministically. Use integer cents and the LARGEST-REMAINDER
       method: floor every share, then hand the leftover cents one at a time to
       the shares with the biggest fractional parts.

    2. RECORDING who owes whom -> ExpenseManager (the ledger)
       Invariant: the sum of all balances is ALWAYS exactly zero. Money is only
       ever moved between people, never created. Demo 1 shows floats breaking it.

    3. SETTLING UP with few payments -> SettlementStrategy
       Greedy (biggest debtor pays biggest creditor) needs at most n-1 payments
       and is what the app ships. The true minimum is NP-hard (it's finding
       the most disjoint zero-sum subgroups); a bitmask DP solves it exactly for
       small groups. Demo 2 measures how often greedy is not optimal.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. Users; add_expense(paid_by, amount, participants, split).
  2. Split types: EQUAL, EXACT amounts, PERCENT, SHARES (weights).
     Shares always sum to the amount exactly. The payer may or may not be a
     participant.
  3. balance(user): positive = others owe them, negative = they owe.
  4. debts(): net pairwise amounts ("Bob owes Ann 7.00").
  5. record_payment(from, to, amount) — settling up.
  6. simplify(): a list of payments that zeros every balance, few payments.
  Out of scope: currencies, groups (as persistence), notifications, auth.


================================================================================
ENTITIES, VALUE OBJECTS, INVARIANTS
================================================================================
    Expense               value object: id, description, payer, amount, shares
    Payment               value object: (debtor, creditor, cents)
    SplitStrategy         split(amount, participants) -> {user: cents}
       EqualSplit / ExactSplit / PercentSplit / ShareSplit
       INVARIANT: sum(shares) == amount, every share >= 0
    ExpenseManager        ledger; INVARIANTS: sum(balances) == 0;
                          pairwise net debt stored in one direction only
    SettlementStrategy    settle(balances) -> [Payment]
       GreedySettlement   <= n-1 payments, O(n log n)
       OptimalSettlement  minimum payments, O(2^n * n), n <= 20


================================================================================
CLASS DIAGRAM
================================================================================
    ┌──────────────────────────────────┐        «protocol» SplitStrategy
    │ ExpenseManager                   │ uses    ▲ EqualSplit   ▲ ExactSplit
    ├──────────────────────────────────┤───────▶ ▲ PercentSplit ▲ ShareSplit
    │ - _balance: {user: cents}        │
    │ - _owes: {(debtor, creditor): c} │        «protocol» SettlementStrategy
    │ - _expenses: [Expense]           │ uses    ▲ GreedySettlement
    ├──────────────────────────────────┤───────▶ ▲ OptimalSettlement
    │ + add_expense(...) -> Expense    │
    │ + record_payment(a, b, cents)    │
    │ + balance(u) / debts()           │
    │ + simplify(strategy) -> [Payment]│
    └──────────────────────────────────┘


================================================================================
LARGEST-REMAINDER TRACE · 1000 cents, PERCENT {A: 33.33, B: 33.33, C: 33.34}
================================================================================
    exact share    floor   fractional part
    A  333.3       333     .3
    B  333.3       333     .3
    C  333.4       333     .4     floors sum to 999 -> 1 cent left over
    leftover cent -> biggest fraction (C)          -> A 333, B 333, C 334 = 1000
    Ties are broken by the order participants were given, so results are
    reproducible on every machine.


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Integer cents everywhere; percentages parsed with Fraction(str(p)) so
    "33.33" is exactly 3333/100, not 33.3299999.
  * Split as strategy objects (not an enum + if/elif): each carries its own
    parameters (exact amounts, weights) and validation. A new split type is a
    new class.
  * The ledger keeps BOTH per-user balances (O(1) balance query) and pairwise
    debts (for "who owes whom" before simplification). Pairwise entries are
    netted on write so (A owes B 5, B owes A 3) is stored as A owes B 2.
  * Simplification is a strategy because "fewest payments" and "only pay people
    you actually shared with" are different product decisions.
  * Expenses are immutable records; edits are modeled as a reversing expense +
    a new one (audit trail for free).


================================================================================
COMPLEXITY
================================================================================
    Operation          Time                 Space
    add_expense        O(p)  p participants O(p)
    record_payment     O(1)                 O(1)
    balance            O(1)
    debts              O(pairs)
    GreedySettlement   O(n log n)           O(n)
    OptimalSettlement  O(2^n * n)           O(2^n)


================================================================================
EDGE CASES
================================================================================
  * Amount not divisible by participants -> extra cents deterministic.
  * Exact amounts not summing to total / percents not summing to 100 -> InvalidSplit.
  * Negative amount or share -> InvalidSplit.
  * Payer not a participant (paid for friends only).
  * Payer is the only participant -> no debt at all.
  * Unknown user -> UnknownUser.
  * Paying more than owed -> direction flips (allowed; it's a transfer).
  * Debt chains A->B->C simplify to A->C.


================================================================================
COMMON MISTAKES
================================================================================
  1. Float money; shares that sum to 999 or 1001.
  2. Rounding every share independently (round(1000/3) * 3 = 999).
  3. `if split_type == "EQUAL": ... elif ...` growing in the manager.
  4. Storing A->B and B->A separately and never netting them.
  5. Claiming greedy settlement is minimal (it isn't; say NP-hard).
  6. Recomputing balances by replaying every expense on each query.
  7. Letting a strategy produce shares for users who aren't participants.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Groups                  -> Group owns member list + its own ledger; the
                               user's global balance is the sum over groups.
  * Multiple currencies     -> Money(amount, currency) value object; balances
                               per currency; convert only at settlement time.
  * Edit / delete expense   -> reverse the old shares, apply the new (event log).
  * Recurring expenses      -> scheduler creating Expense from a template.
  * Several payers          -> Expense.paid: {user: cents}; same ledger math.
  * Scale                   -> ledger rows per (group, debtor, creditor) updated
                               in one DB transaction with the expense insert.


================================================================================
RELATED
================================================================================
  SoftwareDesign/04_design_patterns_in_practice.md  §3 Strategy
  SoftwareDesign/02_oop_and_domain_modeling.md      §3 Invariants, §7 Value objects
  PyDSA bitmask DP (optimal account balancing, LC 465)
  lld/003_vending_machine (money in cents, conservation invariant)
"""

from __future__ import annotations

import heapq
import itertools
import random
from dataclasses import dataclass
from fractions import Fraction
from typing import Protocol


# ----------------------------------------------------------------------------
# Value objects and errors
# ----------------------------------------------------------------------------
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


def allocate(amount: int, weights: list[tuple[str, Fraction]]) -> dict[str, int]:
    """Largest-remainder apportionment: integer shares proportional to weights, summing to amount."""
    total = sum(w for _, w in weights)
    if total <= 0:
        raise InvalidSplit("weights must sum to a positive number")
    exact = [(user, amount * w / total) for user, w in weights]
    shares = {user: int(x) for user, x in exact}           # floor (x >= 0)
    leftover = amount - sum(shares.values())
    order = sorted(range(len(exact)), key=lambda i: (-(exact[i][1] - int(exact[i][1])), i))
    for i in order[:leftover]:
        shares[exact[i][0]] += 1
    return shares


# ----------------------------------------------------------------------------
# Split strategies
# ----------------------------------------------------------------------------
class SplitStrategy(Protocol):
    def split(self, amount_cents: int, participants: list[str]) -> dict[str, int]: ...


class EqualSplit:
    def split(self, amount_cents, participants):
        return allocate(amount_cents, [(p, Fraction(1)) for p in participants])


class ExactSplit:
    def __init__(self, amounts: dict[str, int]) -> None:
        self._amounts = dict(amounts)

    def split(self, amount_cents, participants):
        _same_people(self._amounts, participants)
        if any(a < 0 for a in self._amounts.values()):
            raise InvalidSplit("negative share")
        if sum(self._amounts.values()) != amount_cents:
            raise InvalidSplit(f"exact shares sum to {sum(self._amounts.values())}, not {amount_cents}")
        return {p: self._amounts[p] for p in participants}


class PercentSplit:
    def __init__(self, percents: dict[str, float | int | str]) -> None:
        self._pct = {u: Fraction(str(p)) for u, p in percents.items()}

    def split(self, amount_cents, participants):
        _same_people(self._pct, participants)
        if any(p < 0 for p in self._pct.values()):
            raise InvalidSplit("negative percent")
        if sum(self._pct.values()) != 100:
            raise InvalidSplit(f"percents sum to {float(sum(self._pct.values()))}, not 100")
        return allocate(amount_cents, [(p, self._pct[p]) for p in participants])


class ShareSplit:
    def __init__(self, weights: dict[str, int]) -> None:
        self._weights = dict(weights)

    def split(self, amount_cents, participants):
        _same_people(self._weights, participants)
        if any(w < 0 for w in self._weights.values()):
            raise InvalidSplit("negative weight")
        return allocate(amount_cents, [(p, Fraction(self._weights[p])) for p in participants])


def _same_people(spec: dict[str, object], participants: list[str]) -> None:
    if set(spec) != set(participants):
        raise InvalidSplit(f"split names {sorted(spec)} but participants are {sorted(participants)}")


# ----------------------------------------------------------------------------
# Settlement strategies
# ----------------------------------------------------------------------------
class SettlementStrategy(Protocol):
    def settle(self, balances: dict[str, int]) -> list[Payment]: ...


class GreedySettlement:
    """Largest debtor pays largest creditor. At most n-1 payments."""

    def settle(self, balances):
        creditors = [(-b, u) for u, b in balances.items() if b > 0]
        debtors = [(b, u) for u, b in balances.items() if b < 0]
        heapq.heapify(creditors)
        heapq.heapify(debtors)
        out = []
        while creditors and debtors:
            c_amt, c = heapq.heappop(creditors)
            d_amt, d = heapq.heappop(debtors)
            pay = min(-c_amt, -d_amt)
            out.append(Payment(d, c, pay))
            if -c_amt > pay:
                heapq.heappush(creditors, (c_amt + pay, c))
            if -d_amt > pay:
                heapq.heappush(debtors, (d_amt + pay, d))
        return out


class OptimalSettlement:
    """Minimum payments = n - (max number of disjoint zero-sum groups). Bitmask DP."""

    MAX_PEOPLE = 20

    def settle(self, balances):
        people = [u for u, b in balances.items() if b != 0]
        n = len(people)
        if n > self.MAX_PEOPLE:
            raise ValueError(f"exact settlement is exponential; {n} people > {self.MAX_PEOPLE}")
        amt = [balances[u] for u in people]
        full = (1 << n) - 1
        total = [0] * (1 << n)
        for mask in range(1, 1 << n):
            low = (mask & -mask).bit_length() - 1
            total[mask] = total[mask & (mask - 1)] + amt[low]
        groups = [0] * (1 << n)               # max zero-sum groups completing along some order
        parent = [0] * (1 << n)
        for mask in range(1, 1 << n):
            best, arg = -1, 0
            m = mask
            while m:
                bit = m & -m
                if groups[mask ^ bit] > best:
                    best, arg = groups[mask ^ bit], mask ^ bit
                m ^= bit
            groups[mask] = best + (1 if total[mask] == 0 else 0)
            parent[mask] = arg
        # Walk back, cutting a group every time the prefix sum returns to zero.
        payments: list[Payment] = []
        mask, group_mask = full, 0
        while mask:
            prev = parent[mask]
            group_mask |= mask ^ prev
            if total[prev] == 0:
                sub = {people[i]: amt[i] for i in range(n) if group_mask >> i & 1}
                payments.extend(GreedySettlement().settle(sub))
                group_mask = 0
            mask = prev
        return payments


# ----------------------------------------------------------------------------
# ExpenseManager — the ledger
# ----------------------------------------------------------------------------
class ExpenseManager:
    def __init__(self) -> None:
        self._balance: dict[str, int] = {}
        self._owes: dict[tuple[str, str], int] = {}
        self._expenses: list[Expense] = []
        self._ids = itertools.count(1)

    def add_user(self, user: str) -> None:
        self._balance.setdefault(user, 0)

    def add_expense(self, paid_by: str, amount_cents: int, participants: list[str],
                    split: SplitStrategy | None = None, description: str = "") -> Expense:
        self._known(paid_by, *participants)
        if amount_cents <= 0:
            raise InvalidSplit("amount must be positive")
        if not participants or len(set(participants)) != len(participants):
            raise InvalidSplit("participants must be non-empty and unique")
        shares = (split or EqualSplit()).split(amount_cents, list(participants))
        if sum(shares.values()) != amount_cents or any(v < 0 for v in shares.values()):
            raise InvalidSplit("strategy broke the split invariant")     # never trust a plug-in
        expense = Expense(next(self._ids), description, paid_by, amount_cents, shares)
        for user, share in shares.items():
            self._transfer(debtor=user, creditor=paid_by, cents=share)
        self._expenses.append(expense)
        return expense

    def record_payment(self, from_user: str, to_user: str, cents: int) -> None:
        self._known(from_user, to_user)
        if cents <= 0 or from_user == to_user:
            raise InvalidSplit("payment must be positive and between two people")
        self._transfer(debtor=to_user, creditor=from_user, cents=cents)

    def balance(self, user: str) -> int:
        self._known(user)
        return self._balance[user]

    def balances(self) -> dict[str, int]:
        return dict(self._balance)

    def debts(self) -> dict[tuple[str, str], int]:
        """{(debtor, creditor): cents} — net, one direction per pair."""
        return {k: v for k, v in self._owes.items() if v > 0}

    def simplify(self, strategy: SettlementStrategy | None = None) -> list[Payment]:
        return (strategy or GreedySettlement()).settle(self.balances())

    def _transfer(self, debtor: str, creditor: str, cents: int) -> None:
        """debtor now owes creditor `cents` more (a payment is the reverse transfer)."""
        if debtor == creditor or cents == 0:
            return
        self._balance[debtor] -= cents
        self._balance[creditor] += cents
        reverse = self._owes.pop((creditor, debtor), 0)
        net = self._owes.pop((debtor, creditor), 0) + cents - reverse
        if net > 0:
            self._owes[(debtor, creditor)] = net
        elif net < 0:
            self._owes[(creditor, debtor)] = -net

    def _known(self, *users: str) -> None:
        for u in users:
            if u not in self._balance:
                raise UnknownUser(u)


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


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: 100,000 three-way splits in floats vs integer cents ---")
    rng = random.Random(5)
    float_bal = {"A": 0.0, "B": 0.0, "C": 0.0}
    rounded_lost = 0
    m = _manager("A", "B", "C")
    for _ in range(100_000):
        cents = rng.randrange(1, 100_000)
        payer = rng.choice("ABC")
        dollars = cents / 100
        share = dollars / 3
        for u in "ABC":
            float_bal[u] -= share
        float_bal[payer] += dollars
        rounded_lost += cents - 3 * round(cents / 3)
        m.add_expense(payer, cents, ["A", "B", "C"])
    drift = sum(float_bal.values())
    print(f"      float ledger sum: {drift!r} dollars (should be exactly 0)")
    print(f"      round-each-share ledger: {rounded_lost} cents created or destroyed")
    print(f"      integer ledger sum: {sum(m.balances().values())} cents")
    all_ok &= _check("integer ledger sums to exactly zero; float and per-share rounding do not",
                     sum(m.balances().values()) == 0 and drift != 0 and rounded_lost != 0)

    print("\n--- DEMO 2: greedy vs optimal settlement on 400 random 10-person groups ---")
    rng = random.Random(9)
    worse, extra_max, n_greedy, n_opt = 0, 0, 0, 0
    for _ in range(400):
        balances: dict[str, int] = {}
        names = iter(f"p{i}" for i in range(10))
        people_left = 10
        while people_left >= 2:                         # build hidden zero-sum subgroups
            k = min(people_left, rng.choice([2, 3, 4]))
            vals = [rng.randrange(1, 50) * 100 * rng.choice([-1, 1]) for _ in range(k - 1)]
            vals.append(-sum(vals))
            for v in vals:
                balances[next(names)] = v
            people_left -= k
        g, o = GreedySettlement().settle(balances), OptimalSettlement().settle(balances)
        assert _settles(balances, g) and _settles(balances, o)
        n_greedy += len(g)
        n_opt += len(o)
        if len(g) > len(o):
            worse += 1
            extra_max = max(extra_max, len(g) - len(o))
    print(f"      greedy used more payments than optimal in {worse}/400 groups "
          f"(total {n_greedy} vs {n_opt}, worst case +{extra_max})")
    all_ok &= _check("optimal is never worse and greedy is measurably suboptimal",
                     n_opt <= n_greedy and worse > 0)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
