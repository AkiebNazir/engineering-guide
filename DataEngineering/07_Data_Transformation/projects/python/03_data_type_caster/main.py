import pandas as pd

# Mock dirty data
data = {
    'date_str': ['2023-01-01T12:00:00Z', '2023-02-01T14:30:00Z'],
    'price_str': ['$1,200.50', '$45.00']
}
df = pd.DataFrame(data)

# Cast types
df['date_clean'] = pd.to_datetime(df['date_str'])
df['price_clean'] = df['price_str'].replace({'\$': '', ',': ''}, regex=True).astype(float)

print("Cleaned Types:")
print(df.dtypes)
print(df)
