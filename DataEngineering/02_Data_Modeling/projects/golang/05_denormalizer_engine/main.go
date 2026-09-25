package main

import (
	"fmt"
)

// Represents normalized data
type User struct {
	ID   int
	Name string
}
type Order struct {
	ID     int
	UserID int
	Amount float64
}

// Represents the denormalized wide table record
type DenormalizedRecord struct {
	OrderID   int
	UserName  string
	OrderAmt  float64
}

func main() {
	users := map[int]User{
		1: {ID: 1, Name: "Alice"},
		2: {ID: 2, Name: "Bob"},
	}

	orders := []Order{
		{ID: 101, UserID: 1, Amount: 50.0},
		{ID: 102, UserID: 2, Amount: 200.0},
		{ID: 103, UserID: 1, Amount: 15.5},
	}

	var wideTable []DenormalizedRecord

	// Denormalize (flatten) the data through a programmatic JOIN
	for _, order := range orders {
		if user, exists := users[order.UserID]; exists {
			wideTable = append(wideTable, DenormalizedRecord{
				OrderID:  order.ID,
				UserName: user.Name,
				OrderAmt: order.Amount,
			})
		}
	}

	fmt.Println("Denormalized Analytical Data:")
	for _, rec := range wideTable {
		fmt.Printf("Order: %d | User: %s | Amount: $%.2f
", rec.OrderID, rec.UserName, rec.OrderAmt)
	}
}
