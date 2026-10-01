# Pandas & Polars Mastery: The Engines of Data Manipulation

## 1. The Core Concept (What and Why)

**What are they?** 
- **Pandas** is the absolute industry standard for tabular data manipulation in Python. If data is in a spreadsheet or an SQL table, Pandas is how Python reads, cleans, and engineers it.
- **Polars** is the modern, blazing-fast successor to Pandas. It is written in Rust, utilizes multi-threading, and uses Lazy Evaluation to process massive datasets that would normally crash Pandas.

**Why do they exist?**
NumPy (from Guide 01) is amazing for pure numbers, but it has no concept of "Column Names", "Dates", or "Missing Values". 
Pandas/Polars wrap NumPy arrays with metadata (column names, indexes) and provide high-level SQL-like APIs for joining, grouping, and filtering data.

In AI, 80% of your time is spent cleaning data and engineering features before it ever touches a Neural Network. If you cannot manipulate DataFrames fluently, you cannot build AI.

---

## 2. Setup & Installation

You need both libraries. We also install `pyarrow` to handle Parquet files (the industry standard file format for ML datasets).

```bash
pip install pandas polars pyarrow
```

```python
import pandas as pd
import polars as pl

print(f"Pandas version: {pd.__version__}")
print(f"Polars version: {pl.__version__}")
```

---

## 3. The "Hello World": Pandas vs Polars

Let's load a dataset, filter for users over 30, and calculate their average salary.

**The Pandas Way:**
```python
# 1. Load Data
df_pd = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 35, 45],
    "salary": [50000, 70000, 90000]
})

# 2. Filter & Aggregate
adults_pd = df_pd[df_pd["age"] > 30]
avg_salary_pd = adults_pd["salary"].mean()
print(avg_salary_pd) # 80000.0
```

**The Polars Way:**
```python
# 1. Load Data
df_pl = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 35, 45],
    "salary": [50000, 70000, 90000]
})

# 2. Filter & Aggregate (Notice the Expression API)
avg_salary_pl = (
    df_pl
    .filter(pl.col("age") > 30)
    .select(pl.col("salary").mean())
).item()
print(avg_salary_pl) # 80000.0
```

---

## 4. Deep Dive: Pandas Mechanics

### A. Series vs DataFrame
- **Series:** A single column of data. It is a 1D NumPy array with an index attached.
- **DataFrame:** A 2D table. It is a dictionary of Series objects sharing the same index.

### B. Indexing & Selecting Data (`.loc` vs `.iloc`)
This is the most common point of confusion in Pandas.
- `.iloc[]` (Integer Location): Selects by mathematical position (like a normal Python list).
- `.loc[]` (Label Location): Selects by the string names of the index/columns.

```python
import pandas as pd

df = pd.DataFrame({
    "price": [10, 20, 30],
    "sales": [100, 200, 300]
}, index=["item_A", "item_B", "item_C"])

# Grab the first row mathematically (Returns item_A)
print(df.iloc[0]) 

# Grab the "item_B" row and specifically the "price" column
print(df.loc["item_B", "price"]) # 20
```

### C. Dealing with Missing Data (NaN)
In the real world, data is messy. 
```python
# Drop any row that contains a missing value
clean_df = df.dropna()

# Fill missing values in the 'price' column with the average price
mean_price = df['price'].mean()
df['price'] = df['price'].fillna(mean_price)
```

### D. Grouping and Aggregating
Just like SQL `GROUP BY`.
```python
# Group by 'department', and find the max salary and mean age for each department
summary = df.groupby("department").agg({
    "salary": "max",
    "age": "mean"
})
```

---

## 5. Pro Concept: Pandas Memory Optimization (Interview Critical)

*Interview Question:* "You are trying to load a 10GB CSV into Pandas, but your machine only has 8GB of RAM. It crashes. How do you fix this?"

*Answer:* Pandas is horribly memory-inefficient by default. It defaults all numbers to `int64` or `float64` (8 bytes), and all text to `object` (which stores massive string pointers).

**The Optimization Strategy:**
1. **Downcast Numbers:** If a column contains human ages (0-100), you don't need `int64` (which goes up to 9 quintillion). You can use `int8` (which goes up to 127 and uses 1 byte). You just saved 87% of memory.
2. **Use Categoricals:** If you have a column with 10 Million rows representing "City", but there are only 5 unique cities, converting it from `object` to `category` maps the strings to tiny integers under the hood, saving massive memory.
3. **Use Parquet, not CSV:** Parquet files store data by column, include schema metadata, and compress heavily.

```python
# The Memory Optimization Script
def optimize_memory(df):
    for col in df.columns:
        col_type = df[col].dtype
        
        # Optimize Floats
        if col_type == 'float64':
            df[col] = pd.to_numeric(df[col], downcast='float') # Becomes float32
            
        # Optimize Integers
        elif col_type == 'int64':
            df[col] = pd.to_numeric(df[col], downcast='integer')
            
        # Optimize Strings to Categories (If unique values < 50% of total rows)
        elif col_type == 'object':
            num_unique = len(df[col].unique())
            num_total = len(df[col])
            if num_unique / num_total < 0.5:
                df[col] = df[col].astype('category')
                
    return df
```

---

## 6. The Polars Revolution (Why Pandas is dying)

