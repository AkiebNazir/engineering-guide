"""
Topic 32: Pydantic v2 Deep Dive

================================================================================
EXPLANATION
================================================================================

Pydantic is the most widely used data validation library in modern Python
(powering FastAPI, OpenAI SDKs, etc.).

In Pydantic v2 (which is written in Rust), performance is incredible, but the
API for advanced validation has changed. A senior engineer knows how to use
`@field_validator`, `@model_validator`, custom serializers, and strict vs lax mode.

---
DIAGRAM: Pydantic Validation Lifecycle
---
```mermaid
graph TD
    A[Raw Input Dict] --> B{Before Validators}
    B -->|Clean input| C[Type Coercion & Core Validation]
    C --> D{After Validators}
    D -->|Cross-field checks| E[Valid Pydantic Model]
    C -.->|Fails| F[ValidationError]
```

================================================================================
YOUR TASK
================================================================================
1. Create a `User` model using Pydantic.
2. Add a `@field_validator` that ensures the `username` is alphanumeric and lowercase.
3. Add a `@model_validator` (mode="after") that ensures `password` and `password_confirm` match.
4. Add a custom `@field_serializer` that masks the password with '***' when the model is dumped to JSON.
"""

from typing import Any
try:
    from pydantic import BaseModel, field_validator, model_validator, field_serializer, ValidationError
except ImportError:
    print("Please install pydantic: pip install pydantic")
    import sys
    sys.exit(1)

# ============================================================================
# Pydantic v2 Deep Dive
# ============================================================================

class UserRegistration(BaseModel):
    # TODO: Define fields: username (str), password (str), password_confirm (str)
    
    # TODO: Add a field_validator for 'username'.
    # Convert it to lowercase. If it is not alphanumeric, raise a ValueError.
    
    # TODO: Add a model_validator (mode="after") that checks if password == password_confirm.
    # If they don't match, raise a ValueError.
    
    # TODO: Add a field_serializer for 'password'.
    # Whenever the model is serialized (e.g. model_dump()), the password should output as "***".
    pass

if __name__ == "__main__":
    print("Run the solution file to see the working implementation!")
