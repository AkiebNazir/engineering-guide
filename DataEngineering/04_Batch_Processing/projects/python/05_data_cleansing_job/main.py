import pandas as pd
import numpy as np

def generate_dirty_data(filename="dirty_data.csv"):
    data = {
        "id": [1, 2, 3, 4, 5],
        "name": [" Alice ", "Bob", "Charlie", None, "Eve"],
        "price": ["10.5", "invalid", "20", np.nan, "15.0"],
        "date": ["2023-01-01", "01/02/2023", "bad_date", "2023-01-04", "2023-01-05"]
    }
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

def clean_data(filename="dirty_data.csv"):
    df = pd.read_csv(filename)
    print("Original Data:")
    print(df)
    
    # Clean names
    df['name'] = df['name'].str.strip()
    df['name'] = df['name'].fillna("Unknown")
    
    # Clean price
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['price'] = df['price'].fillna(df['price'].mean())
    
    # Clean date
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Drop rows with invalid dates
    df = df.dropna(subset=['date'])
    
    print("\nCleaned Data:")
    print(df)
    df.to_csv("cleaned_data.csv", index=False)

if __name__ == "__main__":
    generate_dirty_data()
    clean_data()