Pandas was written in 2008. It is single-threaded. If you have a 16-core CPU, Pandas will only use 1 core and the other 15 will sit at 0% usage.
**Polars** is written in Rust. It utilizes Apache Arrow memory formats. It is multithreaded by default.

### The "Lazy Evaluation" Superpower
In Pandas, if you load a 10GB dataset and then instantly filter for `age > 50`, Pandas physically loads all 10GB into RAM, *then* throws away 8GB of it. This causes crashes.

Polars uses **Lazy Evaluation** (Query Optimization).
You use `pl.scan_csv()` instead of `pl.read_csv()`. Polars does not load the data. It builds an Execution Graph. When you finally call `.collect()`, Polars optimizes the query. It realizes you only want `age > 50`, so it streams the file from disk, instantly skipping the young users, and only loads the filtered 2GB into RAM.

```python
import polars as pl

# LAZY API: Builds the query, but does NOT execute it yet.
# Notice we use scan_parquet(), not read_parquet()
query = (
    pl.scan_parquet("massive_100GB_dataset.parquet")
    .filter(pl.col("country") == "USA")
    .groupby("state")
    .agg(pl.col("revenue").sum())
)

# Polars optimizer looks at the query, realizes it doesn't need to load 
# the other 50 columns in the dataset, and multithreads the aggregation.
# .collect() actually executes the optimized graph.
final_df = query.collect() 
```

### The Polars Expression API
Pandas code often requires creating intermediate variables. Polars uses a fluid Expression API that chains cleanly.

```python
# Polars Contexts: select(), with_columns(), filter(), groupby()
df = df.with_columns(
    # Create a new column mathematically
    (pl.col("price") * pl.col("quantity")).alias("total_sales"),
    
    # Conditional logic (Like np.where)
    pl.when(pl.col("age") >= 18).then(pl.lit("Adult")).otherwise(pl.lit("Minor")).alias("age_group")
)
```

---

## 7. Common Pitfalls & Debugging in Production

### ⚠️ Pitfall 1: The `SettingWithCopyWarning` (Pandas)
This is the most famous error in Python data science.
```python
# BAD CODE:
# You filter a dataframe, then try to modify a column on the filtered version.
adults = df[df['age'] >= 18]
adults['status'] = 'Eligible' # Raises SettingWithCopyWarning!
```
Pandas doesn't know if `adults` is a View of `df` or a physical Copy of `df`. It warns you that your assignment might not be modifying the original data like you think it is.
**The Fix:** Always explicitly use `.copy()` when carving out a subset of data you intend to modify.
```python
adults = df[df['age'] >= 18].copy()
adults['status'] = 'Eligible' # Safe!
```

### ⚠️ Pitfall 2: Using `.apply()` instead of Vectorization (Pandas)
Many Python developers treat DataFrames like lists and use `.apply()` to run a custom function on every row.
**NEVER do this in production.** `.apply()` is essentially a hidden Python `for` loop. It completely bypasses the optimized C code and will take 100x longer than necessary.

```python
# BAD (Extremely Slow)
df['price_with_tax'] = df.apply(lambda row: row['price'] * 1.20, axis=1)

# GOOD (Blazing Fast Vectorization)
df['price_with_tax'] = df['price'] * 1.20
```
If you must apply complex logic, use `np.where()` or Polars `pl.when().then()`.

### ⚠️ Pitfall 3: Iterating with `iterrows()`
If you ever write `for index, row in df.iterrows():`, you have failed the interview. This is the slowest possible way to process data in Python. Always find a vectorized equivalent or use `.apply()` as an absolute last resort.

---

## 8. MAANG Interview Preparation (Coding Scenarios)

### Scenario 1: Feature Engineering (Window Functions)
*Prompt:* You have a dataframe of daily stock prices. Create a new column that calculates the 7-day rolling average of the price, and another column calculating the daily percentage change.

**Pandas Solution:**
```python
# Sort by date first!
df = df.sort_values("date")

# 7-day rolling average
df["7d_moving_avg"] = df["price"].rolling(window=7).mean()

# Percentage change from the previous day
df["daily_pct_change"] = df["price"].pct_change() * 100
```

**Polars Solution:**
```python
df = df.sort("date").with_columns([
    pl.col("price").rolling_mean(window_size=7).alias("7d_moving_avg"),
    ((pl.col("price") - pl.col("price").shift(1)) / pl.col("price").shift(1) * 100).alias("daily_pct_change")
])
```

### Scenario 2: Data Leakage Prevention (Train/Test Splits)
*Prompt:* You are preparing data for Machine Learning. You need to fill missing values (Imputation) in the `age` column with the mean age. What is the mathematically correct way to do this?

*Answer:* If you fill the missing values by calculating the mean of the *entire* dataset, and then split your data into Train and Test sets, you have committed **Data Leakage**. Your training data now secretly contains mathematical information from your test data!

*The Correct Approach:*
1. Split the data into Train and Test *first*.
2. Calculate the mean age of the Train set *only*.
3. Use that Train mean to fill the missing values in *both* the Train set and the Test set.

```python
from sklearn.model_selection import train_test_split

train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# Calculate mean strictly on the training data
train_mean_age = train_df['age'].mean()

# Apply to both
train_df['age'] = train_df['age'].fillna(train_mean_age)
test_df['age'] = test_df['age'].fillna(train_mean_age)
```
