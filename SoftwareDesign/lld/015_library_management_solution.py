"""
================================================================================
SOLUTION · LLD 015 · Library Management System                     [Tier 2]
================================================================================

THE CORE IDEA
--------------
This problem is asked to test DOMAIN MODELING, not algorithms. The whole score
comes from finding the right nouns and putting each rule in one place:

    Book        a TITLE in the catalogue (ISBN, title, authors). You can't
                borrow a Book.
    BookCopy    a PHYSICAL item with a barcode and a status. You borrow a copy.
    Loan        a RECORD that a member had a copy from borrowed_at to
                returned_at. It is an entity, not a boolean on the copy —
                history, due dates, renewals and fines all live on it.
    Reservation a member waiting for ANY copy of a Book (FIFO per ISBN).
    Hold        a returned copy set aside on the hold shelf for the first
                person in that queue, with a pickup deadline.

The #1 mistake is `Book.available_count += 1`: the system then can't say which
copy is overdue, lost, or on the hold shelf, and a double scan at the return
desk silently creates a book that doesn't exist (demo 1).

Policies that change by member type or by year are STRATEGIES, not if-chains:
    MembershipPolicy  max loans, loan period, max renewals
    FinePolicy        per-day fine with a cap; grace period as a decorator


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. Catalogue: add books and copies; search by title/author substring.
  2. Members with a membership policy (STANDARD, PREMIUM).
  3. checkout(member, barcode) -> Loan. Refused if: copy not available (or on
     hold for someone else), member at loan limit, member owes fines over the
     threshold, member already has a copy of that ISBN.
  4. return_copy(barcode) -> ReturnReceipt(fine, held_for). Overdue fine is
     charged to the member's account. If someone reserved the ISBN, the copy
     goes to the hold shelf for them with a pickup deadline.
  5. renew(loan) -> new due date. Refused if overdue, max renewals reached, or
     someone is waiting for that ISBN.
  6. reserve(member, isbn) only when no copy is available; FIFO; no duplicates.
  7. Expired holds pass to the next person in the queue (lazily).
  8. pay(member, cents).
  Out of scope: payments integration, notifications transport, multiple branches.


================================================================================
ENTITIES, VALUE OBJECTS, INVARIANTS
================================================================================
    Book (value object)        isbn, title, authors
    BookCopy (entity)          barcode, isbn, status, hold_for, hold_until
    CopyStatus                 AVAILABLE | ON_LOAN | ON_HOLD | LOST
    Member (entity)            id, name, policy, balance_cents
    Loan (entity)              id, member, barcode, isbn, borrowed_at, due_at,
                               returned_at, renewals, fine_cents
    MembershipPolicy           max_loans, loan_days, max_renewals
    FinePolicy                 fine(days_late) -> cents
    Library (application service / facade)
       INVARIANT: copy.status == ON_LOAN  <=>  exactly one open Loan for it
       INVARIANT: copy.status == ON_HOLD  <=>  hold_for is set
       INVARIANT: a member never has two open loans for the same ISBN
       INVARIANT: a member appears at most once in an ISBN's reservation queue


================================================================================
CLASS DIAGRAM
================================================================================
    Book 1 ────────── * BookCopy ──── 0..1 ── open Loan * ─────── 1 Member
      │                                          │                   │
      │ 1                                        │ history           ├─ MembershipPolicy
      └── reservation queue (FIFO of Member ids) └── fine_cents      └─ balance_cents
    Library ──uses──▶ FinePolicy (PerDayFine, GracePeriod decorator)


================================================================================
KEY FLOW · return_copy(barcode)
================================================================================
    loan = open_loans[barcode]                      else NotOnLoan (double scan)
    loan.returned_at = now
    days_late = ceil((now - due_at) / DAY) if late
    fine = fine_policy.fine(days_late); member.balance += fine
    queue = reservations[isbn] (skipping members who no longer qualify)
    queue non-empty -> copy ON_HOLD for queue.popleft(), hold_until = now + 3 days
    else            -> copy AVAILABLE


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Loan is an entity with its own id: it outlives the checkout (history,
    disputes, fines) — "discovered record" entities are what interviewers probe.
  * Member.can_borrow logic lives in the Library service because it needs
    loans AND policy AND balance; the Member stays a data-holding entity with
    one behaviour (charge/pay). Say where you drew the line and why.
  * Reservations are per ISBN (any copy), not per copy.
  * Lazy hold expiry on access (checkout / return / reserve / hold lookups),
    like LLD 004's holds.
  * Integer cents for fines; time from an injected clock (seconds).
  * No `Librarian`/`User` class hierarchy: roles are permissions on actions,
    handled by the API layer, not by subclasses of Person.


================================================================================
COMPLEXITY
================================================================================
    checkout / return / renew / reserve   O(1) average (+ lazy queue skips)
    search                                O(B) over books (an inverted index if large)


================================================================================
EDGE CASES
================================================================================
  * Double scan at the return desk -> NotOnLoan, nothing changes.
  * Returned exactly at due time -> not late; one second late -> 1 day fine.
  * Fine capped (e.g. at the replacement cost).
  * Hold expires; next member gets it; if nobody is waiting, AVAILABLE.
  * Member in the queue already borrowed another copy meanwhile -> skipped.
  * Reserve when a copy is on the shelf -> refused ("just borrow it").
  * Mark a copy lost -> closes the loan with the replacement fee.


================================================================================
COMMON MISTAKES
================================================================================
  1. No distinction between Book and BookCopy.
  2. `is_borrowed: bool` on the copy instead of a Loan entity.
  3. Librarian/Member/Admin inheritance tree for permissions.
  4. Fine rules hard-coded in return_copy.
  5. Reservations stored per copy, so a waiting member misses other copies.
  6. Renewing a book that other people are waiting for.
  7. Floats for money; datetime.now() inside business logic.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Multiple branches -> copy has home_branch + current_branch; transfers.
  * Notifications (due soon, hold ready) -> domain events + Observer; a
    scheduler job scans loans due tomorrow (lld/014).
  * E-books with N concurrent licences -> LicencePool instead of copies.
  * Concurrency at many desks -> lock per copy barcode + per member; or DB
    row locks / conditional updates on copy status.
  * Reporting (most borrowed) -> read model built from loan events.


================================================================================
RELATED
================================================================================
  SoftwareDesign/02_oop_and_domain_modeling.md  §7 entities vs value objects,
                                               §8 aggregates, §11 noun/verb analysis
  lld/004_movie_ticket_booking (holds with expiry)
  lld/001_parking_lot (strategy for pricing -> fines here)
"""

