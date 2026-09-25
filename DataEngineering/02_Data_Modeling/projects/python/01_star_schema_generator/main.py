import sqlite3
from datetime import datetime
import random

def main():
    # Using an in-memory SQLite database for demonstration
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create Dimension: Product
    cursor.execute('''
    CREATE TABLE dim_product (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT,
        category TEXT
    )''')
    
    # Create Dimension: Store
    cursor.execute('''
    CREATE TABLE dim_store (
        store_id INTEGER PRIMARY KEY,
        store_name TEXT,
        city TEXT
    )''')

    # Create Fact: Sales
    cursor.execute('''
    CREATE TABLE fact_sales (
        sale_id INTEGER PRIMARY KEY,
        product_id INTEGER,
        store_id INTEGER,
        quantity INTEGER,
        amount REAL,
        FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
        FOREIGN KEY (store_id) REFERENCES dim_store(store_id)
    )''')

    # Insert Sample Data into Dimensions
    cursor.execute("INSERT INTO dim_product VALUES (1, 'Laptop', 'Electronics'), (2, 'Desk', 'Furniture')")
    cursor.execute("INSERT INTO dim_store VALUES (1, 'Downtown Tech', 'New York'), (2, 'Suburban Goods', 'Boston')")
    
    # Generate Synthetic Data for Fact Table
    for i in range(1, 11):
        prod_id = random.choice([1, 2])
        store_id = random.choice([1, 2])
        qty = random.randint(1, 5)
        amt = qty * (1000.0 if prod_id == 1 else 150.0)
        cursor.execute("INSERT INTO fact_sales (product_id, store_id, quantity, amount) VALUES (?, ?, ?, ?)", 
                       (prod_id, store_id, qty, amt))
        
    conn.commit()

    print("Star Schema Data Generated successfully.")
    print("Sample query joining Fact and Dimensions:")
    
    query = """
    SELECT s.sale_id, p.product_name, st.store_name, s.quantity, s.amount 
    FROM fact_sales s 
    JOIN dim_product p ON s.product_id = p.product_id 
    JOIN dim_store st ON s.store_id = st.store_id 
    LIMIT 5
    """
    for row in cursor.execute(query):
        print(row)

if __name__ == '__main__':
    main()
