package main

import (
	"fmt"
	"strconv"
	"strings"
	"time"
)

func main() {
	dateStr := "2023-01-01T12:00:00Z"
	priceStr := "$1,200.50"

	// Parse date
	cleanDate, _ := time.Parse(time.RFC3339, dateStr)

	// Clean and parse price
	cleanPriceStr := strings.ReplaceAll(priceStr, "$", "")
	cleanPriceStr = strings.ReplaceAll(cleanPriceStr, ",", "")
	cleanPrice, _ := strconv.ParseFloat(cleanPriceStr, 64)

	fmt.Printf("Parsed Date: %v (Type: %T)
", cleanDate, cleanDate)
	fmt.Printf("Parsed Price: %f (Type: %T)
", cleanPrice, cleanPrice)
}
