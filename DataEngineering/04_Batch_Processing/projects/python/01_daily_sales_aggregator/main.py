import pandas as pd
import numpy as np

def generate_data(filename="sales.csv", rows=1000):
    dates = pd.date_range("2023-01-01", periods=10).tolist() * (rows // 10)
    products = ["Laptop", "Mouse", "Keyboard", "Monitor"]
    data = {
        "date": dates,
        "product": np.random.choice(products, rows),
        "amount": np.random.uniform(10.0, 1000.0, rows),
    }
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

def aggregate_sales(filename="sales.csv"):
    df = pd.read_csv(filename)
    df['date'] = pd.to_datetime(df['date'])
    aggregated = df.groupby(['date', 'product'])['amount'].sum().reset_index()
    print(aggregated.head(10))
    aggregated.to_csv("aggregated_sales.csv", index=False)
    
if __name__ == "__main__":
    generate_data()
    aggregate_sales()
