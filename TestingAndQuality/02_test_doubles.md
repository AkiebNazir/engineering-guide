# Test Doubles: Mocks, Stubs, and Fakes

When a function relies on a database or a third-party API (like Stripe), you cannot use the real thing in a unit test. You must substitute it with a "Test Double".

## 1. Stubs
A stub provides canned answers to calls made during the test.
*Use when*: You just need the dependency to return a specific value so your code can proceed.
```python
# Stubbing the Stripe API to always return success
stripe_api.charge = lambda amount: {"status": "success", "id": "123"}
```

## 2. Spies
A spy is a stub that also records how it was called (arguments, how many times).
*Use when*: You want to assert that a side effect happened.
```python
# Did we actually call the email service with the right address?
email_service = spy()
user.register("alice@example.com")
assert email_service.send_welcome.was_called_with("alice@example.com")
```

## 3. Mocks
Mocks are objects pre-programmed with expectations. If the expectations aren't met, the test fails. (Often used interchangeably with Spies in modern frameworks).
*Warning*: Over-mocking leads to tests that just mirror the implementation. If you change a variable name, the mock breaks. Avoid "mocking out the world."

## 4. Fakes
A fake actually has working implementations, but usually takes some shortcut which makes them not suitable for production.
*Use when*: The logic is complex and stubs are too tedious.
```python
# A fake database that stores data in an array instead of Postgres
class FakeUserRepository:
    def __init__(self):
        self.users = {}
    def save(self, user):
        self.users[user.id] = user
    def get(self, id):
        return self.users.get(id)
```
Fakes are the gold standard for testing domain logic without a database, because they act like the real dependency without the I/O cost.
