"""
Topic 26: Metaprogramming & Decorators (Class Decorators, Descriptors, Metaclasses)

================================================================================
EXPLANATION
================================================================================

As a senior Python engineer, you will often need to write frameworks, libraries,
or internal tooling that operate on other code. Metaprogramming is the art of
writing code that manipulates code.

In this lesson, we will cover three advanced concepts:
1. Class Decorators: Decorating entire classes, not just functions.
2. Descriptors: Controlling attribute access at the class level (`__get__`, `__set__`).
3. Metaclasses: Controlling the creation of a class itself.

---
DIAGRAM: The Metaprogramming Hierarchy
---
```mermaid
graph TD
    A[Metaprogramming in Python] --> B(Function Decorators)
    A --> C(Class Decorators)
    A --> D(Descriptors)
    A --> E(Metaclasses)
    
    B -.->|Wraps| B1[Individual Methods/Functions]
    C -.->|Modifies| C1[Entire Class Definition]
    D -.->|Manages| D1[Class Attributes across all instances]
    E -.->|Controls| E1[The very creation of the Class]
```

================================================================================
YOUR TASK
================================================================================
1. Implement a Class Decorator `@singleton` that ensures only one instance of
   a class is ever created.
2. Implement a Descriptor `ValidatedField` that enforces type checking and bounds.
3. Implement a Metaclass `RegistryMeta` that automatically registers any class
   that uses it into a global dictionary.
"""

from typing import Any, Type, Dict, Callable

# ============================================================================
# 1. Class Decorator
# ============================================================================
def singleton(cls: Type[Any]) -> Type[Any]:
    """
    TODO: Implement the singleton class decorator.
    It should return a wrapper that intercepts class instantiation and returns
    the same instance if it was already created.
    """
    pass

@singleton
class DatabaseConnection:
    def __init__(self):
        self.connected = True

# ============================================================================
# 2. Descriptors
# ============================================================================
class ValidatedField:
    """
    TODO: Implement the descriptor protocol (__get__, __set__, __set_name__).
    - __set_name__ should store the name of the attribute.
    - __get__ should return the value from the instance's __dict__.
    - __set__ should enforce that the value is of the correct type (int) and > 0.
    """
    def __init__(self, expected_type: Type, min_value: Any = None):
        pass
        
    def __set_name__(self, owner: Type, name: str):
        pass
        
    def __get__(self, instance: Any, owner: Type) -> Any:
        pass
        
    def __set__(self, instance: Any, value: Any):
        pass

class UserAccount:
    age = ValidatedField(int, min_value=18)
    
    def __init__(self, age: int):
        self.age = age

# ============================================================================
# 3. Metaclasses
# ============================================================================
# Global registry for our metaclass
COMPONENT_REGISTRY: Dict[str, Type] = {}

class RegistryMeta(type):
    """
    TODO: Implement the __new__ or __init__ method for this metaclass.
    Whenever a new class is defined using this metaclass, it should automatically
    be added to the COMPONENT_REGISTRY dictionary with its class name as the key.
    """
    pass

class BaseComponent(metaclass=RegistryMeta):
    pass
    
class EmailComponent(BaseComponent):
    pass

class SMSComponent(BaseComponent):
    pass

if __name__ == "__main__":
    print("Run the solution file to see the working implementation!")
