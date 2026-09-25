package main

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
		fmt.Printf("SK: %d | ID: %d | City: %s | Current: %v
", sk, id, city, current == 1)
	}
}
