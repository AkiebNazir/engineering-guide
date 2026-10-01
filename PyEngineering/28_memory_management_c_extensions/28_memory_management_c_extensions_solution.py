"""
Topic 28: Memory Management & C Extensions

================================================================================
SOLUTION & WALKTHROUGH
================================================================================
"""

import gc
import weakref
import ctypes
import ctypes.util
import sys

# ============================================================================
# 1. Weak References for Caching
# ============================================================================
class HeavyData:
    def __init__(self, id_str: str):
        self.id_str = id_str
        self.data = [0] * 1000000 
        
    def __repr__(self):
        return f"<HeavyData {self.id_str}>"

class ObjectCache:
    def __init__(self):
        # A WeakValueDictionary stores values as weak references.
        # If there are no more strong references to the value anywhere else in the
        # program, the dictionary will automatically remove the entry.
        self._cache = weakref.WeakValueDictionary()

    def get_or_create(self, id_str: str) -> HeavyData:
        if id_str in self._cache:
            print(f"Cache HIT for {id_str}")
            return self._cache[id_str]
            
        print(f"Cache MISS for {id_str}. Creating...")
        obj = HeavyData(id_str)
        self._cache[id_str] = obj
        return obj

    def inspect(self):
        print(f"Items currently in cache: {list(self._cache.keys())}")

# ============================================================================
# 2. C Types (Interfacing with C)
# ============================================================================
def call_c_printf(message: str):
    """Uses ctypes to call the C standard library's printf."""
    # Find the C standard library dynamically based on OS
    if sys.platform == 'win32':
        libc = ctypes.cdll.msvcrt
    else:
        # macOS or Linux
        libc_name = ctypes.util.find_library('c')
        libc = ctypes.CDLL(libc_name)
        
    # Python strings are Unicode, but C printf expects a byte string (char array).
    # We must encode it.
    byte_message = message.encode('utf-8')
    
    # Call the C function!
    libc.printf(b"C-printf output: %s\n", byte_message)

if __name__ == "__main__":
    print("--- Testing Weak Reference Cache ---")
    cache = ObjectCache()
    
    # Create strong references
    obj1 = cache.get_or_create("data-A")
    obj2 = cache.get_or_create("data-B")
    
    cache.inspect() # Should show data-A, data-B
    
    # Hit the cache
    obj1_ref = cache.get_or_create("data-A")
    
    # Now, delete the strong references to obj2
    print("Deleting strong reference to data-B...")
    del obj2
    
    # Force garbage collection (though CPython's refcount usually handles this instantly)
    gc.collect()
    
    # Because obj2 was the only strong reference to the "data-B" HeavyData object,
    # its reference count dropped to 0. It was garbage collected.
    # The WeakValueDictionary detected this and removed it!
    cache.inspect() # Should only show data-A!
    
    print("\n--- Testing ctypes (calling C library) ---")
    call_c_printf("Hello from Python, handled by C!")
