"""
Topic 28: Memory Management & C Extensions

================================================================================
EXPLANATION
================================================================================

Python manages memory primarily through Reference Counting, backed up by a
Generational Garbage Collector (to handle cyclic references).

Sometimes, memory leaks happen because we accidentally keep references to large
objects. The `weakref` module allows us to reference objects without increasing
their reference count.

Other times, Python is just too slow or uses too much memory for a specific
operation, and we need to interface with C code using `ctypes` or CFFI.

---
DIAGRAM: Reference Counting vs Weak References
---
```mermaid
graph TD
    subgraph Strong References
        A[Variable 'my_data'] -- "Refcount +1" --> B(Large Dictionary)
        C[List 'cache'] -- "Refcount +1" --> B
    end

    subgraph Weak Reference
        D[WeakValueDictionary] -. "No Refcount change" .-> B
    end
    
    B -- "If Refcount == 0" --> E[Memory Freed!]
```

================================================================================
YOUR TASK
================================================================================
1. Implement a caching mechanism using `weakref.WeakValueDictionary`. Prove
   that when the last strong reference to a cached object is deleted, it is
   automatically removed from the cache.
2. (Mock) Interfacing with C: We will use the built-in `ctypes` module to load
   the standard C library (libc) and call `printf`.
"""

import gc
import weakref
import ctypes
import sys

# ============================================================================
# 1. Weak References for Caching
# ============================================================================
class HeavyData:
    def __init__(self, id_str: str):
        self.id_str = id_str
        # Simulating heavy memory usage
        self.data = [0] * 1000000 
        
    def __repr__(self):
        return f"<HeavyData {self.id_str}>"

class ObjectCache:
    def __init__(self):
        """
        TODO: Initialize self._cache as a WeakValueDictionary.
        """
        pass

    def get_or_create(self, id_str: str) -> HeavyData:
        """
        TODO: Check if id_str is in self._cache.
        If it is, return it.
        If not, create a new HeavyData(id_str), store it in self._cache, and return it.
        """
        pass

# ============================================================================
# 2. C Types (Interfacing with C)
# ============================================================================
def call_c_printf(message: str):
    """
    TODO: Use ctypes to load the C standard library and call printf.
    Note: On Windows, use ctypes.cdll.msvcrt. On macOS/Linux, use ctypes.CDLL("libc.dylib") or find_library.
    """
    pass

if __name__ == "__main__":
    print("Run the solution file to see the working implementation!")