from __future__ import annotations

import itertools
import math
import random
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Protocol

Clock = Callable[[], float]
DAY = 86_400.0


# ----------------------------------------------------------------------------
# Errors
# ----------------------------------------------------------------------------
class LibraryError(Exception): ...
class NotFound(LibraryError): ...
class NotAvailable(LibraryError): ...
class LimitReached(LibraryError): ...
class UnpaidFines(LibraryError): ...
class AlreadyBorrowed(LibraryError): ...
class NotOnLoan(LibraryError): ...
class RenewalDenied(LibraryError): ...
class ReservationDenied(LibraryError): ...


# ----------------------------------------------------------------------------
# Policies (strategies)
# ----------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class MembershipPolicy:
    name: str
    max_loans: int
    loan_days: int
    max_renewals: int


STANDARD = MembershipPolicy("standard", max_loans=3, loan_days=14, max_renewals=1)
PREMIUM = MembershipPolicy("premium", max_loans=10, loan_days=28, max_renewals=3)


class FinePolicy(Protocol):
    def fine(self, days_late: int) -> int: ...


class PerDayFine:
    def __init__(self, cents_per_day: int, cap_cents: int) -> None:
        self.per_day, self.cap = cents_per_day, cap_cents

    def fine(self, days_late):
        return min(self.cap, max(0, days_late) * self.per_day)


