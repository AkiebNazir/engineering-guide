"""
================================================================================
SOLUTION · LLD 020 · Multi-Channel Notification Service            [Tier 2]
================================================================================

THE CORE IDEA
--------------
A notification service is four small, independently-testable pieces glued by
one thin orchestrator. Beginners fuse all four into one notify() god-method;
interviewers are checking whether you can keep them apart:

    Piece               answers                              testable alone
    TemplateRegistry    WHAT does the message say?            yes (§ templates)
    PreferenceStore     SHOULD this user get it on THIS       yes (§ preferences)
                        channel, for THIS notification type?
    RetryingChannel     HOW MANY TIMES do we retry a          yes (§ retry)
                        transient send failure, and how?
    RateLimiter         IS this user even allowed to send      yes (§ rate limit)
                        right now?

NotificationService.notify() only wires these together and AGGREGATES the
outcome: a channel that fails becomes a DeliveryResult(FAILED, ...), not an
exception that kills the whole call (Ousterhout, "A Philosophy of Software
Design" §7, technique 3 — aggregate error handling instead of propagating a
crash for a per-channel fact). notify() itself only ever raises for a genuine
CALLER error: an unknown template/notification_type, or a user_id that was
never registered with the preference store.

Two testability rules interviewers probe here, same as lld/012's clock:
    * RateLimiter takes an INJECTED clock instead of calling time.monotonic().
    * RetryingChannel takes an INJECTED sleep instead of calling time.sleep().
  Both let the whole test suite below run in milliseconds, deterministically,
  with a "backoff" that is provably logical rather than a real wall-clock wait
  (06_error_handling_and_failure_design.md §7, "retries done right").


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. TemplateRegistry: register(name, template); render(name, **vars) -> str.
     Unknown name -> UnknownTemplateError. A template placeholder with no
     matching keyword -> MissingTemplateVariableError.
  2. PreferenceStore: set_preferences(user_id, notification_type, channels);
     enabled_channels(user_id, notification_type) -> set[str]. A user+type
     never configured returns the empty set; a user_id that NEVER called
     set_preferences at all raises UnknownUserError.
  3. A Channel is anything with send(recipient, message); it may raise
     ChannelSendError to mean "transient, worth retrying" — any other
     exception is a bug and must not be retried.
  4. RetryingChannel(inner, max_attempts, sleep, backoff_s) decorates a
     Channel: retries a ChannelSendError up to max_attempts times, sleeping
     backoff_s * attempt between tries, then raises ChannelDeliveryFailed
     (attempts, last_error) — never the raw error, never silently.
  5. RateLimiter(max_per_window, window_s, clock): allow(user_id) -> bool,
     True and consumes one slot iff the user has made fewer than
     max_per_window allowed calls in the trailing window_s seconds. Users
     are independent.
  6. NotificationService(channels, templates, preferences, rate_limiter,
     sleep, max_attempts, backoff_s).notify(user_id, notification_type,
     **template_vars) -> list[DeliveryResult]: respects preferences (a
     disabled or unconfigured channel is never attempted and produces no
     result), checks the rate limiter ONCE per call, and never lets one
     channel's exhausted retries stop delivery on the others.
  Out of scope: persistence, real network channels, delivery receipts/webhooks.


================================================================================
ENTITIES AND INVARIANTS
================================================================================
    DeliveryStatus        SENT / FAILED / THROTTLED
    DeliveryResult        value object: channel, status, attempts, error
    Channel (protocol)    send(recipient, message); may raise ChannelSendError
    RetryingChannel       decorator around one Channel
       INVARIANT: attempts in [1, max_attempts]; either returns an attempt
                  count (success) or raises ChannelDeliveryFailed — nothing
                  else ever escapes send()
    TemplateRegistry      name -> template string
       INVARIANT: render() never mutates stored templates
    PreferenceStore       (user_id, notification_type) -> set[channel name]
       INVARIANT: enabled_channels() raises ONLY for a user_id that never
                  appeared in any set_preferences() call
    RateLimiter           user_id -> deque of allowed-call timestamps
       INVARIANT: at most max_per_window allow()==True results for one
                  user_id in ANY trailing window of length window_s
    NotificationService
       INVARIANT: notify() never raises for a per-channel failure; one
                  channel's exhausted retries never block another channel's
                  attempt within the same call


================================================================================
NOTIFY FLOW TRACE · user u1 subscribed to {email, sms}; limit 3 / 10 s window;
                    email fails its first 2 raw sends, ever, then always
                    succeeds; sms always succeeds; max_attempts = 3
================================================================================
    call#  rate limiter (hits so far)   email                    sms
    1      1/3 allowed                  fail, fail, ok: SENT(3)  ok: SENT(1)
    2      2/3 allowed                  ok (counter already      ok: SENT(1)
                                        past 2): SENT(1)
    3      3/3 allowed                  ok: SENT(1)              ok: SENT(1)
    4      DENIED (would be 4th)        THROTTLED(0), channel    THROTTLED(0),
                                        never touched            channel never
                                                                  touched
Note how email's fail-twice-then-succeed behaviour is a property of the FAKE
channel used below (it counts its own RAW send() calls across the whole run,
not per notify() call) — exactly what makes the retry-math demo below provable
by simple arithmetic instead of hand-waving.


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * notification_type doubles as the template name: one flat namespace, so
    "unknown notification type" and "unknown template" are literally the same
    failure (UnknownTemplateError) instead of two parallel registries that can
    drift out of sync.
  * A channel disabled by preference — or simply never registered with this
    service — produces NO DeliveryResult at all, not a SKIPPED_BY_PREFERENCE
    entry. "Silently skipped, not attempted" is taken literally: the caller
    isn't handed noise about a channel they never asked to use.
  * The rate limiter is checked ONCE per notify() call, not once per channel.
    A notification going out over 3 channels is one unit of the user's
    budget, not three — otherwise multi-channel users would be throttled
    systematically harder than single-channel ones for the identical event.
  * RetryingChannel only retries ChannelSendError. Any other exception (a
    programmer bug: bad recipient type, KeyError in a formatter the channel
    itself uses) propagates immediately instead of being silently retried
    three times and reported as an ordinary FAILED.
  * Per-channel results are aggregated in a list rather than the first
    failure aborting notify() — "aggregate error handling" (Philosophy of
    Software Design §7): one bad channel is a fact ABOUT that channel, not a
    reason to fail the whole notification.
  * One sliding-window-log limiter (the same algorithm as
    lld/012_rate_limiter's SlidingWindowLog, simplified to a single fixed
    algorithm keyed by user_id) is enough here — the four-algorithm menu from
    012 would be gold-plating for this problem's stated requirement.
  * Injected clock (RateLimiter) and injected sleep (RetryingChannel): every
    test below runs in milliseconds with a deterministic outcome; no flaky
    "sleep and hope" retry test.


================================================================================
COMPLEXITY
================================================================================
    TemplateRegistry.render     O(len(template))
    PreferenceStore.enabled_channels   O(1)
    RateLimiter.allow           amortised O(1) (O(expired hits) to purge)
    RetryingChannel.send        O(max_attempts) worst case
    NotificationService.notify  O(channels attempted x max_attempts)


================================================================================
EDGE CASES
================================================================================
  * A user with zero channels enabled for a notification_type (or none of
    them registered with this service) -> notify() returns [] and never
    touches the rate limiter or any channel.
  * A template with no {placeholders} still renders; unused kwargs are
    simply ignored (str.format's normal behaviour).
  * The boundary call that brings a user exactly to max_per_window is still
    allowed; the NEXT one is throttled (matches lld/012's FixedWindow/
    SlidingWindowLog convention: "exactly W old" has expired).
  * Two channels in the same notify() call fail and succeed independently —
    one FAILED, one SENT, in the same result list.
  * A channel that fails on its very first attempt and then is never retried
    again (max_attempts=1) still reports attempts == 1, not 0.
  * Rate-limiter state is per user_id; channel state is per Channel instance
    — neither leaks across a different user or a different NotificationService.


================================================================================
COMMON MISTAKES
================================================================================
  1. One notify() with nested if/else for every channel x template x
     preference combination instead of four composable pieces.
  2. String-formatting the message ad hoc at each call site instead of one
     template registry — copy ends up scattered and inconsistent.
  3. time.sleep() inside the retry loop — slow, flaky tests.
  4. Rate limiting checked AFTER already calling the channel, so a denied
     user still gets spammed once per call before being throttled.
  5. A raised exception from one channel crashing the whole notify() call
     for every other channel in the same request.
  6. Not distinguishing "transient, worth retrying" from "programmer bug,
     don't retry forever" — retrying a KeyError three times just delays it.
  7. One global rate-limit bucket shared across all users instead of keyed
     per user_id.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Priority/urgent notifications bypassing the rate limit -> a second,
    generous limiter for "urgent" and an AND/OR combination of two budgets
    (see lld/012_rate_limiter's CompositeLimiter).
  * Digest/batching -> buffer low-priority notifications and flush one
    combined message per window instead of one per event.
  * Delivery receipts / webhooks -> channels report asynchronously;
    DeliveryResult gains a PENDING status until a callback updates it.
  * Dead-letter queue -> a FAILED result after retries is queued for manual
    replay instead of being dropped on the floor.
  * Fallback channel -> if email FAILED, automatically try SMS for the same
    event (an ordered channel list + an "escalate on failure" policy).
  * Distributed rate limiting -> centralize the limiter in Redis (lld/012's
    own follow-up) so multiple service instances share one budget per user.


================================================================================
RELATED
================================================================================
  lld/012_rate_limiter                (the sliding-window-log algorithm reused
                                       here, simplified to one per-user limiter)
  lld/007_logging_framework           (Appender x Formatter composition is the
                                       same shape as Channel x Template here)
  SoftwareDesign/04_design_patterns_in_practice.md  §3 Strategy, §10 Decorator
  SoftwareDesign/01_philosophy_of_software_design.md  §7 technique 3
                                       (aggregate error handling)
  SoftwareDesign/06_error_handling_and_failure_design.md  §7
                                       (retries done right: injected clock,
                                       bounded attempts)
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol


# ----------------------------------------------------------------------------
# Value objects, statuses, exceptions
# ----------------------------------------------------------------------------
class DeliveryStatus(Enum):
    SENT = "SENT"
    FAILED = "FAILED"
    THROTTLED = "THROTTLED"


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    channel: str
    status: DeliveryStatus
    attempts: int
    error: str | None = None


class UnknownTemplateError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"unknown template / notification_type: {name!r}")
        self.name = name


class MissingTemplateVariableError(Exception):
    def __init__(self, template_name: str, variable: str) -> None:
        super().__init__(f"template {template_name!r} is missing variable {variable!r}")
        self.template_name = template_name
        self.variable = variable


class UnknownUserError(Exception):
    def __init__(self, user_id: str) -> None:
        super().__init__(f"unknown user_id: {user_id!r}")
        self.user_id = user_id


class ChannelSendError(Exception):
    """Raised by a Channel.send() implementation for a transient (retryable) failure."""


class ChannelDeliveryFailed(Exception):
    def __init__(self, attempts: int, last_error: Exception) -> None:
        super().__init__(f"delivery failed after {attempts} attempt(s): {last_error}")
        self.attempts = attempts
        self.last_error = last_error


class Channel(Protocol):
    def send(self, recipient: str, message: str) -> None: ...


# ----------------------------------------------------------------------------
# Templates — the single place message copy lives
# ----------------------------------------------------------------------------
class TemplateRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, str] = {}

    def register(self, name: str, template: str) -> None:
        self._templates[name] = template

    def render(self, template_name: str, **variables) -> str:
        template = self._templates.get(template_name)
        if template is None:
            raise UnknownTemplateError(template_name)
        try:
            return template.format(**variables)
        except KeyError as e:
            raise MissingTemplateVariableError(template_name, str(e.args[0])) from None


# ----------------------------------------------------------------------------
# User preferences — which channels a user wants for which notification type
# ----------------------------------------------------------------------------
class PreferenceStore:
    def __init__(self) -> None:
        self._known_users: set[str] = set()
        self._prefs: dict[tuple[str, str], set[str]] = {}

    def set_preferences(self, user_id: str, notification_type: str, channels: set[str]) -> None:
        self._known_users.add(user_id)
        self._prefs[(user_id, notification_type)] = set(channels)

    def enabled_channels(self, user_id: str, notification_type: str) -> set[str]:
        if user_id not in self._known_users:
            raise UnknownUserError(user_id)
        return set(self._prefs.get((user_id, notification_type), set()))


# ----------------------------------------------------------------------------
# Retry decorator — bounded attempts, injected sleep, aggregated failure
# ----------------------------------------------------------------------------
class RetryingChannel:
    """Wraps a Channel so a ChannelSendError is retried up to max_attempts times."""

    def __init__(self, inner: Channel, max_attempts: int = 3,
                 sleep: Callable[[float], None] = time.sleep, backoff_s: float = 0.05) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self._inner = inner
        self._max_attempts = max_attempts
        self._sleep = sleep
        self._backoff_s = backoff_s

    def send(self, recipient: str, message: str) -> int:
        """Returns the attempt number that succeeded. Raises ChannelDeliveryFailed if none did."""
        last_error: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                self._inner.send(recipient, message)
                return attempt
            except ChannelSendError as e:
                last_error = e
                if attempt < self._max_attempts:
                    self._sleep(self._backoff_s * attempt)          # linear backoff
        raise ChannelDeliveryFailed(self._max_attempts, last_error)


# ----------------------------------------------------------------------------
# Per-user rate limiting — sliding window log, keyed by user_id
# ----------------------------------------------------------------------------
class RateLimiter:
    """At most max_per_window allowed calls per user_id in any trailing window_s."""

    def __init__(self, max_per_window: int, window_s: float,
                 clock: Callable[[], float] = time.monotonic) -> None:
        if max_per_window < 1 or window_s <= 0:
            raise ValueError("max_per_window >= 1 and window_s > 0 required")
        self.max_per_window = max_per_window
        self.window_s = window_s
        self.clock = clock
        self._hits: dict[str, deque] = {}

    def allow(self, user_id: str) -> bool:
        now = self.clock()
        hits = self._hits.setdefault(user_id, deque())
        while hits and hits[0] <= now - self.window_s:
            hits.popleft()
        if len(hits) >= self.max_per_window:
            return False
        hits.append(now)
        return True


# ----------------------------------------------------------------------------
# NotificationService — wires the four pieces together, aggregates results
# ----------------------------------------------------------------------------
class NotificationService:
    def __init__(self, channels: dict[str, Channel], templates: TemplateRegistry,
                 preferences: PreferenceStore, rate_limiter: RateLimiter,
                 sleep: Callable[[float], None] = time.sleep,
                 max_attempts: int = 3, backoff_s: float = 0.05) -> None:
        self._channel_names = list(channels)
        self._retrying = {name: RetryingChannel(ch, max_attempts, sleep, backoff_s)
                          for name, ch in channels.items()}
        self._templates = templates
        self._preferences = preferences
        self._rate_limiter = rate_limiter

    def notify(self, user_id: str, notification_type: str, **template_vars) -> list[DeliveryResult]:
        message = self._templates.render(notification_type, **template_vars)     # caller error
        enabled = self._preferences.enabled_channels(user_id, notification_type)  # caller error
        targets = [name for name in self._channel_names if name in enabled]
        if not targets:
            return []
        if not self._rate_limiter.allow(user_id):
            return [DeliveryResult(name, DeliveryStatus.THROTTLED, 0) for name in targets]
        results: list[DeliveryResult] = []
        for name in targets:
            try:
                attempts = self._retrying[name].send(user_id, message)
                results.append(DeliveryResult(name, DeliveryStatus.SENT, attempts))
            except ChannelDeliveryFailed as e:
                results.append(DeliveryResult(name, DeliveryStatus.FAILED, e.attempts, str(e.last_error)))
        return results


# ===================================================================== TESTS ==
class FakeClock:
    def __init__(self, t: float = 0.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


class FakeSleep:
    """Records requested backoff durations instead of actually sleeping."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


