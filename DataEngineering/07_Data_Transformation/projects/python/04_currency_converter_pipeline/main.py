import pandas as pd

data = {'tx_id': [1, 2], 'amount': [100.0, 50.0], 'currency': ['EUR', 'GBP']}
df = pd.DataFrame(data)

# Mock exchange rates to USD
rates = {'EUR': 1.1, 'GBP': 1.3}

df['usd_amount'] = df.apply(lambda row: row['amount'] * rates.get(row['currency'], 1.0), axis=1)

print("Standardized Currencies to USD:")
print(df)
