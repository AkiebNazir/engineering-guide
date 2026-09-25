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
