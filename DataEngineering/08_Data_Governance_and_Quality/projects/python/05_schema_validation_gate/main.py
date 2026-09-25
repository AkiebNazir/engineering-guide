def validate_schema(row, expected_schema):
    for col, expected_type in expected_schema.items():
        if col not in row:
            return False, f"Missing column: {col}"
        if not isinstance(row[col], expected_type):
            return False, f"Type mismatch for {col}: expected {expected_type}, got {type(row[col])}"
    return True, "Valid"

schema = {"id": int, "name": str, "is_active": bool}
good_row = {"id": 1, "name": "Alice", "is_active": True}
bad_row = {"id": "two", "name": "Bob", "is_active": "yes"}

print("Good Row:", validate_schema(good_row, schema))
print("Bad Row:", validate_schema(bad_row, schema))
