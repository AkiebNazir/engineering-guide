import sqlite3
import hashlib
from datetime import datetime

def hash_key(val):
    return hashlib.md5(str(val).encode('utf-8')).hexdigest()

def main():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create Hubs (Core Business Entities)
    cursor.execute("CREATE TABLE hub_customer (customer_hk TEXT PRIMARY KEY, customer_id TEXT, load_date TEXT, record_source TEXT)")
    cursor.execute("CREATE TABLE hub_order (order_hk TEXT PRIMARY KEY, order_id TEXT, load_date TEXT, record_source TEXT)")
    
    # Create Links (Relationships between Hubs)
    cursor.execute("CREATE TABLE link_customer_order (link_hk TEXT PRIMARY KEY, customer_hk TEXT, order_hk TEXT, load_date TEXT, record_source TEXT)")
    
    # Create Satellites (Context/Attributes for Hubs/Links)
    cursor.execute("CREATE TABLE sat_customer_details (customer_hk TEXT, name TEXT, email TEXT, load_date TEXT, record_source TEXT, PRIMARY KEY (customer_hk, load_date))")

    # Generate Data
    cust_id = 'C123'
    c_hk = hash_key(cust_id)
    ld = datetime.now().isoformat()
    src = 'CRM_SYS'
    
    # Insert Hub & Sat for Customer
    cursor.execute("INSERT INTO hub_customer VALUES (?, ?, ?, ?)", (c_hk, cust_id, ld, src))
    cursor.execute("INSERT INTO sat_customer_details VALUES (?, ?, ?, ?, ?)", (c_hk, 'Alice Smith', 'alice@example.com', ld, src))

    # Insert Hub for Order
    ord_id = 'O999'
    o_hk = hash_key(ord_id)
    cursor.execute("INSERT INTO hub_order VALUES (?, ?, ?, ?)", (o_hk, ord_id, ld, 'ORDER_SYS'))

    # Insert Link connecting Customer and Order
    l_hk = hash_key(c_hk + o_hk)
    cursor.execute("INSERT INTO link_customer_order VALUES (?, ?, ?, ?, ?)", (l_hk, c_hk, o_hk, ld, 'ORDER_SYS'))

    conn.commit()
    
    print("Data Vault Architecture Initialized & Data Inserted.")
    print("Querying Data Vault to reconstruct business view:")
    
    query = """
    SELECT h.customer_id, s.name, o.order_id 
    FROM link_customer_order l 
    JOIN hub_customer h ON l.customer_hk = h.customer_hk 
    JOIN hub_order o ON l.order_hk = o.order_hk 
    JOIN sat_customer_details s ON h.customer_hk = s.customer_hk
    """
    for row in cursor.execute(query):
        print(row)

if __name__ == '__main__':
    main()
