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
