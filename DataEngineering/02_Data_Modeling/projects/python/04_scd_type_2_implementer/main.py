import sqlite3

def main():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create SCD Type 2 Dimension Table
    cursor.execute('''CREATE TABLE dim_customer (
        surrogate_key INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT,
        name TEXT,
        city TEXT,
        start_date TEXT,
        end_date TEXT,
        is_current INTEGER
    )''')

    # 1. Initial State: Customer lives in Chicago
    t1 = '2023-01-01'
    cursor.execute("INSERT INTO dim_customer (customer_id, name, city, start_date, end_date, is_current) VALUES (?, ?, ?, ?, ?, ?)", 
                   ('C1', 'Bob Jones', 'Chicago', t1, '9999-12-31', 1))
    
    print("--- Initial State ---")
    for row in cursor.execute("SELECT * FROM dim_customer"):
        print(row)
    
    # 2. Update (SCD Type 2 Event): Customer moves to Seattle
    t2 = '2023-06-15'
    
    # Step A: Close the active record
    cursor.execute("UPDATE dim_customer SET end_date = ?, is_current = 0 WHERE customer_id = ? AND is_current = 1", (t2, 'C1'))
    
    # Step B: Insert the new active record
    cursor.execute("INSERT INTO dim_customer (customer_id, name, city, start_date, end_date, is_current) VALUES (?, ?, ?, ?, ?, ?)", 
                   ('C1', 'Bob Jones', 'Seattle', t2, '9999-12-31', 1))
    
    print("\n--- After SCD Type 2 Update (Moved to Seattle) ---")
    for row in cursor.execute("SELECT * FROM dim_customer"):
        print(row)

if __name__ == '__main__':
    main()
