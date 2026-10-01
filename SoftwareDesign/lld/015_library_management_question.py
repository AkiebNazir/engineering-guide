"""
================================================================================
LLD 015 · Library Management System                                [Tier 2]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement the circulation core of a public library.

This question tests domain modeling. Before writing code, list your nouns and
decide which are entities, which are value objects, and which rule each one
owns. These are the agreed requirements.

REQUIREMENTS
------------
  1. Time comes from an injected clock in seconds; DAY = 86_400.
     Money is integer cents.
  2. Catalogue: add_book(Book(isbn, title, authors)), add_copy(isbn, barcode)
     (a Book can have many physical copies), search(text) -> Books whose title
     or any author contains text (case-insensitive), sorted by title.
  3. register(Member(id, name, policy=STANDARD)).
        STANDARD: max 3 open loans, 14-day loans, 1 renewal
        PREMIUM:  max 10 open loans, 28-day loans, 3 renewals
  4. checkout(member_id, barcode) -> Loan(id, member_id, barcode, isbn,
     borrowed_at, due_at, returned_at, renewals, fine_cents)
     Refuse with:
        NotAvailable    copy on loan / lost / on hold for someone else
        UnpaidFines     member.balance_cents > 1000
        LimitReached    member at the policy's max loans
        AlreadyBorrowed member already has an open loan for that ISBN
  5. return_copy(barcode) -> ReturnReceipt(loan, fine_cents, held_for)
        NotOnLoan if the copy has no open loan (e.g. scanned twice).
        days_late = ceil((now - due_at) / DAY) if now > due_at, else 0.
        fine = fine_policy.fine(days_late), added to the member's balance.
        If members are waiting for the ISBN, the copy goes ON_HOLD for the
        first one who doesn't already have that ISBN on loan, for 3 days
        (held_for = that member); otherwise AVAILABLE.
  6. Fine policies: PerDayFine(cents_per_day, cap_cents) (default 25/day, cap
     2000); GracePeriod(inner, days) — the first `days` late days are free.
  7. reserve(member_id, isbn) -> 1-based queue position. ReservationDenied if
     a copy is AVAILABLE, the member already has that ISBN on loan or on hold,
     or is already in the queue.
  8. A hold that isn't picked up within 3 days passes to the next member in the
     queue (or the copy becomes AVAILABLE). No background threads.
  9. renew(loan_id) -> new due_at (+ policy loan days). RenewalDenied if
     overdue, renewal limit reached, or anyone is waiting for the ISBN.
 10. mark_lost(barcode) -> total charged: late fine + 3000 replacement; closes
     the loan; copy LOST.
 11. pay(member_id, cents) -> remaining balance. copy(barcode) -> BookCopy
     (status, hold_for, ...). loans_of(member_id) -> open loans.
     NotFound for unknown ids.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * Book vs BookCopy. Is a Loan an entity or a flag?
  * Where do "can this member borrow?" rules live?
  * Reservations per copy or per title?
  * Fines as a strategy; money and time handling.
  * What happens on a double scan at the return desk?

FOLLOW-UPS TO PREPARE
---------------------
  multiple branches · due-soon notifications · e-book licences ·
  many desks concurrently · reporting.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

DAY = 86_400.0


class LibraryError(Exception): ...
class NotFound(LibraryError): ...
class NotAvailable(LibraryError): ...
class LimitReached(LibraryError): ...
class UnpaidFines(LibraryError): ...
class AlreadyBorrowed(LibraryError): ...
class NotOnLoan(LibraryError): ...
class RenewalDenied(LibraryError): ...
class ReservationDenied(LibraryError): ...


@dataclass(frozen=True, slots=True)
class MembershipPolicy:
    name: str
    max_loans: int
    loan_days: int
    max_renewals: int


STANDARD = MembershipPolicy("standard", max_loans=3, loan_days=14, max_renewals=1)
PREMIUM = MembershipPolicy("premium", max_loans=10, loan_days=28, max_renewals=3)


class PerDayFine:
    def __init__(self, cents_per_day: int, cap_cents: int) -> None:
        raise NotImplementedError

    def fine(self, days_late: int) -> int:
        raise NotImplementedError


class GracePeriod:
    def __init__(self, inner, days: int) -> None:
        raise NotImplementedError

    def fine(self, days_late: int) -> int:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Book:
    isbn: str
    title: str
    authors: tuple[str, ...]


class CopyStatus(Enum):
    AVAILABLE = "available"
    ON_LOAN = "on_loan"
    ON_HOLD = "on_hold"
    LOST = "lost"


@dataclass(slots=True)
class BookCopy:
    barcode: str
    isbn: str
    status: CopyStatus = CopyStatus.AVAILABLE
    hold_for: str | None = None
    hold_until: float = 0.0


@dataclass(slots=True)
class Member:
    id: str
    name: str
    policy: MembershipPolicy = STANDARD
    balance_cents: int = 0


@dataclass(slots=True)
class Loan:
    id: int
    member_id: str
    barcode: str
    isbn: str
    borrowed_at: float
    due_at: float
    returned_at: float | None = None
    renewals: int = 0
    fine_cents: int = 0


@dataclass(frozen=True, slots=True)
class ReturnReceipt:
    loan: Loan
    fine_cents: int
    held_for: str | None


class Library:
    def __init__(self, fines=None, clock: Callable[[], float] = time.time) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def add_book(self, book: Book) -> None: raise NotImplementedError
    def add_copy(self, isbn: str, barcode: str) -> BookCopy: raise NotImplementedError
    def register(self, member: Member) -> Member: raise NotImplementedError
    def search(self, text: str) -> list[Book]: raise NotImplementedError
    def checkout(self, member_id: str, barcode: str) -> Loan: raise NotImplementedError
    def return_copy(self, barcode: str) -> ReturnReceipt: raise NotImplementedError
    def renew(self, loan_id: int) -> float: raise NotImplementedError
    def reserve(self, member_id: str, isbn: str) -> int: raise NotImplementedError
    def mark_lost(self, barcode: str) -> int: raise NotImplementedError
    def pay(self, member_id: str, cents: int) -> int: raise NotImplementedError
    def copy(self, barcode: str) -> BookCopy: raise NotImplementedError
    def loans_of(self, member_id: str) -> list[Loan]: raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _raises(exc, fn) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def _library(clock: FakeClock) -> Library:
    lib = Library(PerDayFine(25, cap_cents=2_000), clock)
    lib.add_book(Book("111", "Designing Data-Intensive Applications", ("Martin Kleppmann",)))
    lib.add_book(Book("222", "A Philosophy of Software Design", ("John Ousterhout",)))
    lib.add_copy("111", "D1")
    lib.add_copy("111", "D2")
    lib.add_copy("222", "P1")
    for mid in ("ann", "bob", "cat"):
        lib.register(Member(mid, mid.title()))
    lib.register(Member("vip", "Vip", PREMIUM))
    return lib


def run_tests() -> bool:
    all_ok = True
    print("--- catalogue ---")
    clock = FakeClock()
    lib = _library(clock)
    all_ok &= _check("search by title or author, case-insensitive",
                     [b.isbn for b in lib.search("design")] == ["222", "111"]
                     and [b.isbn for b in lib.search("kleppmann")] == ["111"])

    print("\n--- checkout rules ---")
    loan = lib.checkout("ann", "D1")
    all_ok &= _check("standard loan is 14 days; copy ON_LOAN",
                     loan.due_at == 14 * DAY and lib.copy("D1").status is CopyStatus.ON_LOAN)
    all_ok &= _check("same copy can't be borrowed twice", _raises(NotAvailable, lambda: lib.checkout("bob", "D1")))
    all_ok &= _check("same member can't hold two copies of one ISBN",
                     _raises(AlreadyBorrowed, lambda: lib.checkout("ann", "D2")))
    lib.add_book(Book("333", "Refactoring", ("Martin Fowler",)))
    lib.add_copy("333", "R0")
    lib.checkout("bob", "R0")
    lib.add_book(Book("444", "Clean Architecture", ("Robert Martin",)))
    lib.add_copy("444", "C1")
    lib.add_book(Book("555", "SICP", ("Abelson", "Sussman")))
    lib.add_copy("555", "S1")
    lib.checkout("bob", "C1")
    lib.checkout("bob", "S1")
    all_ok &= _check("standard members stop at 3 loans", _raises(LimitReached, lambda: lib.checkout("bob", "P1")))

    print("\n--- return, fines ---")
    clock.t = 14 * DAY
    r = lib.return_copy("D1")
    all_ok &= _check("returned exactly at due time -> no fine", r.fine_cents == 0 and r.held_for is None)
    all_ok &= _check("double scan -> NotOnLoan", _raises(NotOnLoan, lambda: lib.return_copy("D1")))
    lib.checkout("cat", "D1")                                    # due at 28 days
    clock.t = 28 * DAY + 1
    all_ok &= _check("one second late -> one day's fine (25)", lib.return_copy("D1").fine_cents == 25)
    lib.checkout("cat", "D1")
    clock.t = 28 * DAY + 1 + 200 * DAY
    all_ok &= _check("fine capped at 2000", lib.return_copy("D1").fine_cents == 2_000)
    all_ok &= _check("member over the fine threshold can't borrow",
                     _raises(UnpaidFines, lambda: lib.checkout("cat", "D1")))
    lib.pay("cat", 2_000)
    all_ok &= _check("after paying they can", lib.checkout("cat", "D1").member_id == "cat")
    graced = GracePeriod(PerDayFine(25, 2_000), days=2)
    all_ok &= _check("grace period decorator: 2 days free, day 3 costs 25",
                     (graced.fine(2), graced.fine(3)) == (0, 25))

    print("\n--- reservations and holds ---")
    clock = FakeClock()
    lib = _library(clock)
    lib.checkout("ann", "P1")
    all_ok &= _check("can't reserve while a copy is on the shelf",
                     _raises(ReservationDenied, lambda: lib.reserve("bob", "111")))
    all_ok &= _check("FIFO positions", lib.reserve("bob", "222") == 1 and lib.reserve("cat", "222") == 2)
    all_ok &= _check("no duplicate reservation", _raises(ReservationDenied, lambda: lib.reserve("bob", "222")))
    all_ok &= _check("can't renew while others wait", _raises(RenewalDenied, lambda: lib.renew(lib.loans_of("ann")[0].id)))
    receipt = lib.return_copy("P1")
    all_ok &= _check("returned copy goes on hold for bob", receipt.held_for == "bob"
                     and lib.copy("P1").status is CopyStatus.ON_HOLD)
    all_ok &= _check("cat can't take bob's hold", _raises(NotAvailable, lambda: lib.checkout("cat", "P1")))
    clock.t = 3 * DAY
    all_ok &= _check("bob's hold expires after 3 days -> passes to cat", lib.copy("P1").hold_for == "cat")
    all_ok &= _check("cat checks it out", lib.checkout("cat", "P1").barcode == "P1")

    print("\n--- renewals and lost copies ---")
    clock = FakeClock()
    lib = _library(clock)
    vip_loan = lib.checkout("vip", "D1")
    all_ok &= _check("premium: 28-day loan, renew extends by 28 days",
                     vip_loan.due_at == 28 * DAY and lib.renew(vip_loan.id) == 56 * DAY)
    std = lib.checkout("ann", "D2")
    lib.renew(std.id)
    all_ok &= _check("standard: only one renewal", _raises(RenewalDenied, lambda: lib.renew(std.id)))
    clock.t = 100 * DAY
    all_ok &= _check("overdue can't renew", _raises(RenewalDenied, lambda: lib.renew(vip_loan.id)))
    all_ok &= _check("lost copy: replacement 3000 + 44 days late x 25; loan closed",
                     lib.mark_lost("D1") == 3_000 + 44 * 25 and lib.copy("D1").status is CopyStatus.LOST
                     and lib.loans_of("vip") == [])
    return all_ok
# ================================================================= END TESTS ==


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
