package main

import (
	"crypto/md5"
	"encoding/hex"
	"fmt"
	"log"
	"time"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

// hashKey generates an MD5 hash key for Data Vault business keys
func hashKey(val string) string {
	hash := md5.Sum([]byte(val))
	return hex.EncodeToString(hash[:])
}

// ---------------- HUBs ----------------

type HubCustomer struct {
	HkCustomerID        string    `gorm:"primaryKey;type:varchar(32)"`
	CustomerBusinessKey string    `gorm:"not null;unique"`
	LoadDate            time.Time `gorm:"not null"`
	RecordSource        string    `gorm:"not null"`
}

type HubTransaction struct {
	HkTransactionID        string    `gorm:"primaryKey;type:varchar(32)"`
	TransactionBusinessKey string    `gorm:"not null;unique"`
	LoadDate               time.Time `gorm:"not null"`
	RecordSource           string    `gorm:"not null"`
}

// ---------------- LINKs ----------------

type LinkCustomerTransaction struct {
	HkLinkID        string    `gorm:"primaryKey;type:varchar(32)"`
	HkCustomerID    string    `gorm:"not null"`
	HkTransactionID string    `gorm:"not null"`
	LoadDate        time.Time `gorm:"not null"`
	RecordSource    string    `gorm:"not null"`

	Customer    HubCustomer    `gorm:"foreignKey:HkCustomerID"`
	Transaction HubTransaction `gorm:"foreignKey:HkTransactionID"`
}

// -------------- SATELLITEs --------------

type SatCustomerDetails struct {
	HkCustomerID string    `gorm:"primaryKey;type:varchar(32)"` // Composite PK part 1
	LoadDate     time.Time `gorm:"primaryKey"`                  // Composite PK part 2
	FirstName    string    `gorm:"not null"`
	LastName     string    `gorm:"not null"`
	RecordSource string    `gorm:"not null"`

	Customer HubCustomer `gorm:"foreignKey:HkCustomerID"`
}

func main() {
	dsn := "host=localhost user=postgres password=postgres dbname=data_vault port=5432 sslmode=disable"
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	})
	if err != nil {
		log.Printf("Failed to connect to database: %v", err)
		log.Println("Skipping actual execution...")
		return
	}

	// 1. Auto Migrate Data Vault Schema
	err = db.AutoMigrate(
		&HubCustomer{},
		&HubTransaction{},
		&LinkCustomerTransaction{},
		&SatCustomerDetails{},
	)
	if err != nil {
		log.Fatalf("Error creating Data Vault schema: %v", err)
	}
	fmt.Println("Data Vault Schema successfully initialized!")

	// 2. Load Data Vault Entities
	loadDate := time.Now()

	// Insert Hub & Satellite for Customer
	cID := "CUST-1001"
	hkCust := hashKey(cID)

	hubC := HubCustomer{
		HkCustomerID:        hkCust,
		CustomerBusinessKey: cID,
		LoadDate:            loadDate,
		RecordSource:        "CRM",
	}
	satC := SatCustomerDetails{
		HkCustomerID: hkCust,
		LoadDate:     loadDate,
		FirstName:    "Alice",
		LastName:     "Smith",
		RecordSource: "CRM",
	}
	db.Create(&hubC)
	db.Create(&satC)

	// Insert Hub for Transaction
	tID := "TX-9999"
	hkTx := hashKey(tID)

	hubT := HubTransaction{
		HkTransactionID:        hkTx,
		TransactionBusinessKey: tID,
		LoadDate:               loadDate,
		RecordSource:           "BILLING",
	}
	db.Create(&hubT)

	// Insert Link connecting Customer to Transaction
	hkLink := hashKey(hkCust + hkTx)
	link := LinkCustomerTransaction{
		HkLinkID:        hkLink,
		HkCustomerID:    hkCust,
		HkTransactionID: hkTx,
		LoadDate:        loadDate,
		RecordSource:    "BILLING",
	}
	db.Create(&link)
	fmt.Println("Data inserted into Data Vault.")

	// 3. Query the vault (Reconstruct business view)
	type BusinessView struct {
		CustomerKey string
		FirstName   string
		LastName    string
		TxKey       string
	}
	var results []BusinessView

	db.Table("link_customer_transactions").
		Select(`
			hub_customers.customer_business_key as customer_key,
			sat_customer_details.first_name,
			sat_customer_details.last_name,
			hub_transactions.transaction_business_key as tx_key
		`).
		Joins("JOIN hub_customers ON hub_customers.hk_customer_id = link_customer_transactions.hk_customer_id").
		Joins("JOIN hub_transactions ON hub_transactions.hk_transaction_id = link_customer_transactions.hk_transaction_id").
		Joins("JOIN sat_customer_details ON sat_customer_details.hk_customer_id = hub_customers.hk_customer_id").
		Scan(&results)

	fmt.Println("--- Business View ---")
	for _, r := range results {
		fmt.Printf("Customer: %s (%s %s) | Transaction: %s\n", r.CustomerKey, r.FirstName, r.LastName, r.TxKey)
	}
}
