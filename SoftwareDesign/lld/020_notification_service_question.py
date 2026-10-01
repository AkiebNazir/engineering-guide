"""
================================================================================
LLD 020 · Multi-Channel Notification Service                       [Tier 2]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement a multi-channel notification service (think a
simplified Courier / notification microservice) that application code calls
to notify a user of an event — "your order shipped", "your password
changed" — across channels like email and SMS.

The interviewer says: "Design a notification service." These are the agreed
requirements.

REQUIREMENTS
------------
  1. TemplateRegistry() — register(name, template) stores a template whose
     {placeholders} are filled by keyword variables. render(name, **vars)
     -> str fills the template. Unknown name -> UnknownTemplateError. A
     placeholder with no matching keyword -> MissingTemplateVariableError.
  2. PreferenceStore() — set_preferences(user_id, notification_type,
     channels: set[str]) records which channel names are enabled for that
     user + notification type (overwrites any prior value for that pair).
     enabled_channels(user_id, notification_type) -> set[str]: returns the
     empty set for a user+type that was never configured, but raises
     UnknownUserError for a user_id that never called set_preferences at
     all (for ANY notification type).
  3. A channel is anything with send(recipient: str, message: str) -> None;
     it may raise ChannelSendError to mean "transient, worth retrying" — any
     other exception is a bug and must not be retried.
  4. RetryingChannel(inner, max_attempts=3, sleep=time.sleep, backoff_s=0.05)
     decorates a channel: send(recipient, message) -> int (the attempt
     number that succeeded) retries a ChannelSendError up to max_attempts
     times, sleeping backoff_s * attempt between tries using the INJECTED
     sleep (never call time.sleep directly). After the last attempt still
     fails, raises ChannelDeliveryFailed(attempts, last_error) — never lets
     the raw error escape, never silently drops it either.
  5. RateLimiter(max_per_window, window_s, clock=time.monotonic) —
     allow(user_id) -> bool: True and consumes one slot iff the user has
     made fewer than max_per_window allowed calls in the trailing window_s
     seconds; False (consumes nothing) otherwise. Users are independent.
  6. NotificationService(channels: dict[str, <channel>], templates,
     preferences, rate_limiter, sleep=time.sleep, max_attempts=3,
     backoff_s=0.05).notify(user_id, notification_type, **template_vars)
     -> list[DeliveryResult]:
       a. Render the message (may raise UnknownTemplateError /
          MissingTemplateVariableError — caller errors, let them propagate).
       b. Look up the user's enabled channels for notification_type (may
          raise UnknownUserError — caller error).
       c. Intersect with the channels this service was built with; if that
          is empty, return [] (nothing to do — not an error).
       d. Otherwise call rate_limiter.allow(user_id) ONCE for the whole
          call; if it returns False, return a THROTTLED DeliveryResult
          (attempts=0) for each channel that would have been attempted,
          WITHOUT calling any channel.
       e. Otherwise attempt each channel in turn through its own
          RetryingChannel; one channel's exhausted retries must not stop
          the others — record SENT (with attempts) or FAILED (with attempts
          and error) per channel.
     notify() itself never raises for an ordinary channel failure — only for
     the two caller errors in (a)/(b) above.
  7. DeliveryResult(channel: str, status: DeliveryStatus, attempts: int,
     error: str | None = None). DeliveryStatus is SENT / FAILED / THROTTLED.
     A channel disabled by preference (or simply not registered with this
     service) never appears in the returned list at all.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * Are channel strategy, templates, preferences, retry and rate limiting
    four separate, independently testable pieces, or fused into one
    notify() god-method?
  * Why inject sleep AND clock instead of calling time.sleep /
    time.monotonic directly?
  * Where does "should this be skipped" live vs "how do we send it" vs
    "how many times do we retry"?
  * Does one channel's failure or exhausted retries crash the whole
    notify() call, or take down the other channels with it?
  * Is the rate limiter global or per user? Were a THROTTLED call's
    channels ever actually touched?

FOLLOW-UPS TO PREPARE
---------------------
  priority/urgent notifications bypassing the limit · digest/batching noisy
  notifications · delivery receipts & webhooks · dead-letter queue for
  exhausted retries · multi-channel fallback (SMS if email fails) ·
  distributed rate limiting across service instances.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Callable


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


class TemplateRegistry:
    def __init__(self) -> None:
        raise NotImplementedError

    def register(self, name: str, template: str) -> None:
        raise NotImplementedError

    def render(self, template_name: str, **variables) -> str:
        raise NotImplementedError


class PreferenceStore:
    def __init__(self) -> None:
        raise NotImplementedError

    def set_preferences(self, user_id: str, notification_type: str, channels: set[str]) -> None:
        raise NotImplementedError

    def enabled_channels(self, user_id: str, notification_type: str) -> set[str]:
        raise NotImplementedError


class RetryingChannel:
    def __init__(self, inner, max_attempts: int = 3,
                 sleep: Callable[[float], None] = time.sleep, backoff_s: float = 0.05) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def send(self, recipient: str, message: str) -> int:
        raise NotImplementedError


class RateLimiter:
    def __init__(self, max_per_window: int, window_s: float,
                 clock: Callable[[], float] = time.monotonic) -> None:
        raise NotImplementedError

    def allow(self, user_id: str) -> bool:
        raise NotImplementedError


class NotificationService:
    def __init__(self, channels: dict, templates: TemplateRegistry,
                 preferences: PreferenceStore, rate_limiter: RateLimiter,
                 sleep: Callable[[float], None] = time.sleep,
                 max_attempts: int = 3, backoff_s: float = 0.05) -> None:
        raise NotImplementedError

    def notify(self, user_id: str, notification_type: str, **template_vars) -> list[DeliveryResult]:
        raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
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


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
