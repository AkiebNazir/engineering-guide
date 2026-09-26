package main

import (
	"fmt"
	"log"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

// DimCountry is the top level of the normalized location hierarchy
type DimCountry struct {
	CountryID   uint   `gorm:"primaryKey;autoIncrement"`
	CountryName string `gorm:"not null"`
}

// DimState belongs to DimCountry
type DimState struct {
	StateID   uint   `gorm:"primaryKey;autoIncrement"`
	StateName string `gorm:"not null"`
	CountryID uint   `gorm:"not null"`
	Country   DimCountry `gorm:"foreignKey:CountryID"`
}

// DimCity belongs to DimState
type DimCity struct {
	CityID   uint   `gorm:"primaryKey;autoIncrement"`
	CityName string `gorm:"not null"`
	StateID  uint   `gorm:"not null"`
	State    DimState `gorm:"foreignKey:StateID"`
}

// DimStore belongs to DimCity
type DimStore struct {
	StoreID   uint   `gorm:"primaryKey;autoIncrement"`
	StoreName string `gorm:"not null"`
	CityID    uint   `gorm:"not null"`
	City      DimCity `gorm:"foreignKey:CityID"`
}

// FactSales links to the most granular dimension
type FactSales struct {
	SaleID  uint    `gorm:"primaryKey;autoIncrement"`
	StoreID uint    `gorm:"not null"`
	Amount  float64 `gorm:"not null"`
	Store   DimStore `gorm:"foreignKey:StoreID"`
}

func main() {
	// Standard connection to a relational database for schema management.
	dsn := "host=localhost user=postgres password=postgres dbname=data_warehouse port=5432 sslmode=disable"
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	})
	if err != nil {
		log.Printf("Failed to connect to database: %v", err)
		log.Println("Skipping actual execution...")
		return
	}

	// 1. Auto Migrate Snowflake Schema (creates tables with foreign keys)
	err = db.AutoMigrate(&DimCountry{}, &DimState{}, &DimCity{}, &DimStore{}, &FactSales{})
	if err != nil {
		log.Fatalf("Error creating Snowflake schema: %v", err)
	}
	fmt.Println("Snowflake Schema successfully created/migrated!")

	// 2. Insert Normalized Data
	country := DimCountry{CountryName: "USA"}
	db.Create(&country)

	state := DimState{StateName: "New York", CountryID: country.CountryID}
	db.Create(&state)

	city := DimCity{CityName: "NYC", StateID: state.StateID}
	db.Create(&city)

	store := DimStore{StoreName: "NYC Flagship", CityID: city.CityID}
	db.Create(&store)

	sale := FactSales{StoreID: store.StoreID, Amount: 500.0}
	db.Create(&sale)
	fmt.Println("Snowflake data inserted.")

	// 3. Querying across the snowflake relationships
	type SnowflakeResult struct {
		SaleID      uint
		StoreName   string
		CityName    string
		StateName   string
		CountryName string
		Amount      float64
	}

	var results []SnowflakeResult
	db.Table("fact_sales").
		Select(`
			fact_sales.sale_id, 
			dim_stores.store_name, 
			dim_cities.city_name, 
			dim_states.state_name, 
			dim_countries.country_name, 
			fact_sales.amount
		`).
		Joins("JOIN dim_stores ON dim_stores.store_id = fact_sales.store_id").
		Joins("JOIN dim_cities ON dim_cities.city_id = dim_stores.city_id").
		Joins("JOIN dim_states ON dim_states.state_id = dim_cities.state_id").
		Joins("JOIN dim_countries ON dim_countries.country_id = dim_states.country_id").
		Scan(&results)

	fmt.Println("--- Snowflake Query Results ---")
	for _, r := range results {
		fmt.Printf("Sale: %d | Store: %s | Location: %s, %s, %s | Amount: $%.2f\n", 
			r.SaleID, r.StoreName, r.CityName, r.StateName, r.CountryName, r.Amount)
	}
}
