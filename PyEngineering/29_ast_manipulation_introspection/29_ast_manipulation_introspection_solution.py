"""
Topic 29: AST Manipulation & Introspection

================================================================================
SOLUTION & WALKTHROUGH
================================================================================
"""

import inspect
import ast
from typing import Callable, Any

# ============================================================================
# 1. Introspection (inspect module)
# ============================================================================
def analyze_function_signature(func: Callable[..., Any]):
    print(f"Analyzing signature for: {func.__name__}")
    
    # Get the signature object
    sig = inspect.signature(func)
    
    for name, param in sig.parameters.items():
        # Check if an annotation exists
        if param.annotation != inspect.Parameter.empty:
            # param.annotation is the actual type object (e.g., <class 'str'>)
            # If it's a string (from from __future__ import annotations), it's just a string
            type_name = getattr(param.annotation, '__name__', str(param.annotation))
            print(f"  - Parameter '{name}' expects type: {type_name}")
        else:
            print(f"  - Parameter '{name}' has NO type hint.")
            
    if sig.return_annotation != inspect.Signature.empty:
         ret_name = getattr(sig.return_annotation, '__name__', str(sig.return_annotation))
         print(f"  -> Returns: {ret_name}")

def sample_api_handler(request_id: str, payload: dict, timeout: int = 30) -> bool:
    return True

# ============================================================================
# 2. AST Manipulation
# ============================================================================
class InfiniteLoopDetector(ast.NodeVisitor):
    def visit_While(self, node: ast.While):
        # We found a While loop. Let's check its contents.
        has_break = False
        
        # ast.walk recursively yields all child nodes
        for child in ast.walk(node):
            if isinstance(child, ast.Break):
                has_break = True
                break
                
        if not has_break:
            print(f"WARNING: Potential infinite loop detected at line {node.lineno}")
            
        # Continue visiting the rest of the AST in case there are nested loops
        self.generic_visit(node)

def lint_code(source_code: str):
    # 1. Parse the string into an Abstract Syntax Tree
    tree = ast.parse(source_code)
    
    # 2. Walk the tree using our custom visitor
    detector = InfiniteLoopDetector()
    detector.visit(tree)

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
    print("--- Introspection ---")
    analyze_function_signature(sample_api_handler)
    
    print("\n--- AST Linter ---")
    lint_code(sample_code)
