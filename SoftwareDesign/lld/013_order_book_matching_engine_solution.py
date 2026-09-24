"""
================================================================================
SOLUTION · LLD 013 · Stock Exchange Order Book / Matching Engine   [Tier 2]
================================================================================

THE CORE IDEA
--------------
An order book is two sorted sides of resting LIMIT orders:

    BIDS (buy)   best = HIGHEST price        ASKS (sell)  best = LOWEST price

An incoming order MATCHES against the opposite side while prices cross, in
PRICE-TIME PRIORITY: better price first, and at the same price, whoever arrived
first. Each trade executes at the RESTING (maker) order's price — an aggressive
buyer willing to pay 105 who meets an ask at 101 pays 101.

The data structure is the interview:

    price -> PriceLevel (FIFO deque of orders + total quantity)
    a heap of prices per side (max-heap for bids via negation)
    order id -> Order for O(1) cancel

Cancel is LAZY: mark the order cancelled and subtract its quantity from the
level total; the matcher skips it when it reaches the front of the deque, and
empty price levels are popped from the heap only when they surface as "best".
Removing from the middle of a deque/list would be O(n) (demo 2).

Time-in-force is a small strategy-like switch on what happens to the unfilled
remainder: GTC rests on the book, IOC is cancelled, FOK executes only if the
WHOLE quantity can fill immediately (checked before touching the book).


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. One instrument. Prices are integer ticks, quantities integers.
  2. submit(order) -> [Trade]; order types LIMIT and MARKET.
  3. Time in force: GTC (rest remainder), IOC (cancel remainder),
     FOK (all or nothing). MARKET orders never rest.
  4. cancel(order_id) -> bool.
  5. best_bid(), best_ask(), depth(n) -> aggregated levels.
  6. Order status: NEW, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED.
  7. Observers receive every trade (market data feed).
  Out of scope: multiple instruments (one book each), self-trade prevention,
  auctions, persistence, networking.


================================================================================
ENTITIES AND INVARIANTS
================================================================================
    Side, OrderType, TimeInForce, Status   enums
    Order         entity: id, trader, side, type, tif, price, qty, remaining, seq, status
    Trade         value object: buy id, sell id, price, qty, aggressor side
    BookSide      price -> deque[Order], price -> open qty, price heap
    MatchingEngine
       INVARIANT: after every submit/cancel the book is NOT CROSSED
                  (best_bid < best_ask, or a side is empty)
       INVARIANT: every trade's qty is subtracted from exactly one buy and one sell
       INVARIANT: level_qty[p] == sum(remaining of live orders at p)


================================================================================
MATCHING TRACE
================================================================================
    book:  ASKS 101: [s1 qty 5 (seq 1), s2 qty 5 (seq 2)]   102: [s3 qty 10]
    submit BUY LIMIT 102 qty 12 GTC (b1)
      best ask 101 <= 102 -> s1 fills 5 @101   (s1 FILLED)
                             s2 fills 5 @101   (s2 FILLED; level 101 empty)
      best ask 102 <= 102 -> s3 fills 2 @102   (s3 PARTIALLY_FILLED, 8 left)
      b1 FILLED -> trades [(b1,s1,101,5), (b1,s2,101,5), (b1,s3,102,2)]
    submit BUY LIMIT 100 qty 3 -> no cross, rests: BIDS 100: [b2]
    book now: best bid 100 < best ask 102  (not crossed)


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * dict + heap + deques: O(log L) new price level, O(1) append at an existing
    level, O(1) cancel. Real engines use arrays indexed by tick (bounded price
    range) or red-black trees; a sorted container is fine to name.
  * Integer ticks: floats would make 100.1 + 0.2 a different price level.
  * Trades at the maker's price; the aggressor gets any price improvement.
  * FOK pre-check walks the opposite side's levels (O(L log L) here) and does
    not mutate anything if it can't fill fully.
  * The engine is single-threaded by design: exchanges serialise order entry
    through one sequencer thread per instrument (deterministic replay, no
    locks in the hot path). Concurrency lives in the gateway queue in front.
  * Observers get trades AFTER the book is consistent.


================================================================================
COMPLEXITY
================================================================================
    submit (no match, existing level)   O(1)
    submit (new level)                  O(log L)
    each fill                           O(1) amortised (+ lazy skips)
    cancel                              O(1)
    best_bid / best_ask                 O(1) amortised (lazy heap cleanup)
    depth(n)                            O(L log L)
    L = number of price levels


================================================================================
EDGE CASES
================================================================================
  * Aggressor price better than several levels -> sweeps them best first.
  * Same price, earlier seq fills first (time priority).
  * Cancel an order already filled / unknown / already cancelled -> False.
  * Partially filled order cancelled -> remaining removed, trades stand.
  * MARKET into an empty side -> no trades, CANCELLED.
  * FOK with insufficient liquidity -> CANCELLED, book untouched.
  * qty <= 0, LIMIT without a positive price, MARKET with GTC -> REJECTED.


================================================================================
COMMON MISTAKES
================================================================================
  1. Sorting the whole book on every order.
  2. Trading at the aggressor's price instead of the maker's.
  3. Removing cancelled orders from the middle of a list (O(n)).
  4. Forgetting time priority within a price level.
  5. FOK implemented as "fill what you can, then roll back".
  6. Float prices.
  7. Letting a MARKET order rest on the book.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Self-trade prevention -> policy strategy: cancel resting / cancel incoming / both.
  * Stop orders -> separate trigger book keyed by stop price; on each trade,
    release triggered stops as new orders.
  * Iceberg orders -> visible slice re-queued at the back after each refill.
  * Order modify -> price change = cancel + new (loses priority); qty decrease
    keeps priority.
  * Many instruments -> one engine per symbol, sharded by symbol, each single-threaded.
  * Crash recovery -> the input order log is the source of truth; replay it
    deterministically (event sourcing).
  * Market data -> L1 (top of book), L2 (depth), L3 (every order) feeds as observers.


================================================================================
RELATED
================================================================================
  PyDSA heaps (two heaps / lazy deletion)
  SoftwareDesign/04_design_patterns_in_practice.md  §7 Observer, §8 Command (order log)
  lld/009_lru_lfu_cache (O(1) structure design)
"""

