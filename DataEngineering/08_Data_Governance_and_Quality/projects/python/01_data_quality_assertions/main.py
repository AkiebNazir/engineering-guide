import pandas as pd
import numpy as np

def run_data_quality_checks(df):
    errors = []
    if df['id'].isnull().any():
        errors.append("Assertion Failed: 'id' contains nulls.")
    if not df['id'].is_unique:
        errors.append("Assertion Failed: 'id' is not unique.")
    if (df['age'] < 0).any():
        errors.append("Assertion Failed: 'age' contains negative values.")
    return errors

df = pd.DataFrame({'id': [1, 2, 2], 'age': [25, -5, 30]})
print("Running Data Quality Assertions...")
errors = run_data_quality_checks(df)
if errors:
    for e in errors:
        print(e)
else:
    print("All checks passed!")
