import pandas as pd




df = pd.DataFrame({
    "name": ["Shahida", "Akieb", "Aasif", "Jamid"],
    "age": [33, 30, 27, 25],
    "education": ["12th", "Master's", "Bachler's", "BA"]
})

print(df["age"] > 30)
print(df[df["age"] > 30])