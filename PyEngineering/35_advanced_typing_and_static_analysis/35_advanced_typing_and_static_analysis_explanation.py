"""
Topic 35: Advanced Typing & Static Analysis

================================================================================
EXPLANATION
================================================================================

Python's typing system has evolved massively. A senior engineer doesn't just use
`int` and `str`; they use advanced constructs to give `mypy` and `pyright` the
exact information needed to prove correctness before the code ever runs.

- `@overload`: Defines multiple valid signatures for a single function.
- `Literal`: Restricts a value to a specific set of strings or integers.
- `TypeGuard` (PEP 647): Tells the type checker that a boolean-returning function
  actually narrows the type of a variable.

---
DIAGRAM: TypeGuard Flow
---
```mermaid
graph TD
    A[x: Any] --> B{is_string_list(x)}
    B -- True --> C[x: list[str]]
    B -- False --> D[x: Any]
```

================================================================================
YOUR TASK
================================================================================
1. Use `@overload` to define a function `fetch_data` that:
   - If passed `return_json=True`, returns a `dict`.
   - If passed `return_json=False`, returns a `bytes`.
2. Write a `TypeGuard` function `is_valid_user_dict` that takes a `dict` and
   narrows it to `dict[str, str]` if all keys and values are strings.
"""

from typing import Any, overload, Literal, TypeGuard

# ============================================================================
# 1. Overloads & Literals
# ============================================================================

# TODO: Write the @overload definitions for fetch_data.

def fetch_data(url: str, return_json: bool) -> Any:
    """
    TODO: Implement the actual function.
    """
    pass

# ============================================================================
# 2. TypeGuard
# ============================================================================

def is_valid_user_dict(val: dict[Any, Any]) -> bool:
    """
    TODO: Add the proper return type hint `TypeGuard[dict[str, str]]`.
    Implement the logic to return True ONLY if all keys and values are strings.
    """
    pass

def process_user(val: dict[Any, Any]):
    if is_valid_user_dict(val):
        # TODO: If is_valid_user_dict returns True, mypy knows `val` is dict[str, str].
        # Print a key-value pair.
        pass
    else:
        print("Invalid user dictionary.")

if __name__ == "__main__":
    print("Run the solution file to see the working implementation!")
