package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"
)

type Transaction struct {
	ID       int     `json:"id"`
	Amount   float64 `json:"amount"`
	Currency string  `json:"currency"`
}

type ConvertedTransaction struct {
	Transaction
	USDAmount float64 `json:"usd_amount"`
}

type ExchangeRateClient struct {
	APIKey string
	Client *http.Client
}

func NewExchangeRateClient(apiKey string) *ExchangeRateClient {
	return &ExchangeRateClient{
		APIKey: apiKey,
		Client: &http.Client{Timeout: 10 * time.Second},
	}
}

func (c *ExchangeRateClient) FetchRates(ctx context.Context, baseCurrency string) (map[string]float64, error) {
	if c.APIKey == "demo_key" || c.APIKey == "" {
		log.Println("Using mock exchange rates due to missing/demo API key")
		return map[string]float64{"EUR": 0.9, "GBP": 0.75, "USD": 1.0}, nil
	}

	url := fmt.Sprintf("https://v6.exchangerate-api.com/v6/%s/latest/%s", c.APIKey, baseCurrency)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.Client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var result struct {
		ConversionRates map[string]float64 `json:"conversion_rates"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return result.ConversionRates, nil
}

func main() {
	apiKey := os.Getenv("EXCHANGE_RATE_API_KEY")
	client := NewExchangeRateClient(apiKey)

	rates, err := client.FetchRates(context.Background(), "USD")
	if err != nil {
		log.Fatalf("Failed to fetch rates: %v", err)
	}

	txs := []Transaction{
		{ID: 1, Amount: 100.0, Currency: "EUR"},
		{ID: 2, Amount: 50.0, Currency: "GBP"},
		{ID: 3, Amount: 150.0, Currency: "USD"},
	}

	var processed []ConvertedTransaction
	for _, tx := range txs {
		rate, ok := rates[tx.Currency]
		if !ok || rate == 0 {
			log.Printf("No rate found for currency %s, skipping", tx.Currency)
			continue
		}

		usdAmount := tx.Amount / rate

		processed = append(processed, ConvertedTransaction{
			Transaction: tx,
			USDAmount:   usdAmount,
		})
	}

	out, _ := json.MarshalIndent(processed, "", "  ")
	fmt.Println("Processed Transactions:")
	fmt.Println(string(out))
}
