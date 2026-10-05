"""
Topic 26: Metaprogramming & Decorators (Class Decorators, Descriptors, Metaclasses)

================================================================================
SOLUTION & WALKTHROUGH
================================================================================

This file contains the complete, idiomatic solution for the metaprogramming
challenges. You can run this file directly to see it in action.
"""

from typing import Any, Type, Dict, Callable
import functools

# ============================================================================
# 1. Class Decorator: @singleton
# ============================================================================
# A class decorator takes a class as an argument and returns a modified class
# or a wrapper function that intercepts instantiation.
def singleton(cls: Type[Any]) -> Callable[..., Any]:
    """
    Ensures that only a single instance of the decorated class exists.
    """
    # We store the instance in a closure variable.
    _instance = None

    @functools.wraps(cls)
    def wrapper(*args, **kwargs):
        nonlocal _instance
        if _instance is None:
            # If no instance exists, create one and store it.
            _instance = cls(*args, **kwargs)
        # Always return the stored instance.
        return _instance

    return wrapper

@singleton
class DatabaseConnection:
    def __init__(self):
        print("Initializing DatabaseConnection...")
        self.connected = True

# ============================================================================
# 2. Descriptors: ValidatedField
# ============================================================================
# A descriptor is any object that defines __get__, __set__, or __delete__.
# It allows you to customize attribute access at the class level.
class ValidatedField:
    def __init__(self, expected_type: Type, min_value: Any = None):
        self.expected_type = expected_type
        self.min_value = min_value
        self.name = "" # Will be set by __set_name__
        
    def __set_name__(self, owner: Type, name: str):
        # Called automatically when the class is created.
        # Tells the descriptor what variable name it was assigned to.
        self.name = name
        
    def __get__(self, instance: Any, owner: Type) -> Any:
        # If called on the class itself (e.g. UserAccount.age), return the descriptor
        if instance is None:
            return self
        # Otherwise, return the value from the instance's dictionary
        return instance.__dict__.get(self.name)
        
    def __set__(self, instance: Any, value: Any):
        # Enforce type checking
        if not isinstance(value, self.expected_type):
            raise TypeError(f"Expected {self.name} to be {self.expected_type.__name__}, got {type(value).__name__}")
            
        # Enforce min_value if provided
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"Expected {self.name} to be >= {self.min_value}, got {value}")
            
        # Store the value in the instance's dictionary
        instance.__dict__[self.name] = value

class UserAccount:
    # age is managed by the ValidatedField descriptor
    age = ValidatedField(int, min_value=18)
    
    def __init__(self, age: int):
        self.age = age

# ============================================================================
# 3. Metaclasses: RegistryMeta
# ============================================================================
# A metaclass is the "class of a class". By subclassing `type`, we can intercept
# the creation of new classes.
COMPONENT_REGISTRY: Dict[str, Type] = {}

class RegistryMeta(type):
    # __new__ is called before the class is created.
    def __new__(mcs, name, bases, namespace):
        # Create the class normally using type.__new__
        cls = super().__new__(mcs, name, bases, namespace)
        
        # Don't register the base class itself if we don't want to,
        # but for this example, we register everything that uses the metaclass.
        # Alternatively, we could check if name != 'BaseComponent'.
        if name != 'BaseComponent':
            COMPONENT_REGISTRY[name] = cls
            print(f"[Registry] Registered component: {name}")
            
        return cls

# By setting the metaclass here, any subclass will also use RegistryMeta.
class BaseComponent(metaclass=RegistryMeta):
    pass
    
class EmailComponent(BaseComponent):
    pass

class SMSComponent(BaseComponent):
    pass


if __name__ == "__main__":
    print("--- Testing Class Decorator (@singleton) ---")
    db1 = DatabaseConnection() # Prints "Initializing DatabaseConnection..."
    db2 = DatabaseConnection() # Does not print anything
    print(f"db1 is db2? {db1 is db2}") # True
    print()

    print("--- Testing Descriptor (ValidatedField) ---")
    try:
        user = UserAccount(age=25)
        print(f"User created with age {user.age}")
        
        print("Attempting to set age to 15...")
        user.age = 15 # Should raise ValueError
    except Exception as e:
        print(f"Error caught: {e}")
        
    try:
        print("Attempting to set age to 'thirty'...")
        user.age = "thirty" # Should raise TypeError
    except Exception as e:
        print(f"Error caught: {e}")
    print()

    print("--- Testing Metaclass (RegistryMeta) ---")
    print(f"Registered components: {list(COMPONENT_REGISTRY.keys())}")