class GracePeriod:
    """Decorator: the first `days` late days are free."""

    def __init__(self, inner: FinePolicy, days: int) -> None:
        self.inner, self.days = inner, days

    def fine(self, days_late):
        return self.inner.fine(days_late - self.days) if days_late > self.days else 0


# ----------------------------------------------------------------------------
# Domain objects
# ----------------------------------------------------------------------------
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
    balance_cents: int = 0                  # money owed to the library


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

    @property
    def open(self) -> bool:
        return self.returned_at is None


@dataclass(frozen=True, slots=True)
class ReturnReceipt:
    loan: Loan
    fine_cents: int
    held_for: str | None


# ----------------------------------------------------------------------------
# Library — application service
# ----------------------------------------------------------------------------
class Library:
    FINE_BLOCK_CENTS = 1_000
    HOLD_DAYS = 3
    REPLACEMENT_CENTS = 3_000

    def __init__(self, fines: FinePolicy | None = None, clock: Clock = time.time) -> None:
        self._fines = fines or PerDayFine(25, cap_cents=2_000)
        self._clock = clock
        self._books: dict[str, Book] = {}
        self._copies: dict[str, BookCopy] = {}
        self._copies_by_isbn: dict[str, list[str]] = {}
        self._members: dict[str, Member] = {}
        self._loans: dict[int, Loan] = {}
        self._open_by_barcode: dict[str, Loan] = {}
        self._open_by_member: dict[str, dict[str, Loan]] = {}     # member -> isbn -> loan
        self._queues: dict[str, deque[str]] = {}
        self._ids = itertools.count(1)

    # -- catalogue and members -------------------------------------------------------
    def add_book(self, book: Book) -> None:
        self._books.setdefault(book.isbn, book)
        self._copies_by_isbn.setdefault(book.isbn, [])

    def add_copy(self, isbn: str, barcode: str) -> BookCopy:
        self._book(isbn)
        if barcode in self._copies:
            raise LibraryError(f"barcode {barcode} exists")
        copy = self._copies[barcode] = BookCopy(barcode, isbn)
        self._copies_by_isbn[isbn].append(barcode)
        self._release_to_queue(copy)                    # someone may be waiting already
        return copy

    def register(self, member: Member) -> Member:
        if member.id in self._members:
            raise LibraryError(f"member {member.id} exists")
        self._members[member.id] = member
        self._open_by_member[member.id] = {}
        return member

    def search(self, text: str) -> list[Book]:
        t = text.lower()
        return sorted((b for b in self._books.values()
                       if t in b.title.lower() or any(t in a.lower() for a in b.authors)),
                      key=lambda b: b.title)

    # -- circulation -----------------------------------------------------------------
    def checkout(self, member_id: str, barcode: str) -> Loan:
        member, copy = self._member(member_id), self._copy(barcode)
        self._expire_hold(copy)
        if copy.status is CopyStatus.ON_HOLD and copy.hold_for != member_id:
            raise NotAvailable(f"{barcode} is on hold for another member")
        if copy.status not in (CopyStatus.AVAILABLE, CopyStatus.ON_HOLD):
            raise NotAvailable(f"{barcode} is {copy.status.value}")
        self._check_can_borrow(member, copy.isbn)
        now = self._clock()
        loan = Loan(next(self._ids), member_id, barcode, copy.isbn, now, now + member.policy.loan_days * DAY)
        copy.status, copy.hold_for = CopyStatus.ON_LOAN, None
        self._loans[loan.id] = loan
        self._open_by_barcode[barcode] = loan
        self._open_by_member[member_id][copy.isbn] = loan
        return loan

    def return_copy(self, barcode: str) -> ReturnReceipt:
        copy = self._copy(barcode)
        loan = self._open_by_barcode.get(barcode)
        if loan is None:
            raise NotOnLoan(f"{barcode} is not on loan")
        now = self._clock()
        fine = self._close(loan, now)
        copy.status = CopyStatus.AVAILABLE
        self._release_to_queue(copy)
        return ReturnReceipt(loan, fine, copy.hold_for)

    def renew(self, loan_id: int) -> float:
        loan = self._loans.get(loan_id)
        if loan is None or not loan.open:
            raise NotFound(f"no open loan {loan_id}")
        member = self._members[loan.member_id]
        if self._clock() > loan.due_at:
            raise RenewalDenied("overdue loans can't be renewed")
        if loan.renewals >= member.policy.max_renewals:
            raise RenewalDenied("renewal limit reached")
        if self._queue(loan.isbn):
            raise RenewalDenied("other members are waiting for this book")
        loan.renewals += 1
        loan.due_at += member.policy.loan_days * DAY
        return loan.due_at

    def reserve(self, member_id: str, isbn: str) -> int:
        """Join the waiting list; returns the 1-based position."""
        member = self._member(member_id)
        self._book(isbn)
        for bc in self._copies_by_isbn[isbn]:
            self._expire_hold(self._copies[bc])
        if any(self._copies[bc].status is CopyStatus.AVAILABLE for bc in self._copies_by_isbn[isbn]):
            raise ReservationDenied("a copy is on the shelf; borrow it")
        if isbn in self._open_by_member[member.id]:
            raise ReservationDenied("you already have this book")
        if any(self._copies[bc].hold_for == member_id for bc in self._copies_by_isbn[isbn]):
            raise ReservationDenied("a copy is already on hold for you")
        queue = self._queues.setdefault(isbn, deque())
        if member_id in queue:
            raise ReservationDenied("already reserved")
        queue.append(member_id)
        return len(queue)

    def mark_lost(self, barcode: str) -> int:
        copy = self._copy(barcode)
        loan = self._open_by_barcode.get(barcode)
        if loan is None:
            raise NotOnLoan(barcode)
        self._close(loan, self._clock(), extra=self.REPLACEMENT_CENTS)
        copy.status = CopyStatus.LOST
        return loan.fine_cents

    def pay(self, member_id: str, cents: int) -> int:
        member = self._member(member_id)
        if cents <= 0:
            raise LibraryError("payment must be positive")
        member.balance_cents = max(0, member.balance_cents - cents)
        return member.balance_cents

    # -- queries ---------------------------------------------------------------------
    def copy(self, barcode: str) -> BookCopy:
        copy = self._copy(barcode)
        self._expire_hold(copy)
        return copy

    def available(self, isbn: str) -> list[str]:
        out = []
        for bc in self._copies_by_isbn.get(isbn, []):
            self._expire_hold(self._copies[bc])
            if self._copies[bc].status is CopyStatus.AVAILABLE:
                out.append(bc)
        return out

    def loans_of(self, member_id: str) -> list[Loan]:
        return list(self._open_by_member[self._member(member_id).id].values())

    def member(self, member_id: str) -> Member:
        return self._member(member_id)

    # -- internals -------------------------------------------------------------------
    def _check_can_borrow(self, member: Member, isbn: str) -> None:
        open_loans = self._open_by_member[member.id]
        if member.balance_cents > self.FINE_BLOCK_CENTS:
            raise UnpaidFines(f"owes {member.balance_cents} cents")
        if len(open_loans) >= member.policy.max_loans:
            raise LimitReached(f"{member.policy.max_loans} loans max")
        if isbn in open_loans:
            raise AlreadyBorrowed(f"already has a copy of {isbn}")

    def _close(self, loan: Loan, now: float, extra: int = 0) -> int:
        days_late = math.ceil((now - loan.due_at) / DAY) if now > loan.due_at else 0
        loan.fine_cents = self._fines.fine(days_late) + extra
        loan.returned_at = now
        self._members[loan.member_id].balance_cents += loan.fine_cents
        del self._open_by_barcode[loan.barcode]
        del self._open_by_member[loan.member_id][loan.isbn]
        return loan.fine_cents

    def _queue(self, isbn: str) -> deque[str]:
        return self._queues.get(isbn, deque())

    def _release_to_queue(self, copy: BookCopy) -> None:
        """An AVAILABLE copy goes to the first queued member who still qualifies."""
        queue = self._queues.get(copy.isbn)
        while queue:
            candidate = queue.popleft()
            if copy.isbn in self._open_by_member[candidate]:
                continue                                   # got another copy meanwhile
            copy.status = CopyStatus.ON_HOLD
            copy.hold_for = candidate
            copy.hold_until = self._clock() + self.HOLD_DAYS * DAY
            return
        copy.status, copy.hold_for = CopyStatus.AVAILABLE, None

    def _expire_hold(self, copy: BookCopy) -> None:
        if copy.status is CopyStatus.ON_HOLD and self._clock() >= copy.hold_until:
            copy.status, copy.hold_for = CopyStatus.AVAILABLE, None
            self._release_to_queue(copy)

    def _book(self, isbn: str) -> Book:
        if isbn not in self._books:
            raise NotFound(f"no book {isbn}")
        return self._books[isbn]

    def _copy(self, barcode: str) -> BookCopy:
        if barcode not in self._copies:
            raise NotFound(f"no copy {barcode}")
        return self._copies[barcode]

    def _member(self, member_id: str) -> Member:
        if member_id not in self._members:
            raise NotFound(f"no member {member_id}")
        return self._members[member_id]


