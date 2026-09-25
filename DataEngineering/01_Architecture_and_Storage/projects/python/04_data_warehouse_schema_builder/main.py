import sqlite3

def build_data_warehouse():
    # Connect to in-memory SQLite database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    print("Building Data Warehouse Schema...")
    
    # Dimension Table: Date
    cursor.execute('''
    CREATE TABLE dim_date (
        date_id INTEGER PRIMARY KEY,
        full_date TEXT,
        year INTEGER,
        month INTEGER,
        day INTEGER
    )
    ''')
    
    # Dimension Table: Product
    cursor.execute('''
    CREATE TABLE dim_product (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT,
        category TEXT,
        price REAL
    )
    ''')
    
    # Fact Table: Sales
    cursor.execute('''
    CREATE TABLE fact_sales (
        sale_id INTEGER PRIMARY KEY,
        date_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        total_amount REAL,
        FOREIGN KEY(date_id) REFERENCES dim_date(date_id),
        FOREIGN KEY(product_id) REFERENCES dim_product(product_id)
    )
    ''')
    
    print("Tables created successfully.")
    
    # Insert Sample Data
    print("Inserting sample data...")
    cursor.execute("INSERT INTO dim_date VALUES (1, '2023-10-01', 2023, 10, 1)")
    cursor.execute("INSERT INTO dim_product VALUES (101, 'Laptop', 'Electronics', 1200.00)")
    cursor.execute("INSERT INTO fact_sales VALUES (1001, 1, 101, 2, 2400.00)")
    conn.commit()
    
    # Query the Star Schema
    print("\nQuerying Data (Star Schema Join):")
    cursor.execute('''
    SELECT d.full_date, p.product_name, f.quantity, f.total_amount
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    JOIN dim_product p ON f.product_id = p.product_id
    ''')
    
    rows = cursor.fetchall()
    for row in rows:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    build_data_warehouse()
