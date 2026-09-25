import pandas as pd
import json

nested_json = {
    "user_id": 1,
    "profile": {"name": "Alice", "age": 30},
    "location": {"city": "NYC", "zip": "10001"}
}

# Use pandas json_normalize to flatten deeply nested structures
df = pd.json_normalize(nested_json)
print("Flattened JSON to tabular format:")
print(df.to_csv(index=False))