# ===================================================================== TESTS ==
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


class CounterLibrary:
    """The naive model: a Book with available_count, no copies, no loans."""

    def __init__(self, total: int) -> None:
        self.total = total
        self.available_count = total

    def checkout(self) -> bool:
        if self.available_count == 0:
            return False
        self.available_count -= 1
        return True

    def return_copy(self) -> None:
        self.available_count += 1          # can't tell a real return from a double scan


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: 20,000 random desk operations, including double scans at the return desk ---")
    rng = random.Random(15)
    clock = FakeClock()
    lib = Library(PerDayFine(25, 2_000), clock)
    naive = CounterLibrary(5)
    lib.add_book(Book("X", "Popular Book", ("A",)))
    barcodes = [f"X{i}" for i in range(5)]
    for bc in barcodes:
        lib.add_copy("X", bc)
    members = [f"m{i}" for i in range(12)]
    for m in members:
        lib.register(Member(m, m, PREMIUM))
    naive_violations = model_violations = 0
    outcomes: dict[str, int] = {}
    for _ in range(20_000):
        clock.t += rng.uniform(0, 2 * DAY)
        op = rng.random()
        try:
            if op < 0.35:
                lib.checkout(rng.choice(members), rng.choice(barcodes))
                naive.checkout()
            elif op < 0.7:
                lib.return_copy(rng.choice(barcodes))       # includes double scans
                naive.return_copy()
            elif op < 0.85:
                lib.reserve(rng.choice(members), "X")
            else:
                m = rng.choice(members)
                if lib.member(m).balance_cents:
                    lib.pay(m, lib.member(m).balance_cents)
            outcomes["ok"] = outcomes.get("ok", 0) + 1
        except LibraryError as e:
            if isinstance(e, NotOnLoan):
                naive.return_copy()                         # the counter model accepts the double scan
            outcomes[type(e).__name__] = outcomes.get(type(e).__name__, 0) + 1
        naive_violations += not 0 <= naive.available_count <= naive.total
        on_loan = sum(1 for bc in barcodes if lib.copy(bc).status is CopyStatus.ON_LOAN)
        holds = [lib.copy(bc).hold_for for bc in barcodes if lib.copy(bc).status is CopyStatus.ON_HOLD]
        model_violations += (on_loan != len(lib._open_by_barcode)
                             or len(holds) != len(set(holds))
                             or any(len(lib.loans_of(m)) > 1 for m in members))
    print(f"      outcomes: {outcomes}")
    print(f"      counter model: available_count outside [0, 5] after {naive_violations} operations")
    print(f"      copies + loans model: invariant violations: {model_violations}")
    all_ok &= _check("entity model keeps every invariant; the counter model breaks",
                     model_violations == 0 and naive_violations > 0)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
