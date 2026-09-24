"""
Topic 29: AST Manipulation & Introspection

================================================================================
EXPLANATION
================================================================================

Python is a highly dynamic language. You can inspect functions, classes, and
objects at runtime using the `inspect` module. Furthermore, Python allows you
to parse source code into an Abstract Syntax Tree (AST), manipulate it, and
even compile it back into executable code.

This is how tools like Pytest (which rewrites assert statements to show detailed
errors) and linters (like Flake8/Ruff) work.

---
DIAGRAM: The AST Pipeline
---
```mermaid
graph LR
    A[Source Code String] -->|ast.parse| B(Abstract Syntax Tree)
    B -->|ast.NodeTransformer| C(Modified AST)
    C -->|compile()| D(Code Object)
    D -->|exec()| E[Running Program]
```

================================================================================
YOUR TASK
================================================================================
1. Use the `inspect` module to write a function that takes ANY function, inspects
   its signature, and prints out its arguments and their type hints.
2. Use the `ast` module to write a simple linter that takes a string of Python
   code and finds all `while` loops that don't have a `break` statement inside them
   (a potential infinite loop risk).
"""

import inspect
import ast
from typing import Callable, Any

# ============================================================================
# 1. Introspection (inspect module)
# ============================================================================
def analyze_function_signature(func: Callable[..., Any]):
    """
    TODO: Use inspect.signature to get the parameters of the function.
    Print the name of each parameter and its annotation (type hint).
    """
    pass

# Test function for introspection
def sample_api_handler(request_id: str, payload: dict, timeout: int = 30) -> bool:
    return True

# ============================================================================
# 2. AST Manipulation
# ============================================================================
class InfiniteLoopDetector(ast.NodeVisitor):
    """
    TODO: Implement visit_While.
    When a While node is visited, check if any of its descendant nodes is a Break node.
    If not, print a warning with the line number.
    Hint: use ast.walk(node) to check all descendants.
    """
    pass

def lint_code(source_code: str):
    """
    TODO: Parse the source code into an AST and run the InfiniteLoopDetector.
    """
    pass

sample_code = \"\"\"
def safe_loop():
    x = 0
    while x < 10:
        if x == 5:
            break
        x += 1

def dangerous_loop():
    while True:
        print("I never stop!")
\"\"\"

if __name__ == "__main__":
    print("Run the solution file to see the working implementation!")
