package main

import (
	"encoding/csv"
	"fmt"
	"os"
	"strconv"
)

func main() {
	// Generate mock CSV data
	file, err := os.Create("sales.csv")
	if err != nil {
		panic(err)
	}
	defer file.Close()
	file.WriteString("date,product,amount\n")
	file.WriteString("2023-01-01,Laptop,1200.50\n")
	file.WriteString("2023-01-01,Mouse,25.00\n")
	file.WriteString("2023-01-02,Laptop,1200.50\n")
	file.WriteString("2023-01-02,Mouse,25.00\n")
	file.WriteString("2023-01-01,Laptop,1000.00\n")

	// Read and aggregate
	f, err := os.Open("sales.csv")
	if err != nil {
		panic(err)
	}
	defer f.Close()

	reader := csv.NewReader(f)
	records, err := reader.ReadAll()
	if err != nil {
		panic(err)
	}

	// Key: date_product, Value: total amount
	aggregated := make(map[string]float64)

	for i, record := range records {
		if i == 0 {
			continue // skip header
		}
		date := record[0]
		product := record[1]
		amount, _ := strconv.ParseFloat(record[2], 64)
		key := fmt.Sprintf("%s_%s", date, product)
		aggregated[key] += amount
	}

	fmt.Println("Aggregated Sales:")
	for key, amount := range aggregated {
		fmt.Printf("%s: %.2f\n", key, amount)
	}
}
