# The Testing Pyramid and Unit Tests

The Testing Pyramid dictates that you should have many fast, cheap tests at the bottom, and fewer slow, expensive tests at the top.

```arch
%% caption: The classic testing pyramid balances speed, cost, and confidence.
route straight
node e2e "E2E Tests\\n(UI / Browser)" at 1,0 icon=client color=red
node it "Integration Tests\\n(DB / API)" at 1,1 icon=network color=amber
node unit "Unit Tests\\n(Functions / Classes)" at 1,2 icon=code color=green

unit -> it : "Fewer, but higher confidence"
it -> e2e : "Fewer, but higher confidence"
```

## 1. Unit Tests

Unit tests verify the smallest testable parts of an application in complete isolation.

**Characteristics:**
- They do not talk to a real database.
- They do not make network calls.
- They execute in milliseconds. You can run 10,000 of them in 5 seconds.

### Anatomy of a Good Unit Test
Use the **Arrange-Act-Assert** pattern.
```python
def test_calculate_discount():
    # Arrange
    cart = Cart(total=100)
    user = User(is_vip=True)

    # Act
    discount = calculate_discount(cart, user)

    # Assert
    assert discount == 20
```

### What NOT to test
Do not test private methods. Test the *public API* of the class. If you test private methods, your tests become tightly coupled to the implementation details, and refactoring will break the tests even if the overall behavior didn't change (brittle tests).

## 2. Test-Driven Development (TDD)

TDD is a design process, not just a testing process.
1. **Red**: Write a failing test for the feature you are about to build.
2. **Green**: Write the absolute minimum amount of code to make the test pass (even if it's ugly).
3. **Refactor**: Clean up the code. The test ensures you didn't break anything.

By writing the test first, you are forced to design a clean, modular API, because highly coupled code is painfully difficult to test.
