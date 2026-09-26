package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"os"
	"strconv"
	"strings"
	"time"
)

type Transaction struct {
	Date  time.Time
	Price float64
}

// CleanPrice string removes formatting and converts to float64.
func CleanPrice(priceStr string) (float64, error) {
	clean := strings.ReplaceAll(priceStr, "$", "")
	clean = strings.ReplaceAll(clean, ",", "")
	return strconv.ParseFloat(strings.TrimSpace(clean), 64)
}

// ProcessRecords simulates reading from a CSV stream, casting and validating data.
func ProcessRecords(reader io.Reader) ([]Transaction, error) {
	csvReader := csv.NewReader(reader)
	if _, err := csvReader.Read(); err != nil {
		return nil, fmt.Errorf("failed to read header: %w", err)
	}

	var results []Transaction

	for {
		record, err := csvReader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("Error reading CSV row: %v", err)
			continue
		}

		if len(record) < 2 {
			log.Printf("Invalid record length: %v", record)
			continue
		}

		dateStr := record[0]
		priceStr := record[1]

		parsedDate, err := time.Parse(time.RFC3339, dateStr)
		if err != nil {
			log.Printf("Failed to parse date %q: %v", dateStr, err)
			continue
		}

		parsedPrice, err := CleanPrice(priceStr)
		if err != nil {
			log.Printf("Failed to parse price %q: %v", priceStr, err)
			continue
		}

		results = append(results, Transaction{
			Date:  parsedDate,
			Price: parsedPrice,
		})
	}

	return results, nil
}

func main() {
	csvData := `date_str,price_str
2023-01-01T12:00:00Z,$1,200.50
2023-02-01T14:30:00Z,$45.00
invalid_date,$100.00
2023-03-01T00:00:00Z,not_a_number`

	r := strings.NewReader(csvData)

	transactions, err := ProcessRecords(r)
	if err != nil {
		log.Fatalf("Data pipeline failed: %v", err)
	}

	fmt.Println("Successfully casted and validated transactions:")
	for _, tx := range transactions {
		fmt.Printf("Date: %s, Price: %.2f\n", tx.Date.Format(time.RFC3339), tx.Price)
	}
}
