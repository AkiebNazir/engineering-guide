package main

import (
	"fmt"
	"log"
	"time"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

// DimCustomer represents an SCD Type 2 dimension table
type DimCustomer struct {
	CustomerSK int       `gorm:"primaryKey;autoIncrement;column:customer_sk"`
	CustomerID int       `gorm:"not null;column:customer_id"`
	City       string    `gorm:"not null"`
	StartDate  time.Time `gorm:"not null"`
	EndDate    time.Time `gorm:"not null"`
	IsCurrent  bool      `gorm:"not null;default:true"`
}

// processSCD2Update handles inserting or updating an SCD Type 2 record transactionally.
func processSCD2Update(db *gorm.DB, customerID int, newCity string, effectiveDate time.Time) error {
	return db.Transaction(func(tx *gorm.DB) error {
		// 1. Find the current active record
		var currentRecord DimCustomer
		err := tx.Where("customer_id = ? AND is_current = ?", customerID, true).First(&currentRecord).Error

		if err == nil { // Record exists, we need to expire it
			currentRecord.EndDate = effectiveDate
			currentRecord.IsCurrent = false
			if err := tx.Save(&currentRecord).Error; err != nil {
				return err
			}
		} else if err != gorm.ErrRecordNotFound {
			return err
		}

		// 2. Insert the new active record
		maxDate := time.Date(9999, 12, 31, 0, 0, 0, 0, time.UTC)
		newRecord := DimCustomer{
			CustomerID: customerID,
			City:       newCity,
			StartDate:  effectiveDate,
			EndDate:    maxDate,
			IsCurrent:  true,
		}
		if err := tx.Create(&newRecord).Error; err != nil {
			return err
		}

		return nil
	})
}

func main() {
	dsn := "host=localhost user=postgres password=postgres dbname=data_warehouse port=5432 sslmode=disable"
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	})
	if err != nil {
		log.Printf("Failed to connect to database: %v", err)
		log.Println("Skipping actual execution...")
		return
	}

	// 1. Setup SCD Type 2 Table
	err = db.AutoMigrate(&DimCustomer{})
	if err != nil {
		log.Fatalf("Migration failed: %v", err)
	}
	fmt.Println("SCD Type 2 Table successfully migrated!")

	// 2. Insert initial record (Customer lives in New York)
	t1 := time.Date(2023, 1, 1, 0, 0, 0, 0, time.UTC)
	if err := processSCD2Update(db, 1, "New York", t1); err != nil {
		log.Fatalf("Failed to process initial insert: %v", err)
	}

	// 3. Process Update (Customer moves to Los Angeles)
	t2 := time.Date(2023, 10, 1, 0, 0, 0, 0, time.UTC)
	if err := processSCD2Update(db, 1, "Los Angeles", t2); err != nil {
		log.Fatalf("Failed to process SCD2 update: %v", err)
	}

	// 4. View history
	var records []DimCustomer
	db.Order("customer_sk ASC").Find(&records)

	fmt.Println("--- SCD Type 2 Customer History ---")
	for _, r := range records {
		fmt.Printf("SK: %d | ID: %d | City: %-12s | Current: %-5v | %s to %s\n",
			r.CustomerSK, r.CustomerID, r.City, r.IsCurrent,
			r.StartDate.Format("2006-01-02"), r.EndDate.Format("2006-01-02"))
	}
}
