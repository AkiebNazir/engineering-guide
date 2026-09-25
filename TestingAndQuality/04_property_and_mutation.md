# Advanced: Property-Based and Mutation Testing

Writing tests manually means you only test the edge cases you can think of. Advanced methodologies generate tests for you to find the bugs you missed.

## 1. Property-Based Testing

Instead of writing a test like `assert sum(2, 2) == 4`, you define the *properties* of the function, and the testing framework (like Hypothesis for Python, or QuickCheck) generates thousands of random inputs to try and break those properties.

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_properties(xs):
    result = my_custom_sort(xs)
    
    # Property 1: Length stays the same
    assert len(result) == len(xs)
    
    # Property 2: Result is ordered
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))
```
The framework will throw negative numbers, massive integers, empty lists, and NaN at your function. If it finds a failure, it will "shrink" the input to find the smallest possible example that breaks your code.

## 2. Mutation Testing

Code coverage metrics (e.g., "95% of lines are covered by tests") are lies. You can execute a line of code in a test without actually `assert`ing anything about the result.

Mutation testing proves that your tests actually catch bugs.

**How it works (e.g., using Stryker or PIT):**
1. The framework changes your source code (a "mutation"). It might change `a + b` to `a - b`, or `if (x > 0)` to `if (x >= 0)`.
2. It runs your test suite.
3. If your tests **pass**, it means your tests didn't notice the bug! The mutant "survived".
4. If your tests **fail**, your tests did their job! The mutant was "killed".

The goal of mutation testing is to kill 100% of the mutants. It forces you to write incredibly robust assertions.
