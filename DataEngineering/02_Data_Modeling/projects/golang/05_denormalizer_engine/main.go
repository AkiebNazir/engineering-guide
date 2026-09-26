package main

import (
	"fmt"
	"log"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

// In a real-world Go data pipeline, you often rely on the RDBMS
// or an OLAP engine to handle denormalization at scale.
// Using an ORM like GORM allows you to construct the wide (denormalized) 
// structs easily from normalized tables.

// Normalized: Dimension Product
type DimProduct struct {
	ProductID   int    `gorm:"primaryKey"`
	ProductName string `gorm:"not null"`
	Category    string
}

// Normalized: Dimension Store
type DimStore struct {
	StoreID   int    `gorm:"primaryKey"`
	StoreName string `gorm:"not null"`
	City      string
}

// Normalized: Fact Sales
type FactSales struct {
	SaleID    int `gorm:"primaryKey"`
	ProductID int
	StoreID   int
	Amount    float64
}

// Denormalized Wide Struct (Target for Analytics/ML/API)
type DenormalizedSales struct {
	SaleID      int     `gorm:"column:sale_id"`
	ProductName string  `gorm:"column:product_name"`
	Category    string  `gorm:"column:category"`
	StoreName   string  `gorm:"column:store_name"`
	City        string  `gorm:"column:city"`
	Amount      float64 `gorm:"column:amount"`
}

func main() {
	// Connect to the data warehouse/database
	dsn := "host=localhost user=postgres password=postgres dbname=data_warehouse port=5432 sslmode=disable"
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	})
	if err != nil {
		log.Printf("Failed to connect to database: %v", err)
		log.Println("Skipping actual execution...")
		return
	}

	// For demonstration, we assume tables are already populated.
	// AutoMigrate is just to ensure schema presence in this example.
	db.AutoMigrate(&DimProduct{}, &DimStore{}, &FactSales{})

	// Example: Denormalizer Engine Query
	// We use LEFT JOINs to flatten the normalized schema into our wide struct.
	// This approach offloads the join heavy-lifting to the DB engine.
	var wideTable []DenormalizedSales

	err = db.Table("fact_sales").
		Select(`
			fact_sales.sale_id,
			dim_products.product_name,
			dim_products.category,
			dim_stores.store_name,
			dim_stores.city,
			fact_sales.amount
		`).
		Joins("LEFT JOIN dim_products ON dim_products.product_id = fact_sales.product_id").
		Joins("LEFT JOIN dim_stores ON dim_stores.store_id = fact_sales.store_id").
		Scan(&wideTable).Error

	if err != nil {
		log.Fatalf("Failed to execute denormalization query: %v", err)
	}

	fmt.Println("--- Denormalized Wide Table (Ready for Analytics) ---")
	for _, rec := range wideTable {
		fmt.Printf("Sale: %d | Product: %s (%s) | Store: %s (%s) | Amount: $%.2f\n",
			rec.SaleID, rec.ProductName, rec.Category, rec.StoreName, rec.City, rec.Amount)
	}

	// In a complete ETL pipeline, this wideTable slice would then be written
	// to a fast NoSQL store (e.g., Redis, DynamoDB) for serving, or written 
	// as Parquet/CSV to S3.
}
