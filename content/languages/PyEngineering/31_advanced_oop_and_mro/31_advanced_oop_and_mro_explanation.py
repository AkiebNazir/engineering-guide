"""
Topic 31: Advanced OOP, Multiple Inheritance & MRO

================================================================================
EXPLANATION
================================================================================

Python supports Multiple Inheritance. When a class inherits from multiple parents,
Python uses the C3 Linearization algorithm to determine the Method Resolution Order (MRO).

Furthermore, a senior engineer uses Abstract Base Classes (abc.ABC) to enforce
contracts (interfaces) and Mixins to provide reusable chunks of functionality
without creating deep, rigid inheritance trees.

---
DIAGRAM: Method Resolution Order (MRO)
---
```mermaid
graph TD
    O[object]
    A[A] --> O
    B[B] --> O
    C[C inherits A, B] --> A
    C --> B
    
    %% MRO is C -> A -> B -> object
```

================================================================================
YOUR TASK
================================================================================
1. Create an Abstract Base Class `LoggerInterface` with an abstract method `log`.
2. Create a Mixin `TimestampMixin` that provides a method `get_timestamp()`.
3. Create a class `Database` that arbirarily inherits from `A` and `B` (defined below).
   Predict and test the MRO when you call `db.save()`.
"""

from abc import ABC, abstractmethod
from datetime import datetime

# ============================================================================
# 1. Abstract Base Classes (ABC)
# ============================================================================
class LoggerInterface:
    """
    TODO: Make this class an Abstract Base Class.
    Define an abstract method `log(self, message: str) -> None`.
    """
    pass

# ============================================================================
# 2. Mixins
# ============================================================================
class TimestampMixin:
    """
    TODO: Implement `get_timestamp(self) -> str` which returns the current
    time in ISO format.
    """
    pass

class ConsoleLogger: # TODO: Inherit from LoggerInterface and TimestampMixin
    """
    TODO: Implement the `log` method. It should print: "[TIMESTAMP] message".
    """
    pass

# ============================================================================
# 3. Multiple Inheritance & MRO
# ============================================================================
class A:
    def save(self):
        print("Saving from A")

class B:
    def save(self):
        print("Saving from B")

class Database:
    """
    TODO: Inherit from both A and B. When save() is called, whose save() runs?
    Hint: It depends on the order you specify them: class Database(A, B).
    Call super().save() inside your save() to see how it delegates.
    """
    pass

if __name__ == "__main__":
    print("Run the solution file to see the working implementation!")
