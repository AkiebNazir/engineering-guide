"""
Topic 32: Pydantic v2 Deep Dive

================================================================================
SOLUTION & WALKTHROUGH
================================================================================
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
    username: str
    password: str
    password_confirm: str

    # field_validator operates on a single field before or after the core validation.
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        # Pydantic v2 passes the value 'v' directly.
        v = v.lower()
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v

    # model_validator(mode="after") operates on the entire model AFTER all fields
    # have been individually parsed and validated. 'self' is the model instance.
    @model_validator(mode='after')
    def check_passwords_match(self) -> 'UserRegistration':
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self

    # field_serializer changes how a field is outputted when calling model_dump()
    # or model_dump_json(). Useful for masking secrets or formatting dates.
    @field_serializer('password', 'password_confirm')
    def serialize_password(self, password: str, _info: Any) -> str:
        return "***"

if __name__ == "__main__":
    print("--- Testing Successful Validation ---")
    user = UserRegistration(
        username="SeniorEngineer123", # Will be lowercased
        password="MySecretPassword",
        password_confirm="MySecretPassword"
    )
    print(f"Validated Model:\n{user}")
    
    print("\n--- Testing Custom Serialization ---")
    # Notice how the passwords are masked in the output dump!
    print(user.model_dump_json(indent=2))
    
    print("\n--- Testing Validation Errors ---")
    try:
        # Passwords don't match
        UserRegistration(
            username="bad_user!", # Not alphanumeric
            password="pwd1",
            password_confirm="pwd2"
        )
    except ValidationError as e:
        print(f"Validation caught multiple errors:\n{e.json()}")