class FakeChannel:
    """A channel whose RAW send() call counter fails the first `fail_first_n`
    calls it ever receives, then always succeeds. Used to make retry outcomes
    exactly computable instead of asserted by comment."""

    def __init__(self, fail_first_n: int = 0) -> None:
        self.fail_first_n = fail_first_n
        self.calls: list[tuple[str, str]] = []

    def send(self, recipient: str, message: str) -> None:
        self.calls.append((recipient, message))
        if len(self.calls) <= self.fail_first_n:
            raise ChannelSendError(f"transient failure #{len(self.calls)}")


class EmailChannel(FakeChannel):
    pass


class SMSChannel(FakeChannel):
    pass


def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _raises(exc, fn) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def run_tests() -> bool:
    all_ok = True
    print("--- templates ---")
    templates = TemplateRegistry()
    templates.register("order_shipped", "Hi {name}, your order #{order_id} has shipped!")
    all_ok &= _check("template renders with variables substituted",
                     templates.render("order_shipped", name="Ann", order_id=42)
                     == "Hi Ann, your order #42 has shipped!")
    all_ok &= _check("unknown template name raises", _raises(UnknownTemplateError, lambda: templates.render("nope")))
    all_ok &= _check("missing variable raises",
                     _raises(MissingTemplateVariableError, lambda: templates.render("order_shipped", name="Ann")))

    print("\n--- user preferences ---")
    preferences = PreferenceStore()
    preferences.set_preferences("u1", "order_shipped", {"email"})
    preferences.set_preferences("u2", "order_shipped", {"email", "sms"})
    email, sms = EmailChannel(), SMSChannel()
    templates2 = TemplateRegistry()
    templates2.register("order_shipped", "Hi {name}, order #{order_id} shipped")
    service = NotificationService({"email": email, "sms": sms}, templates2, preferences,
                                  RateLimiter(100, 60, FakeClock()), sleep=FakeSleep())
    results = service.notify("u1", "order_shipped", name="Ann", order_id=1)
    all_ok &= _check("user with only email enabled gets exactly one DeliveryResult",
                     len(results) == 1 and results[0].channel == "email"
                     and results[0].status == DeliveryStatus.SENT)
    all_ok &= _check("the disabled sms channel was never attempted", sms.calls == [])

    print("\n--- retry: transient failures then success ---")
    preferences.set_preferences("u3", "order_shipped", {"email"})
    flaky = EmailChannel(fail_first_n=2)
    sleeper = FakeSleep()
    svc2 = NotificationService({"email": flaky}, templates2, preferences,
                               RateLimiter(100, 60, FakeClock()), sleep=sleeper, max_attempts=3)
    start = time.perf_counter()
    r = svc2.notify("u3", "order_shipped", name="Bo", order_id=2)
    elapsed = time.perf_counter() - start
    all_ok &= _check("fails twice then succeeds on the 3rd attempt -> SENT, attempts == 3",
                     r[0].status == DeliveryStatus.SENT and r[0].attempts == 3)
    all_ok &= _check("the injected sleep recorded 2 backoffs but no real wall-clock time passed",
                     len(sleeper.calls) == 2 and elapsed < 0.05)

    print("\n--- retry exhaustion on one channel doesn't abort the others ---")
    preferences.set_preferences("u4", "order_shipped", {"email", "sms"})
    dead = EmailChannel(fail_first_n=999)
    alive = SMSChannel(fail_first_n=0)
    svc3 = NotificationService({"email": dead, "sms": alive}, templates2, preferences,
                               RateLimiter(100, 60, FakeClock()), sleep=FakeSleep(), max_attempts=3)
    r2 = {d.channel: d for d in svc3.notify("u4", "order_shipped", name="Cy", order_id=3)}
    all_ok &= _check("email exhausts its retry budget -> FAILED with attempts == max_attempts",
                     r2["email"].status == DeliveryStatus.FAILED and r2["email"].attempts == 3)
    all_ok &= _check("sms for the same call still succeeds",
                     r2["sms"].status == DeliveryStatus.SENT and r2["sms"].attempts == 1)

    print("\n--- rate limiting per user ---")
    preferences.set_preferences("u5", "order_shipped", {"email"})
    preferences.set_preferences("u6", "order_shipped", {"email"})
    rl_channel = EmailChannel()
    clock = FakeClock()
    rl = RateLimiter(max_per_window=3, window_s=10, clock=clock)
    svc4 = NotificationService({"email": rl_channel}, templates2, preferences, rl, sleep=FakeSleep())
    statuses = [svc4.notify("u5", "order_shipped", name="X", order_id=i)[0].status for i in range(5)]
    all_ok &= _check("first 3 sent, next 2 throttled",
                     statuses == [DeliveryStatus.SENT] * 3 + [DeliveryStatus.THROTTLED] * 2)
    all_ok &= _check("throttled calls never touched the channel", len(rl_channel.calls) == 3)
    other = svc4.notify("u6", "order_shipped", name="Y", order_id=1)
    all_ok &= _check("a different user has an independent budget", other[0].status == DeliveryStatus.SENT)
    clock.t += 10
    after = svc4.notify("u5", "order_shipped", name="X", order_id=99)
    all_ok &= _check("advancing the clock past the window refills the budget", after[0].status == DeliveryStatus.SENT)

    print("\n--- caller errors ---")
    all_ok &= _check("unknown user_id raises",
                     _raises(UnknownUserError,
                             lambda: service.notify("ghost", "order_shipped", name="x", order_id=1)))
    all_ok &= _check("unknown notification_type raises",
                     _raises(UnknownTemplateError, lambda: service.notify("u1", "nonexistent_type", name="x")))
    return all_ok
