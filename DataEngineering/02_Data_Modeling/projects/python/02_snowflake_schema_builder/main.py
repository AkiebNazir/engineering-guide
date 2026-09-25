import sqlite3

def main():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Snowflake Dimensions (Normalized Location data)
    cursor.execute("CREATE TABLE dim_country (country_id INTEGER PRIMARY KEY, country_name TEXT)")
    cursor.execute("CREATE TABLE dim_state (state_id INTEGER PRIMARY KEY, state_name TEXT, country_id INTEGER)")
    cursor.execute("CREATE TABLE dim_city (city_id INTEGER PRIMARY KEY, city_name TEXT, state_id INTEGER)")
    
    # Store dimension links to city (most granular location)
    cursor.execute("CREATE TABLE dim_store (store_id INTEGER PRIMARY KEY, store_name TEXT, city_id INTEGER)")

    # Fact Table
    cursor.execute("CREATE TABLE fact_sales (sale_id INTEGER PRIMARY KEY, store_id INTEGER, amount REAL)")

    # Insert Normalized Data
    cursor.execute("INSERT INTO dim_country VALUES (1, 'USA')")
    cursor.execute("INSERT INTO dim_state VALUES (1, 'New York', 1)")
    cursor.execute("INSERT INTO dim_city VALUES (1, 'NYC', 1)")
    cursor.execute("INSERT INTO dim_store VALUES (1, 'NYC Flagship', 1)")
    
    # Insert Fact Data
    cursor.execute("INSERT INTO fact_sales VALUES (1, 1, 500.0)")

    print("Snowflake Schema Data Generated.")
    print("Querying across the snowflake relationships:")
    
    query = """
    SELECT f.sale_id, s.store_name, c.city_name, st.state_name, co.country_name, f.amount
    FROM fact_sales f
    JOIN dim_store s ON f.store_id = s.store_id
    JOIN dim_city c ON s.city_id = c.city_id
    JOIN dim_state st ON c.state_id = st.state_id
    JOIN dim_country co ON st.country_id = co.country_id
    """
    for row in cursor.execute(query):
        print(row)

if __name__ == '__main__':
    main()
