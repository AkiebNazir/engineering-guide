import os

base_dir = "/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/02_Data_Modeling/projects/golang"

files = {
    "01_star_schema_generator/main.go": """package main

import (
	"database/sql"
	"fmt"
	"log"

	_ "github.com/mattn/go-sqlite3"
)

func main() {
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// DDL for Star Schema
	ddl := `
	CREATE TABLE dim_product (
		product_id INTEGER PRIMARY KEY,
		name TEXT,
		category TEXT
	);
	CREATE TABLE dim_time (
		time_id INTEGER PRIMARY KEY,
		full_date TEXT,
		month INTEGER,
		year INTEGER
	);
	CREATE TABLE fact_sales (
		sale_id INTEGER PRIMARY KEY,
		product_id INTEGER,
		time_id INTEGER,
		amount REAL,
		FOREIGN KEY(product_id) REFERENCES dim_product(product_id),
		FOREIGN KEY(time_id) REFERENCES dim_time(time_id)
	);`

	_, err = db.Exec(ddl)
	if err != nil {
		log.Fatal("Error creating tables:", err)
	}

	fmt.Println("Star Schema successfully created!")
}
""",
    "02_snowflake_schema_builder/main.go": """package main

import (
	"database/sql"
	"fmt"
	"log"

	_ "github.com/mattn/go-sqlite3"
)

func main() {
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// DDL for Snowflake Schema
	ddl := `
	CREATE TABLE dim_country (
		country_id INTEGER PRIMARY KEY,
		country_name TEXT
	);
	CREATE TABLE dim_city (
		city_id INTEGER PRIMARY KEY,
		city_name TEXT,
		country_id INTEGER,
		FOREIGN KEY(country_id) REFERENCES dim_country(country_id)
	);
	CREATE TABLE dim_store (
		store_id INTEGER PRIMARY KEY,
		store_name TEXT,
		city_id INTEGER,
		FOREIGN KEY(city_id) REFERENCES dim_city(city_id)
	);
	CREATE TABLE fact_sales (
		sale_id INTEGER PRIMARY KEY,
		store_id INTEGER,
		amount REAL,
		FOREIGN KEY(store_id) REFERENCES dim_store(store_id)
	);`

	_, err = db.Exec(ddl)
	if err != nil {
		log.Fatal("Error creating Snowflake schema:", err)
	}
	fmt.Println("Snowflake Schema successfully created!")
}
""",
    "03_data_vault_hub_link_sat/main.go": """package main

import (
	"database/sql"
	"fmt"
	"log"

	_ "github.com/mattn/go-sqlite3"
)

func main() {
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// DDL for Data Vault
	ddl := `
	-- HUB
	CREATE TABLE hub_customer (
		hk_customer_id TEXT PRIMARY KEY,
		customer_business_key TEXT,
		load_date DATETIME,
		record_source TEXT
	);
	
	-- LINK
	CREATE TABLE link_transaction (
		hk_transaction_id TEXT PRIMARY KEY,
		hk_customer_id TEXT,
		transaction_business_key TEXT,
		load_date DATETIME,
		record_source TEXT,
		FOREIGN KEY(hk_customer_id) REFERENCES hub_customer(hk_customer_id)
	);
	
	-- SATELLITE
	CREATE TABLE sat_customer_details (
		hk_customer_id TEXT,
		load_date DATETIME,
		first_name TEXT,
		last_name TEXT,
		record_source TEXT,
		PRIMARY KEY (hk_customer_id, load_date),
		FOREIGN KEY(hk_customer_id) REFERENCES hub_customer(hk_customer_id)
	);`

	_, err = db.Exec(ddl)
	if err != nil {
		log.Fatal("Error creating Data Vault:", err)
	}
	fmt.Println("Data Vault successfully initialized!")
}
""",
    "04_scd_type_2_implementer/main.go": """package main

import (
	"database/sql"
	"fmt"
	"log"

	_ "github.com/mattn/go-sqlite3"
)

func main() {
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// Setup SCD Type 2 Table
	_, err = db.Exec(`CREATE TABLE dim_customer (
		customer_sk INTEGER PRIMARY KEY AUTOINCREMENT,
		customer_id INTEGER,
		city TEXT,
		start_date TEXT,
		end_date TEXT,
		is_current BOOLEAN
	)`)
	if err != nil {
		log.Fatal(err)
	}

	// Insert initial record
	db.Exec("INSERT INTO dim_customer (customer_id, city, start_date, end_date, is_current) VALUES (1, 'New York', '2023-01-01', '9999-12-31', 1)")

	// Process Update (Customer moved to LA on 2023-10-01)
	// 1. Expire old record
	db.Exec("UPDATE dim_customer SET end_date = '2023-09-30', is_current = 0 WHERE customer_id = 1 AND is_current = 1")
	// 2. Insert new record
	db.Exec("INSERT INTO dim_customer (customer_id, city, start_date, end_date, is_current) VALUES (1, 'Los Angeles', '2023-10-01', '9999-12-31', 1)")

	rows, _ := db.Query("SELECT customer_sk, customer_id, city, is_current FROM dim_customer")
	defer rows.Close()
	fmt.Println("SCD Type 2 Records:")
	for rows.Next() {
		var sk, id, current int
		var city string
		rows.Scan(&sk, &id, &city, &current)
		fmt.Printf("SK: %d | ID: %d | City: %s | Current: %v\n", sk, id, city, current == 1)
	}
}
""",
    "05_denormalizer_engine/main.go": """package main

import (
	"fmt"
)

// Represents normalized data
type User struct {
	ID   int
	Name string
}
type Order struct {
	ID     int
	UserID int
	Amount float64
}

// Represents the denormalized wide table record
type DenormalizedRecord struct {
	OrderID   int
	UserName  string
	OrderAmt  float64
}

func main() {
	users := map[int]User{
		1: {ID: 1, Name: "Alice"},
		2: {ID: 2, Name: "Bob"},
	}

	orders := []Order{
		{ID: 101, UserID: 1, Amount: 50.0},
		{ID: 102, UserID: 2, Amount: 200.0},
		{ID: 103, UserID: 1, Amount: 15.5},
	}

	var wideTable []DenormalizedRecord

	// Denormalize (flatten) the data through a programmatic JOIN
	for _, order := range orders {
		if user, exists := users[order.UserID]; exists {
			wideTable = append(wideTable, DenormalizedRecord{
				OrderID:  order.ID,
				UserName: user.Name,
				OrderAmt: order.Amount,
			})
		}
	}

	fmt.Println("Denormalized Analytical Data:")
	for _, rec := range wideTable {
		fmt.Printf("Order: %d | User: %s | Amount: $%.2f\n", rec.OrderID, rec.UserName, rec.OrderAmt)
	}
}
"""
}

for path, code in files.items():
    full_path = os.path.join(base_dir, path)
    with open(full_path, "w") as f:
        f.write(code)

print("Go code generated!")
