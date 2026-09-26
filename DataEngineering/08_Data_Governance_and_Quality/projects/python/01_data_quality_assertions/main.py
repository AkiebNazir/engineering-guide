import pandas as pd
import pandera as pa
from pandera.errors import SchemaErrors

def main():
    # Define a real-world schema for a user dimension table using Pandera
    schema = pa.DataFrameSchema(
        columns={
            "id": pa.Column(int, checks=pa.Check.gt(0), nullable=False, unique=True),
            "age": pa.Column(int, checks=[pa.Check.ge(0), pa.Check.le(120)], nullable=False),
            "email": pa.Column(str, checks=pa.Check.str_matches(r"^[\w\.-]+@[\w\.-]+\.\w+$"), nullable=True),
            "signup_date": pa.Column(pd.DatetimeTZDtype(tz="UTC")),
        },
        strict=True, # Fail if extra columns are present
    )

    # Sample data containing some valid and some invalid records
    data = pd.DataFrame({
        "id": [1, 2, 2, 4], # Duplicate ID (2)
        "age": [25, -5, 30, 45], # Negative age (-5)
        "email": ["alice@example.com", "bob@example", "charlie@example.com", "dave@example.com"], # Invalid email for Bob
        "signup_date": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]).dt.tz_localize("UTC"),
    })

    print("Running Data Quality Assertions with Pandera...\n")
    try:
        # Attempt to validate the dataframe
        validated_df = schema.validate(data, lazy=True) # lazy=True collects all errors
        print("All data quality checks passed!")
        print(validated_df.head())
    except SchemaErrors as err:
        print("Data Quality Checks Failed!")
        print(f"Number of schema errors found: {len(err.failure_cases)}")
        print("\nFailure Cases Details:")
        print(err.failure_cases[['column', 'check', 'failure_case', 'index']])

if __name__ == "__main__":
    main()
