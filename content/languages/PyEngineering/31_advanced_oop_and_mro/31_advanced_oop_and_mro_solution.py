"""
Topic 31: Advanced OOP, Multiple Inheritance & MRO

================================================================================
SOLUTION & WALKTHROUGH
================================================================================
"""

from abc import ABC, abstractmethod
from datetime import datetime

# ============================================================================
# 1. Abstract Base Classes (ABC)
# ============================================================================
# By inheriting from ABC and using @abstractmethod, we enforce that any child
# class MUST implement the log method. Python will raise a TypeError upon
# instantiation if they don't.
class LoggerInterface(ABC):
    @abstractmethod
    def log(self, message: str) -> None:
        pass

# ============================================================================
# 2. Mixins
# ============================================================================
# A Mixin is a class that contains methods for use by other classes without
# having to be the parent class of those other classes. They are meant to be
# inherited alongside other classes.
class TimestampMixin:
    def get_timestamp(self) -> str:
        return datetime.now().isoformat()

# We inherit the interface first, then the Mixin.
class ConsoleLogger(LoggerInterface, TimestampMixin):
    def log(self, message: str) -> None:
        # We can use self.get_timestamp() because we inherited TimestampMixin
        print(f"[{self.get_timestamp()}] {message}")

# ============================================================================
# 3. Multiple Inheritance & MRO
# ============================================================================
class A:
    def save(self):
        print("Saving from A")
        
        # In multiple inheritance, super() DOES NOT mean "parent".
        # It means "the next class in the Method Resolution Order (MRO)".
        # If A was inherited alongside B, super() here might point to B!
        if hasattr(super(), 'save'):
            super().save()

class B:
    def save(self):
        print("Saving from B")

# Database inherits from A, then B.
# The MRO will be: Database -> A -> B -> object
class Database(A, B):
    def save(self):
        print("Saving from Database")
        # Calls the next class in the MRO, which is A.
        super().save()

if __name__ == "__main__":
    print("--- Testing Abstract Base Classes & Mixins ---")
    logger = ConsoleLogger()
    logger.log("System booted up.")
    
    print("\n--- Testing Multiple Inheritance & MRO ---")
    db = Database()
    
    # You can view the MRO explicitly:
    print(f"MRO is: {[cls.__name__ for cls in Database.mro()]}")
    
    print("\nCalling db.save():")
    # Output will be:
    # Saving from Database
    # Saving from A
    # Saving from B
    db.save()
