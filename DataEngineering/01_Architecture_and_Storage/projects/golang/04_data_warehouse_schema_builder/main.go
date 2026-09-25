package main

import (
	"database/sql"
	"fmt"
	"os"

	_ "github.com/mattn/go-sqlite3"
)

func main() {
	dbFile := "warehouse.db"
	os.Remove(dbFile) // Start fresh

	db, err := sql.Open("sqlite3", dbFile)
	if err != nil {
		panic(err)
	}
	defer db.Close()

	// Star schema: 1 Fact, 2 Dimensions
	ddls := []string{
		`CREATE TABLE dim_users (
			user_id INTEGER PRIMARY KEY, 
			name TEXT, 
			region TEXT
		);`,
		`CREATE TABLE dim_products (
			product_id INTEGER PRIMARY KEY, 
			name TEXT, 
			category TEXT
		);`,
		`CREATE TABLE fact_sales (
			sale_id INTEGER PRIMARY KEY, 
			user_id INTEGER, 
			product_id INTEGER, 
			amount REAL, 
			FOREIGN KEY(user_id) REFERENCES dim_users(user_id), 
			FOREIGN KEY(product_id) REFERENCES dim_products(product_id)
		);`,
	}

	for _, ddl := range ddls {
		_, err := db.Exec(ddl)
		if err != nil {
			panic(err)
		}
	}
	fmt.Println("Star schema created successfully in SQLite database:", dbFile)
}
