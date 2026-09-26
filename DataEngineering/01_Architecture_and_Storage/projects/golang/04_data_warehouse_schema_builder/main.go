package main

import (
	"fmt"
	"log"
	"time"

	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

// ==========================================
// Schema Definitions (Star Schema)
// ==========================================

// DimDate represents the Date dimension table.
type DimDate struct {
	DateID   uint      `gorm:"primaryKey;autoIncrement"`
	FullDate time.Time `gorm:"uniqueIndex;not null"`
	Year     int       `gorm:"not null"`
	Month    int       `gorm:"not null"`
	Day      int       `gorm:"not null"`
}

// DimProduct represents the Product dimension table.
type DimProduct struct {
	ProductID   uint    `gorm:"primaryKey"`
	ProductName string  `gorm:"size:100;not null"`
	Category    string  `gorm:"size:50;not null"`
	Price       float64 `gorm:"type:decimal(10,2);not null"`
}

// FactSales represents the central fact table.
type FactSales struct {
	SaleID      uint       `gorm:"primaryKey;autoIncrement"`
	DateID      uint       `gorm:"not null"`
	ProductID   uint       `gorm:"not null"`
	Quantity    int        `gorm:"not null"`
	TotalAmount float64    `gorm:"type:decimal(12,2);not null"`
	
	// Foreign Key constraints
	Date    DimDate    `gorm:"foreignKey:DateID"`
	Product DimProduct `gorm:"foreignKey:ProductID"`
}

// ==========================================
// Operations
// ==========================================

func buildAndPopulateWarehouse(db *gorm.DB) error {
	log.Println("Migrating database schema...")
	// AutoMigrate creates tables, missing foreign keys, constraints, columns and indexes.
	err := db.AutoMigrate(&DimDate{}, &DimProduct{}, &FactSales{})
	if err != nil {
		return fmt.Errorf("failed to migrate schema: %w", err)
	}

	log.Println("Inserting sample data into Data Warehouse...")
	
	// Use a transaction for data integrity
	return db.Transaction(func(tx *gorm.DB) error {
		dt := time.Date(2023, 10, 1, 0, 0, 0, 0, time.UTC)
		dDate := DimDate{
			FullDate: dt,
			Year:     dt.Year(),
			Month:    int(dt.Month()),
			Day:      dt.Day(),
		}
		if err := tx.Create(&dDate).Error; err != nil {
			return err
		}

		dProd := DimProduct{
			ProductID:   101,
			ProductName: "Enterprise Database Server",
			Category:    "Hardware",
			Price:       15000.00,
		}
		if err := tx.Create(&dProd).Error; err != nil {
			return err
		}

		fSales := FactSales{
			DateID:      dDate.DateID,
			ProductID:   dProd.ProductID,
			Quantity:    3,
			TotalAmount: dProd.Price * 3,
		}
		if err := tx.Create(&fSales).Error; err != nil {
			return err
		}

		return nil // Commit transaction
	})
}

func analyzeSales(db *gorm.DB) {
	log.Println("Running analytical query on Star Schema...")

	type SalesReport struct {
		FullDate    time.Time
		ProductName string
		Quantity    int
		TotalAmount float64
	}

	var results []SalesReport

	// Perform the joins for our Star Schema query
	err := db.Model(&FactSales{}).
		Select("dim_dates.full_date, dim_products.product_name, fact_sales.quantity, fact_sales.total_amount").
		Joins("JOIN dim_dates ON fact_sales.date_id = dim_dates.date_id").
		Joins("JOIN dim_products ON fact_sales.product_id = dim_products.product_id").
		Scan(&results).Error

	if err != nil {
		log.Fatalf("Failed to execute analytical query: %v", err)
	}

	fmt.Printf("\n--- Sales Analysis Report ---\n")
	fmt.Printf("%-15s | %-30s | %-5s | %s\n", "Date", "Product Name", "Qty", "Total Amount")
	fmt.Println("---------------------------------------------------------------------------")
	for _, row := range results {
		fmt.Printf("%-15s | %-30s | %-5d | $%.2f\n", 
			row.FullDate.Format("2006-01-02"), 
			row.ProductName, 
			row.Quantity, 
			row.TotalAmount)
	}
	fmt.Println("---------------------------------------------------------------------------")
}

func main() {
	// In production, configure connecting to a real data warehouse like PostgreSQL/Redshift/etc.
	// dsn := "host=localhost user=gorm password=gorm dbname=warehouse port=5432 sslmode=disable"
	// db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	
	// For simulation, using SQLite in-memory database
	db, err := gorm.Open(sqlite.Open("file::memory:?cache=shared"), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Warn), // Suppress noisy SQL logs for clear output
	})
	if err != nil {
		log.Fatalf("Failed to connect database: %v", err)
	}

	if err := buildAndPopulateWarehouse(db); err != nil {
		log.Fatalf("Failed to build and populate warehouse: %v", err)
	}

	analyzeSales(db)
}
