# Software Design Foundations

> "Simplicity is the ultimate sophistication... perfection is achieved not when there is
> nothing more to add, but when there is nothing left to take away." — Antoine de
> Saint-Exupéry (paraphrased; often quoted alongside Leonardo da Vinci)

This file is the on-ramp. It assumes you can write a function and a loop in **Python or
Go**, and nothing else — not what "coupling" means, not what an interface is for, not why
anyone would wrap a dictionary in a class. Chapters `01`–`14` assume you already have that
vocabulary; this chapter builds it, with the smallest examples that make each idea
concrete.

**If you already know what encapsulation, coupling, and an interface are for** — if the
words "deep module" or "invariant" don't need a definition — skip straight to
`01_philosophy_of_software_design.md`. You won't miss anything; this chapter is not
repeated anywhere else in the track.

Every example below is run for real. What's printed under **Output:** is the actual
output of the actual code, not a guess.

---

## Contents

1. [Why design at all](#1--why-design-at-all)
2. [Programs, functions, and modules](#2--programs-functions-and-modules)
3. [What a class actually is](#3--what-a-class-actually-is)
4. [Abstraction and encapsulation](#4--abstraction-and-encapsulation)
5. [Coupling and cohesion, in plain terms](#5--coupling-and-cohesion-in-plain-terms)
6. [Interfaces: the shape of a thing](#6--interfaces-the-shape-of-a-thing)
7. [Requirements: functional vs. non-functional](#7--requirements-functional-vs-non-functional)
8. [A complete worked example, start to finish](#8--a-complete-worked-example-start-to-finish)
9. [Glossary](#9--glossary)
10. [How to read the rest of this track](#10--how-to-read-the-rest-of-this-track)
11. [Checklist before you move on](#11--checklist-before-you-move-on)

---

## 1 · Why design at all

Say you're asked to track a shopping cart's total. The obvious first version:

```python
total = 0
total += 12       # a coffee mug
total += 8        # a notebook
print(total)       # 20
```

That's fine — for exactly this. Then the requirements grow the way real requirements
always do: some items are taxed, some aren't; there's a discount code; the store adds a
second cart for gift orders; someone asks for the total in cents, not dollars, because
floats were losing a penny here and there. Six months in, the "total" logic is
copy-pasted in four places, one of them forgot the discount code, and nobody is sure
which copy is the real one.

Nothing about this was a single bad decision. Each step was reasonable on its own. What
went wrong is that there was never a place that was **the one place** the total gets
computed — so every new requirement was bolted on wherever it was easiest to reach.

> **Software design is the set of decisions about how to organize code** — which pieces
> exist, what each piece is allowed to know, and how they talk to each other — **so that
> the program stays easy to understand and change as it grows.**

That's the entire subject. Everything from here to chapter `14` — classes, modules,
patterns, architecture — is a technique for keeping that promise as a program gets
bigger than one person can hold in their head at once.

Two things are worth noticing before you write a line of design-oriented code:

- **You can't tell good design from bad by staring at one version of the code.** You can
  only tell by asking "what happens when a new requirement shows up?" Design is judged by
  what it costs to *change* things, not by what it costs to write them the first time.
- **Nobody designs a large system correctly the first time.** The goal is not to predict
  every future requirement. It's to keep the *cost of being wrong* low, so that when a
  requirement you didn't expect arrives, fixing it touches one place, not four.

---

## 2 · Programs, functions, and modules

Three words this whole track uses constantly, defined precisely once:

| Term | Definition | Why it exists |
|---|---|---|
| **Program** | A sequence of instructions a computer runs. | The thing you're building. |
| **Function** (or method) | A named, reusable group of instructions that takes input and produces output. | So you write the logic once and call it by name instead of repeating it. |
| **Module** | A named, reusable group of *related* functions and data — a file, a class, a package. | So you can find related code together and reason about it as one unit, without reading the whole program. |

A function stops you repeating **instructions**. A module stops you repeating —
and scattering — **knowledge** (the shopping-cart story in §1 is knowledge — "how a total
is computed" — spread across four places instead of owned by one module).

```python
def total_price(prices: list[int]) -> int:
    return sum(prices)

print(total_price([1200, 800]))   # cents: a coffee mug + a notebook
```

Output:

```
2000
```

```go
package main

import "fmt"

func totalPrice(prices []int) int {
	total := 0
	for _, p := range prices {
		total += p
	}
	return total
}

func main() {
	fmt.Println(totalPrice([]int{1200, 800}))
}
```

Output:

```
2000
```

A function is the smallest unit of reuse. Almost every design idea in this track is
about the next size up: how to group functions and the data they operate on into
modules that are easy to use correctly and hard to use incorrectly.

---

## 3 · What a class actually is

A **class** is a way of bundling data with **the only code allowed to change that data
in ways that matter.** That's the whole idea — not inheritance, not polymorphism, not
any of the words from a textbook chapter titled "OOP." Those are tools a class can use;
they are not what a class *is for*.

Here's a bank balance with no class at all — just a dictionary anyone can touch:

```python
account = {"balance": 100}

def withdraw(account, amount):
    account["balance"] -= amount           # nothing stops this from going negative

withdraw(account, 500)
print(account["balance"])
```

Output:

```
-400
```

The bank now believes it owes money it never had. Nothing in the code is *wrong*,
exactly — `account["balance"] -= amount` is a perfectly correct line of Python. The
problem is that the **rule** ("a balance can never go negative") lives nowhere. It's not
written down anywhere in the code, so nothing enforces it, and every one of the (let's
say) thirty places in a real program that touch `account["balance"]` would have to
remember to check it themselves.

Now the same balance as a class:

```python
class Account:
    def __init__(self, balance: int):
        self._balance = balance

    def withdraw(self, amount: int) -> None:
        if amount > self._balance:
            raise ValueError(f"cannot withdraw {amount}: balance is {self._balance}")
        self._balance -= amount

    @property
    def balance(self) -> int:
        return self._balance


account = Account(100)
try:
    account.withdraw(500)
except ValueError as e:
    print(e)
print(account.balance)
```

Output:

```
cannot withdraw 500: balance is 100
100
```

Nothing outside `Account` can touch `_balance` directly (by convention in Python — the
leading underscore says "don't"; Go enforces it with the compiler, below). `withdraw` is
now the **one door** the balance changes through, and the rule lives inside that door,
written exactly once.

```
    A DICTIONARY                              A CLASS

 ┌────────────────────┐              ┌─────────────────────────────────┐
 │ balance: 100        │  any code,  │ withdraw(amount)                │ ◀─ the only door
 │                     │  anywhere,  ├─────────────────────────────────┤
 │                     │  can write  │ _balance                        │ ◀─ rule: never
 └────────────────────┘  any value   │                                 │    below zero,
                                     └─────────────────────────────────┘    enforced here
   the rule must be checked            the rule is checked once,
   everywhere the field is touched     in the one function that touches it
```

Go doesn't have Python's classes, but the same idea — data plus the one set of functions
allowed to change it — works with a struct whose field is **unexported** (lowercase, so
only code in the same package can even see it) and methods on that struct:

```go
package main

import "fmt"

type Account struct {
	balance int // unexported: code outside this package cannot read or write it directly
}

func NewAccount(balance int) *Account { return &Account{balance: balance} }

func (a *Account) Withdraw(amount int) error {
	if amount > a.balance {
		return fmt.Errorf("cannot withdraw %d: balance is %d", amount, a.balance)
	}
	a.balance -= amount
	return nil
}

func (a *Account) Balance() int { return a.balance }

func main() {
	account := NewAccount(100)
	if err := account.Withdraw(500); err != nil {
		fmt.Println(err)
	}
	fmt.Println(account.Balance())
}
```

Output:

```
cannot withdraw 500: balance is 100
100
```

Ask this question of every class you write, from your first one to your thousandth:
**what rule does this protect, and is there exactly one door it's enforced through?**
If a class has no rule to protect — it's just fields, with no logic that would ever
reject an input — it isn't really a class yet. It's a plain record, and Python
(`@dataclass`) and Go (a plain struct) both have a lighter-weight way to say exactly
that, with nothing pretending to be more. `02_oop_and_domain_modeling.md` §1 and §3
build on this.

---

## 4 · Abstraction and encapsulation

These two words get used interchangeably by beginners and precisely by everyone else.
They're related but different:

- **Encapsulation** is the *mechanism*: hiding a piece of data so that code outside a
  module can't reach in and touch it directly. In `Account` above, that's `_balance`
  being unexported.
- **Abstraction** is the *result*: callers of `Account` only ever think in terms of
  "withdraw an amount," never in terms of "how the balance is actually stored." The
  *how* is free to change without anyone who calls `withdraw` noticing or caring.

Here's abstraction made concrete. Two versions of `Account` store the balance
completely differently — one keeps a running total, the other keeps every transaction
and adds them up on demand — but expose the exact same operations:

```python
# Version 1: stores the running balance directly.
class AccountV1:
    def __init__(self, opening: int):
        self._balance = opening

    def deposit(self, amount: int) -> None:
        self._balance += amount

    @property
    def balance(self) -> int:
        return self._balance


# Version 2: stores every transaction instead, and computes the balance on demand.
# Nothing outside this class knows the representation changed.
class AccountV2:
    def __init__(self, opening: int):
        self._transactions = [opening]

    def deposit(self, amount: int) -> None:
        self._transactions.append(amount)

    @property
    def balance(self) -> int:
        return sum(self._transactions)


def run(account) -> int:
    account.deposit(50)
    account.deposit(25)
    return account.balance


print(run(AccountV1(100)))
print(run(AccountV2(100)))
```

Output:

```
175
175
```

`run()` cannot tell the two versions apart, and doesn't need to. That's the entire
payoff of abstraction: **the caller depends on what a module does, never on how it does
it — so the "how" can change for free.** This is why "encapsulation lets the
implementation change" is the right one-line answer in an interview, not "encapsulation
hides fields" — hiding fields is the mechanism; a free-to-change implementation is the
point.

The same demonstration in Go, using an interface (§6 explains these properly) so `run`
can accept either concrete type:

```go
package main

import "fmt"

type Account interface {
	Deposit(amount int)
	Balance() int
}

type AccountV1 struct{ balance int }

func NewAccountV1(opening int) *AccountV1 { return &AccountV1{balance: opening} }
func (a *AccountV1) Deposit(amount int)   { a.balance += amount }
func (a *AccountV1) Balance() int         { return a.balance }

type AccountV2 struct{ transactions []int }

func NewAccountV2(opening int) *AccountV2 { return &AccountV2{transactions: []int{opening}} }
func (a *AccountV2) Deposit(amount int)   { a.transactions = append(a.transactions, amount) }
func (a *AccountV2) Balance() int {
	total := 0
	for _, t := range a.transactions {
		total += t
	}
	return total
}

func run(a Account) int {
	a.Deposit(50)
	a.Deposit(25)
	return a.Balance()
}

func main() {
	fmt.Println(run(NewAccountV1(100)))
	fmt.Println(run(NewAccountV2(100)))
}
```

Output:

```
175
175
```

---

## 5 · Coupling and cohesion, in plain terms

Two more words that sound abstract until you see them side by side.

**Coupling** is how much one piece of code has to know about another to work.
**Cohesion** is how much the things inside *one* piece of code actually belong together.

The goal is always the same shape: **low coupling, high cohesion** — modules that don't
need to know much about each other, and where everything inside one module is there for
a related reason.

```python
# HIGH COUPLING: to compute shipping cost you must hand over a whole Customer
# object, and this function reaches into fields that have nothing to do with
# shipping — it silently depends on Customer's entire shape.
def shipping_cost(customer, weight_kg):
    if customer.loyalty_tier == "gold" and customer.account.is_active:
        return 0
    return weight_kg * 2.5

# LOWER COUPLING: this function asks for exactly what it needs, and nothing
# about it changes if Customer grows ten more unrelated fields tomorrow.
def shipping_cost(free_shipping: bool, weight_kg: float) -> float:
    return 0 if free_shipping else weight_kg * 2.5
```

Neither version is "wrong" in isolation — the second one just needs its caller to do a
little more work deciding `free_shipping`. That's usually the right trade: the decision
of *who gets free shipping* is a business rule that belongs somewhere specific (probably
near `Customer`), and `shipping_cost` shouldn't need to know the rule exists at all.

Cohesion is the same idea turned inward — instead of "how much does this function
depend on things outside it," it asks "does everything *inside* this module belong
together?"

```python
# LOW COHESION: three unrelated jobs sharing one name because they happen
# to run one after another. Nothing connects "validate," "email," and "log"
# except that they're both called from the same place.
class OrderHelper:
    def validate_address(self, order): ...
    def send_receipt_email(self, order): ...
    def write_audit_log(self, order): ...

# HIGH COHESION: each class does one related job. A change to how receipts
# are formatted can never accidentally break address validation, because
# they're not sharing a file, a name, or a reason to change.
class AddressValidator:
    def validate(self, order): ...

class ReceiptMailer:
    def send(self, order): ...

class OrderAuditLog:
    def record(self, order): ...
```

A useful test for cohesion: **can you describe what a module does in one sentence,
without using the word "and"?** `OrderHelper` above needs "validates addresses, *and*
sends emails, *and* writes logs" — three sentences wearing one name. Each of the three
split-out classes needs only one.

`03_modularity_coupling_and_api_design.md` gives coupling and cohesion their full
treatment — several distinct *kinds* of each, ranked from worst to best, and a sharper
vocabulary (*connascence*) for talking about exactly how two pieces of code depend on
each other.

---

## 6 · Interfaces: the shape of a thing

An **interface** is a promise about *what a piece of code can do*, with no promise
about *how*. Anything that keeps the promise can be used anywhere the interface is
expected — which is what lets you swap one implementation for another without touching
the code that uses it.

Say a program needs to notify a user two different ways — email and SMS — and more
channels will probably show up later:

```python
from typing import Protocol


class Notifier(Protocol):
    def send(self, message: str) -> None: ...


class EmailNotifier:
    def send(self, message: str) -> None:
        print(f"[email] {message}")


class SMSNotifier:
    def send(self, message: str) -> None:
        print(f"[sms] {message}")


def welcome(user_name: str, notifier: Notifier) -> None:
    notifier.send(f"Welcome, {user_name}!")


welcome("Asha", EmailNotifier())
welcome("Asha", SMSNotifier())
```

Output:

```
[email] Welcome, Asha!
[sms] Welcome, Asha!
```

`welcome()` never mentions `EmailNotifier` or `SMSNotifier` by name. It only knows about
the *shape* — "something with a `send(message)`" — so adding a third channel
(`PushNotifier`, `SlackNotifier`, anything) never requires changing `welcome` at all.
That's the payoff: **code written against an interface doesn't need to change when a new
implementation of it shows up.**

Go's interfaces work the same way, with one difference worth knowing early: a Go type
never *declares* which interfaces it implements. If its methods happen to match, it
satisfies the interface automatically — this is called **structural typing**, and
`02_oop_and_domain_modeling.md` §5 covers exactly how it differs from Python's
`Protocol` and from nominal interfaces (Java's `implements`).

```go
package main

import "fmt"

type Notifier interface {
	Send(message string)
}

type EmailNotifier struct{}

func (EmailNotifier) Send(message string) { fmt.Println("[email]", message) }

type SMSNotifier struct{}

func (SMSNotifier) Send(message string) { fmt.Println("[sms]", message) }

func Welcome(userName string, n Notifier) {
	n.Send(fmt.Sprintf("Welcome, %s!", userName))
}

func main() {
	Welcome("Asha", EmailNotifier{})
	Welcome("Asha", SMSNotifier{})
}
```

Output:

```
[email] Welcome, Asha!
[sms] Welcome, Asha!
```

Notice that `EmailNotifier` and `SMSNotifier` never write the word `Notifier` anywhere
in their own definitions — Go worked out on its own that both satisfy it, just by
having a matching `Send(string)` method.

---

## 7 · Requirements: functional vs. non-functional

Before any of the above is worth doing, you need to know what you're actually building.
Every design conversation — real or in an interview — starts by sorting what's being
asked into two buckets:

| Kind | Answers | Example (a library checkout system) |
|---|---|---|
| **Functional requirement** | *What* must the system do? | "A member can check out a book if it isn't already checked out." "A member can return a book." |
| **Non-functional requirement** | *How well* must it do it? | "Must never let two members check out the same physical book at once." "Checkout must respond in under 200ms." "Must support 10,000 members." |

Functional requirements describe **behavior**; non-functional requirements describe
**qualities** of that behavior — correctness under concurrent use, speed, capacity,
security, availability. Skipping the second bucket is the single most common mistake in
a design interview: a design that's functionally perfect but was never asked to survive
two people checking out the same book at the same instant will fall apart the moment a
concurrency question follows it up.

A simple way to remember the split: functional requirements go in the **class diagram**
(what methods exist, what they do); non-functional requirements go in the **design
decisions** (which data structure, which locking strategy, which trade-off you chose
and why). `14_low_level_design_interview_playbook.md` §4 turns this into the actual
first five minutes of an interview — the questions to ask, and why asking them first
matters more than the code that follows.

---

## 8 · A complete worked example, start to finish

Put §§3–7 together on one small, realistic problem: a corner library that lets members
check out and return books.

**Requirements first**, following §7's split:

- *Functional:* a member can check out an available book; a member can return a book
  they hold.
- *Non-functional:* the same book can never be checked out by two members at once (the
  one rule this whole example exists to protect).

**The naive version** — global state, no rule enforced anywhere:

```python
checked_out = {}

def checkout(book_id):
    checked_out[book_id] = True

checkout("B1")
checkout("B1")           # "succeeds" again — two members now think they hold the book
print(checked_out)
```

Output:

```
{'B1': True}
```

This is §3's dictionary problem all over again: the non-functional requirement —
*never double-book a copy* — is written nowhere, so nothing stops it from being broken.

**The designed version** — one class owns the rule, and it's the only door:

```python
class Library:
    def __init__(self):
        self._checked_out: set[str] = set()

    def checkout(self, book_id: str) -> None:
        if book_id in self._checked_out:
            raise ValueError(f"{book_id} is already checked out")
        self._checked_out.add(book_id)

    def return_book(self, book_id: str) -> None:
        self._checked_out.discard(book_id)


library = Library()
library.checkout("B1")
try:
    library.checkout("B1")
except ValueError as e:
    print(e)
library.return_book("B1")
library.checkout("B1")            # fine again, now that it was returned
print("ALL GOOD")
```

Output:

```
B1 is already checked out
ALL GOOD
```

And in Go — the same rule, the same one door:

```go
package main

import "fmt"

// BEFORE: a package-level map. Nothing stops checking out the same book twice.
var checkedOutBefore = map[string]bool{}

func checkoutBefore(bookID string) {
	checkedOutBefore[bookID] = true
}

// AFTER: one small type owns the rule.
type Library struct {
	checkedOut map[string]bool
}

func NewLibrary() *Library {
	return &Library{checkedOut: map[string]bool{}}
}

func (l *Library) Checkout(bookID string) error {
	if l.checkedOut[bookID] {
		return fmt.Errorf("%s is already checked out", bookID)
	}
	l.checkedOut[bookID] = true
	return nil
}

func (l *Library) Return(bookID string) {
	delete(l.checkedOut, bookID)
}

func main() {
	checkoutBefore("B1")
	checkoutBefore("B1") // silently "succeeds" again
	fmt.Println(checkedOutBefore)

	library := NewLibrary()
	_ = library.Checkout("B1")
	if err := library.Checkout("B1"); err != nil {
		fmt.Println(err)
	}
	library.Return("B1")
	if err := library.Checkout("B1"); err != nil {
		fmt.Println(err)
	}
	fmt.Println("ALL GOOD")
}
```

Output:

```
map[B1:true]
B1 is already checked out
ALL GOOD
```

This tiny `Library` already has every idea from this chapter in it: a **module** (§2)
that **encapsulates** (§4) a `set`/`map` behind **one door** (§3) that enforces a
**non-functional requirement** (§7) — and it did it with **low coupling**: nothing
about `Library` depends on how a book got its ID or who's asking.

It's also, not by accident, a miniature of `SoftwareDesign/lld/001_parking_lot` and
every other LLD problem in this track: *some resource, some rule about who can hold it,
one class that makes breaking the rule impossible.* Real LLD problems add more entities,
concurrency, and edge cases — never a different underlying idea.

---

## 9 · Glossary

Every term this chapter used, in one line, for quick reference:

| Term | One line |
|---|---|
| **Program** | A sequence of instructions a computer runs. |
| **Function / method** | A named, reusable group of instructions. |
| **Module** | A named, reusable group of related functions and data — a file, class, or package. |
| **Class / object** | Data bundled with the only code allowed to change it in ways that matter. |
| **Invariant** | A rule that must always hold (e.g. "balance never negative"), enforced by a class's own methods. |
| **State** | The data a class currently holds — what an invariant is a rule *about*. |
| **Encapsulation** | Hiding data so only a module's own code can touch it. |
| **Abstraction** | Callers depend on *what* a module does, never *how* — so the *how* can change freely. |
| **Coupling** | How much one piece of code has to know about another to work. Lower is better. |
| **Cohesion** | How much the things inside one module belong together. Higher is better. |
| **Interface** | A promise about what a piece of code can do, independent of how. |
| **Dependency** | Code that can't be understood or changed without also understanding something else. |
| **Functional requirement** | What the system must do. |
| **Non-functional requirement** | How well it must do it — speed, capacity, correctness under concurrency, security. |
| **Design** | The set of decisions about how code is organized so it stays easy to change. |

---

## 10 · How to read the rest of this track

Every idea above gets a full, precise treatment later — this chapter only gave you
enough to follow along without stopping to look up a word:

| This chapter's term | Gets its full treatment in |
|---|---|
| Design, complexity, "why did this get hard to change" | `01_philosophy_of_software_design.md` §1–§4 |
| Class, invariant, the four pillars precisely | `02_oop_and_domain_modeling.md` §1–§3 |
| Abstraction / encapsulation, applied to a real domain model | `02_oop_and_domain_modeling.md` §7–§8 |
| Coupling, cohesion, and connascence, ranked and named | `03_modularity_coupling_and_api_design.md` §1–§3 |
| Interfaces — nominal vs. structural, Python vs. Go in depth | `02_oop_and_domain_modeling.md` §5 |
| Requirements, and the rest of a 45-minute LLD interview | `14_low_level_design_interview_playbook.md` §3–§5 |

From here, follow `README.md`'s path starting at step 1 — `01_philosophy_of_software_design.md`.
Nothing in `01`–`14` repeats this chapter; it only uses the words it defined.

---

## 11 · Checklist before you move on

You're ready for `01` when you can, without looking back:

- [ ] Say in one sentence what a class is *for* (not what it *has*).
- [ ] Explain why the dictionary version of `Account` in §3 lost money, in terms of
      "where does the rule live," not "the code had a bug."
- [ ] Explain the difference between encapsulation and abstraction — one sentence each.
- [ ] Look at two functions and say which one is more tightly coupled to its caller's
      internals, and why.
- [ ] Explain why `welcome()` in §6 never needed to change when `SMSNotifier` was added.
- [ ] Sort a made-up feature request into functional vs. non-functional requirements.

If any of those feels shaky, re-read that section — each one is short by design.
