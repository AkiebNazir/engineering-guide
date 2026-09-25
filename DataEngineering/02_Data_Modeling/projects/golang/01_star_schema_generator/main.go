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