from __future__ import annotations

import heapq
import itertools
import random
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Callable


# ----------------------------------------------------------------------------
# Enums and value objects
# ----------------------------------------------------------------------------
class Side(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    LIMIT = "limit"
    MARKET = "market"


class TimeInForce(Enum):
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


class Status(Enum):
    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass(slots=True, eq=False)
class Order:
    id: str
    trader: str
    side: Side
    qty: int
    price: int | None = None
    type: OrderType = OrderType.LIMIT
    tif: TimeInForce = TimeInForce.GTC
    remaining: int = 0
    seq: int = 0
    status: Status = Status.NEW


@dataclass(frozen=True, slots=True)
class Trade:
    buy_id: str
    sell_id: str
    price: int
    qty: int
    aggressor: Side


# ----------------------------------------------------------------------------
# One side of the book
# ----------------------------------------------------------------------------
class BookSide:
    def __init__(self, side: Side) -> None:
        self.side = side
        self.levels: dict[int, deque[Order]] = {}
        self.level_qty: dict[int, int] = {}
        self._heap: list[int] = []                   # bids store -price

    def _key(self, price: int) -> int:
        return -price if self.side is Side.BUY else price

    def add(self, order: Order) -> None:
        p = order.price
        if p not in self.levels:
            self.levels[p] = deque()
            self.level_qty[p] = 0
            heapq.heappush(self._heap, self._key(p))
        self.levels[p].append(order)
        self.level_qty[p] += order.remaining

    def best(self) -> int | None:
        while self._heap:
            p = abs(self._heap[0])
            if self.level_qty.get(p, 0) > 0:
                return p
            heapq.heappop(self._heap)                 # lazy removal of an empty level
            self.levels.pop(p, None)
            self.level_qty.pop(p, None)
        return None

    def cancel(self, order: Order) -> None:
        self.level_qty[order.price] -= order.remaining

    def sorted_levels(self) -> list[tuple[int, int]]:
        live = [(p, q) for p, q in self.level_qty.items() if q > 0]
        return sorted(live, key=lambda pq: self._key(pq[0]))


# ----------------------------------------------------------------------------
# Matching engine
# ----------------------------------------------------------------------------
class MatchingEngine:
    def __init__(self) -> None:
        self._bids = BookSide(Side.BUY)
        self._asks = BookSide(Side.SELL)
        self._orders: dict[str, Order] = {}
        self._seq = itertools.count(1)
        self._listeners: list[Callable[[Trade], None]] = []

    def subscribe(self, listener: Callable[[Trade], None]) -> None:
        self._listeners.append(listener)

    # -- commands ------------------------------------------------------------------
    def submit(self, order: Order) -> list[Trade]:
        order.remaining = order.qty
        order.seq = next(self._seq)
        if not self._valid(order):
            order.status = Status.REJECTED
            return []
        self._orders[order.id] = order
        if order.tif is TimeInForce.FOK and self._fillable(order) < order.qty:
            order.status = Status.CANCELLED
            return []
        trades = self._match(order)
        if order.remaining == 0:
            order.status = Status.FILLED
        elif order.type is OrderType.LIMIT and order.tif is TimeInForce.GTC:
            self._side(order.side).add(order)
            order.status = Status.PARTIALLY_FILLED if trades else Status.NEW
        else:
            order.status = Status.CANCELLED
        for trade in trades:
            for listener in self._listeners:
                listener(trade)
        return trades

    def cancel(self, order_id: str) -> bool:
        order = self._orders.get(order_id)
        if order is None or order.status not in (Status.NEW, Status.PARTIALLY_FILLED):
            return False
        self._side(order.side).cancel(order)
        order.remaining = 0
        order.status = Status.CANCELLED
        return True

    # -- queries -------------------------------------------------------------------
    def best_bid(self) -> int | None:
        return self._bids.best()

    def best_ask(self) -> int | None:
        return self._asks.best()

    def depth(self, n: int = 5) -> dict[str, list[tuple[int, int]]]:
        return {"bids": self._bids.sorted_levels()[:n], "asks": self._asks.sorted_levels()[:n]}

    def order(self, order_id: str) -> Order:
        return self._orders[order_id]

    # -- internals -----------------------------------------------------------------
    def _side(self, side: Side) -> BookSide:
        return self._bids if side is Side.BUY else self._asks

    @staticmethod
    def _valid(order: Order) -> bool:
        if order.qty <= 0 or order.id is None:
            return False
        if order.type is OrderType.LIMIT:
            return order.price is not None and order.price > 0
        return order.price is None and order.tif is not TimeInForce.GTC

    @staticmethod
    def _crosses(order: Order, resting_price: int) -> bool:
        if order.type is OrderType.MARKET:
            return True
        return resting_price <= order.price if order.side is Side.BUY else resting_price >= order.price

    def _fillable(self, order: Order) -> int:
        opposite = self._asks if order.side is Side.BUY else self._bids
        total = 0
        for price, qty in opposite.sorted_levels():
            if not self._crosses(order, price) or total >= order.qty:
                break
            total += qty
        return total

    def _match(self, order: Order) -> list[Trade]:
        opposite = self._asks if order.side is Side.BUY else self._bids
        trades: list[Trade] = []
        while order.remaining:
            price = opposite.best()
            if price is None or not self._crosses(order, price):
                break
            queue = opposite.levels[price]
            while queue and order.remaining:
                maker = queue[0]
                if maker.remaining == 0:                 # lazily cancelled
                    queue.popleft()
                    continue
                fill = min(order.remaining, maker.remaining)
                order.remaining -= fill
                maker.remaining -= fill
                opposite.level_qty[price] -= fill
                if maker.remaining == 0:
                    maker.status = Status.FILLED
                    queue.popleft()
                else:
                    maker.status = Status.PARTIALLY_FILLED
                buy, sell = (order, maker) if order.side is Side.BUY else (maker, order)
                trades.append(Trade(buy.id, sell.id, price, fill, order.side))
        return trades


# ===================================================================== TESTS ==
def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _buy(oid, qty, price=None, **kw) -> Order:
    return Order(oid, "t", Side.BUY, qty, price, OrderType.LIMIT if price else OrderType.MARKET, **kw)


def _sell(oid, qty, price=None, **kw) -> Order:
    return Order(oid, "t", Side.SELL, qty, price, OrderType.LIMIT if price else OrderType.MARKET, **kw)


def _t(trades) -> list[tuple]:
    return [(t.buy_id, t.sell_id, t.price, t.qty) for t in trades]


def run_tests() -> bool:
    all_ok = True
    print("--- the matching trace ---")
    e = MatchingEngine()
    e.submit(_sell("s1", 5, 101))
    e.submit(_sell("s2", 5, 101))
    e.submit(_sell("s3", 10, 102))
    trades = e.submit(_buy("b1", 12, 102))
    all_ok &= _check("sweeps 101 in time order, then 102, at maker prices",
                     _t(trades) == [("b1", "s1", 101, 5), ("b1", "s2", 101, 5), ("b1", "s3", 102, 2)])
    all_ok &= _check("statuses: b1 FILLED, s2 FILLED, s3 PARTIALLY_FILLED with 8 left",
                     e.order("b1").status is Status.FILLED and e.order("s2").status is Status.FILLED
                     and e.order("s3").status is Status.PARTIALLY_FILLED and e.order("s3").remaining == 8)
    e.submit(_buy("b2", 3, 100))
    all_ok &= _check("non-crossing order rests; book not crossed",
                     (e.best_bid(), e.best_ask()) == (100, 102) and e.order("b2").status is Status.NEW)
    all_ok &= _check("depth aggregates levels, best first",
                     e.depth() == {"bids": [(100, 3)], "asks": [(102, 8)]})

    print("\n--- price priority beats time priority ---")
    e = MatchingEngine()
    e.submit(_buy("early_low", 5, 99))
    e.submit(_buy("late_high", 5, 100))
    all_ok &= _check("incoming sell hits the higher bid first even though it arrived later",
                     _t(e.submit(_sell("s", 5, 98))) == [("late_high", "s", 100, 5)])

    print("\n--- cancel ---")
    e = MatchingEngine()
    e.submit(_sell("a", 5, 101))
    e.submit(_sell("b", 5, 101))
    all_ok &= _check("cancel resting order -> True; twice -> False; unknown -> False",
                     e.cancel("a") and not e.cancel("a") and not e.cancel("zzz"))
    all_ok &= _check("cancelled order is skipped; b fills", _t(e.submit(_buy("x", 5, 101))) == [("x", "b", 101, 5)])
    all_ok &= _check("filled order can't be cancelled; empty level disappears",
                     not e.cancel("b") and e.best_ask() is None)
    e.submit(_sell("c", 10, 105))
    e.submit(_buy("y", 4, 105))
    e.cancel("c")
    all_ok &= _check("cancel after partial fill keeps the trade, removes the rest",
                     e.order("c").status is Status.CANCELLED and e.best_ask() is None)

    print("\n--- time in force and market orders ---")
    e = MatchingEngine()
    e.submit(_sell("s1", 5, 101))
    e.submit(_sell("s2", 5, 103))
    ioc = _buy("ioc", 8, 102, tif=TimeInForce.IOC)
    all_ok &= _check("IOC fills what crosses (5 @101) and cancels the rest",
                     _t(e.submit(ioc)) == [("ioc", "s1", 101, 5)] and ioc.status is Status.CANCELLED
                     and e.best_bid() is None)
    fok = _buy("fok", 6, 103, tif=TimeInForce.FOK)
    all_ok &= _check("FOK for 6 with only 5 available -> nothing trades, book untouched",
                     e.submit(fok) == [] and fok.status is Status.CANCELLED and e.depth()["asks"] == [(103, 5)])
    fok2 = _buy("fok2", 5, 103, tif=TimeInForce.FOK)
    all_ok &= _check("FOK for exactly the available 5 -> fills", len(e.submit(fok2)) == 1 and fok2.status is Status.FILLED)
    e.submit(_buy("b1", 2, 90))
    e.submit(_buy("b2", 2, 80))
    mkt = _sell("m", 10, tif=TimeInForce.IOC)
    all_ok &= _check("MARKET sell sweeps every bid level, remainder cancelled",
                     _t(e.submit(mkt)) == [("b1", "m", 90, 2), ("b2", "m", 80, 2)] and mkt.status is Status.CANCELLED)

    print("\n--- validation and observers ---")
    e = MatchingEngine()
    seen = []
    e.subscribe(seen.append)
    bad = [_buy("q0", 0, 100), _buy("p0", 5, 0), Order("mg", "t", Side.BUY, 5, None, OrderType.MARKET, TimeInForce.GTC)]
    all_ok &= _check("zero qty, zero price, GTC market -> REJECTED",
                     all(e.submit(o) == [] and o.status is Status.REJECTED for o in bad))
    e.submit(_sell("s", 1, 50))
    e.submit(_buy("b", 1, 60))
    all_ok &= _check("trade feed observer notified with the maker price", [(t.price, t.aggressor) for t in seen] == [(50, Side.BUY)])
    return all_ok
# ================================================================= END TESTS ==


class NaiveEngine:
    """Reference: keep all resting orders in a list; sort candidates for every order."""

    def __init__(self) -> None:
        self.resting: list[Order] = []
        self.seq = itertools.count(1)

    def submit(self, o: Order) -> list[tuple]:
        o.remaining, o.seq = o.qty, next(self.seq)
        opp = [r for r in self.resting if r.side is not o.side and r.remaining > 0]
        if o.side is Side.BUY:
            opp = [r for r in opp if r.price <= o.price]
            opp.sort(key=lambda r: (r.price, r.seq))
        else:
            opp = [r for r in opp if r.price >= o.price]
            opp.sort(key=lambda r: (-r.price, r.seq))
        out = []
        for r in opp:
            if not o.remaining:
                break
            f = min(o.remaining, r.remaining)
            o.remaining -= f
            r.remaining -= f
            buy, sell = (o, r) if o.side is Side.BUY else (r, o)
            out.append((buy.id, sell.id, r.price, f))
        self.resting = [r for r in self.resting if r.remaining > 0]
        if o.remaining:
            self.resting.append(o)
        return out

    def cancel(self, oid: str) -> bool:
        for r in self.resting:
            if r.id == oid and r.remaining > 0:
                r.remaining = 0
                self.resting.remove(r)
                return True
        return False


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: 6,000 random orders + cancels vs a naive sort-everything engine ---")
    rng = random.Random(13)
    fast, slow = MatchingEngine(), NaiveEngine()
    mismatches = crossed = 0
    ids: list[str] = []
    for i in range(6000):
        if ids and rng.random() < 0.2:
            oid = rng.choice(ids)
            mismatches += fast.cancel(oid) != slow.cancel(oid)
            continue
        side = rng.choice([Side.BUY, Side.SELL])
        price, qty = rng.randint(95, 105), rng.randint(1, 20)
        oid = f"o{i}"
        ids.append(oid)
        a = _t(fast.submit(Order(oid, "t", side, qty, price)))
        b = slow.submit(Order(oid, "t", side, qty, price))
        mismatches += a != b
        bb, ba = fast.best_bid(), fast.best_ask()
        crossed += bb is not None and ba is not None and bb >= ba
    all_ok &= _check(f"identical trades ({mismatches} mismatches); book never crossed ({crossed} times)",
                     mismatches == 0 and crossed == 0)

    print("\n--- DEMO 2: 10,000 resting orders, then 2,000 cancels + 2,000 aggressive orders ---")
    rng = random.Random(14)
    results = {}
    for name, make in (("heap + lazy cancel", MatchingEngine), ("naive list", NaiveEngine)):
        eng = make()
        for i in range(10_000):
            eng.submit(Order(f"r{i}", "t", Side.SELL, 5, rng.randint(1000, 2000)))
        cancel_ids = [f"r{i}" for i in rng.sample(range(10_000), 2_000)]
        start = time.perf_counter()
        for oid in cancel_ids[:2000]:
            eng.cancel(oid)
        for i in range(2000):
            eng.submit(Order(f"b{i}", "t", Side.BUY, 3, rng.randint(900, 1100)))
        results[name] = time.perf_counter() - start
        print(f"      {name:<20}: 2,000 cancels + 2,000 orders in {results[name] * 1000:8.1f} ms")
    ratio = results["naive list"] / results["heap + lazy cancel"]
    all_ok &= _check(f"structured book is {ratio:.0f}x faster", ratio > 20)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
