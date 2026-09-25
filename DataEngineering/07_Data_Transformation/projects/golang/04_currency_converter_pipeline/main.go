package main

import "fmt"

type Transaction struct {
	ID       int
	Amount   float64
	Currency string
}

func main() {
	txs := []Transaction{
		{1, 100.0, "EUR"},
		{2, 50.0, "GBP"},
	}

	rates := map[string]float64{"EUR": 1.1, "GBP": 1.3}

	for _, tx := range txs {
		usd := tx.Amount * rates[tx.Currency]
		fmt.Printf("TX %d: %.2f %s = $%.2f USD
", tx.ID, tx.Amount, tx.Currency, usd)
	}
}