# ================================================================= END TESTS ==


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: retry attempts exactly match the retry policy, for 20 independent channels ---")
    templates = TemplateRegistry()
    templates.register("ping", "ping {n}")
    preferences = PreferenceStore()
    max_attempts = 3
    expected_total = 0
    actual_total = 0
    fakes: list[FakeChannel] = []
    statuses_ok = True
    for i in range(20):
        fail_first_n = i % 5                                    # 0,1,2,3,4 repeating
        user = f"solo-{i}"
        preferences.set_preferences(user, "ping", {"ch"})
        fake = EmailChannel(fail_first_n=fail_first_n)
        fakes.append(fake)
        svc = NotificationService({"ch": fake}, templates, preferences,
                                  RateLimiter(1000, 60, FakeClock()), sleep=FakeSleep(), max_attempts=max_attempts)
        result = svc.notify(user, "ping", n=i)[0]
        expected_attempts = min(fail_first_n + 1, max_attempts)
        expected_status = DeliveryStatus.SENT if fail_first_n < max_attempts else DeliveryStatus.FAILED
        expected_total += expected_attempts
        actual_total += result.attempts
        statuses_ok &= result.status == expected_status
    print(f"      expected total attempts (from the retry-policy formula): {expected_total}")
    print(f"      actual total attempts (from the DeliveryResult objects):  {actual_total}")
    all_ok &= _check("every channel ended in the status the retry policy predicts", statuses_ok)
    all_ok &= _check("recorded attempts across 20 channels match the retry policy exactly",
                     expected_total == actual_total)
    fake_calls_total = sum(len(f.calls) for f in fakes)
    all_ok &= _check("every attempt actually reached the channel fake (no phantom or missing retries)",
                     fake_calls_total == actual_total)

    print("\n--- DEMO 2: rate-limiter cap never exceeded, across 8 users hammering one shared channel ---")
    templates2 = TemplateRegistry()
    templates2.register("burst", "burst {i}")
    preferences2 = PreferenceStore()
    users = [f"user-{i}" for i in range(8)]
    for u in users:
        preferences2.set_preferences(u, "burst", {"email"})
    shared_channel = EmailChannel(fail_first_n=0)                # always succeeds: isolates the rate-limit proof
    limiter = RateLimiter(max_per_window=5, window_s=60, clock=FakeClock())
    svc_burst = NotificationService({"email": shared_channel}, templates2, preferences2, limiter, sleep=FakeSleep())
    per_user_sent = {u: 0 for u in users}
    per_user_throttled = {u: 0 for u in users}
    calls_per_user = 12
    for u in users:
        for i in range(calls_per_user):
            status = svc_burst.notify(u, "burst", i=i)[0].status
            if status == DeliveryStatus.SENT:
                per_user_sent[u] += 1
            else:
                per_user_throttled[u] += 1
    print(f"      {len(users)} users x {calls_per_user} notify() calls each, limit 5 / 60 s, one shared clock (no advance)")
    for u in users:
        print(f"      {u}: sent {per_user_sent[u]}, throttled {per_user_throttled[u]}")
    all_ok &= _check("every user got exactly min(calls, limit) = 5 sent, never more",
                     all(n == 5 for n in per_user_sent.values()))
    all_ok &= _check("every user's remaining 7 calls this window were throttled",
                     all(n == 7 for n in per_user_throttled.values()))
    all_ok &= _check(f"channel fake recorded exactly {5 * len(users)} raw sends (5 per user), not "
                     f"{calls_per_user * len(users)}", len(shared_channel.calls) == 5 * len(users))
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
