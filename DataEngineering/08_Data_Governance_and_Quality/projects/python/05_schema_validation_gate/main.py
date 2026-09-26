import json
from pydantic import BaseModel, ValidationError, Field, EmailStr
from datetime import datetime
from typing import Optional

# Define the expected schema for incoming data using Pydantic.
# This acts as a strict schema validation gate for data entering the pipeline.
class UserEvent(BaseModel):
    event_id: str = Field(..., min_length=10, description="Unique identifier for the event")
    user_id: int = Field(..., gt=0)
    email: EmailStr
    event_timestamp: datetime
    is_active: bool
    platform: Optional[str] = "web"

def process_event(raw_payload: str):
    """
    Validates a raw JSON string against the UserEvent schema.
    If valid, proceeds with downstream processing.
    If invalid, routes to a Dead Letter Queue (DLQ).
    """
    print(f"\nProcessing payload:\n{raw_payload}")
    try:
        # Parse and validate the schema
        event_dict = json.loads(raw_payload)
        validated_event = UserEvent(**event_dict)
        
        print("✅ Schema Validation Passed!")
        # Accessing typed and validated fields
        print(f"Proceeding to ingest event: {validated_event.event_id} from user {validated_event.user_id}")
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON format. Routing to DLQ...")
    except ValidationError as e:
        print("❌ Schema Validation Failed. Routing to DLQ...")
        print(f"Validation Errors:\n{e.json()}")

def main():
    # Good Payload: Matches the schema perfectly
    good_payload = json.dumps({
        "event_id": "evt_123456789",
        "user_id": 42,
        "email": "alice@company.com",
        "event_timestamp": "2023-10-25T14:30:00Z",
        "is_active": True
    })

    # Bad Payload 1: Missing required field (event_timestamp), invalid email, user_id is negative
    bad_payload = json.dumps({
        "event_id": "evt_987", # Too short
        "user_id": -5,
        "email": "not-an-email",
        "is_active": "yes" # Should be boolean, but Pydantic might try to coerce. Let's see. 'yes' can't be coerced to bool easily.
    })

    process_event(good_payload)
    process_event(bad_payload)

if __name__ == "__main__":
    main()
