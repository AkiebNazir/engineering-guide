"""
Topic 35: Advanced Typing & Static Analysis

================================================================================
SOLUTION & WALKTHROUGH
================================================================================
"""

from typing import Any, overload, Literal, TypeGuard

# ============================================================================
# 1. Overloads & Literals
# ============================================================================
# We use Literal to specify EXACTLY the boolean value passed.
@overload
def fetch_data(url: str, return_json: Literal[True]) -> dict[str, Any]:
    ...

@overload
def fetch_data(url: str, return_json: Literal[False]) -> bytes:
    ...

# The actual implementation must accept the union of all overloaded types.
def fetch_data(url: str, return_json: bool) -> dict[str, Any] | bytes:
    if return_json:
        return {"data": "success"}
    return b"success"

# ============================================================================
# 2. TypeGuard
# ============================================================================
# TypeGuard tells MyPy: "If this function returns True, you can safely assume
# that the variable `val` passed into it is actually a dict[str, str]."
def is_valid_user_dict(val: dict[Any, Any]) -> TypeGuard[dict[str, str]]:
    for k, v in val.items():
        if not isinstance(k, str) or not isinstance(v, str):
            return False
    return True

def process_user(val: dict[Any, Any]):
    # Before the if statement, MyPy thinks `val` is dict[Any, Any]
    if is_valid_user_dict(val):
        # Inside this block, MyPy now KNOWS `val` is dict[str, str]!
        # It will allow string operations on the keys/values.
        for k, v in val.items():
            print(f"{k.upper()}: {v.lower()}")
    else:
        print("Invalid user dictionary.")

if __name__ == "__main__":
    print("--- Testing Overloads ---")
    d = fetch_data("http://example.com", True)
    b = fetch_data("http://example.com", False)
    print(f"return_json=True  -> {type(d)}")
    print(f"return_json=False -> {type(b)}")
    
    print("\n--- Testing TypeGuard ---")
    process_user({"name": "Alice", "role": "Admin"})
    process_user({"name": "Bob", "age": 42}) # Age is an int, will fail guard
