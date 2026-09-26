package main

import (
	"fmt"
	"log"
	"math/rand"
	"time"

	"github.com/avast/retry-go"
)

// flakyDataPull simulates pulling data from an unstable API.
func flakyDataPull() (string, error) {
	log.Println("Attempting to pull data from upstream API...")
	if rand.Float32() < 0.7 {
		return "", fmt.Errorf("upstream API returned 503 Service Unavailable")
	}
	return "data_payload", nil
}

func main() {
	rand.Seed(time.Now().UnixNano())

	var result string

	// Using avast/retry-go to handle retries with exponential backoff
	err := retry.Do(
		func() error {
			var err error
			result, err = flakyDataPull()
			return err
		},
		retry.Attempts(5),
		retry.Delay(1*time.Second),
		retry.MaxDelay(10*time.Second),
		retry.DelayType(retry.BackOffDelay),
		retry.OnRetry(func(n uint, err error) {
			log.Printf("Retry %d: %v\n", n, err, n)
		}),
	)

	if err != nil {
		log.Fatalf("Task ultimately failed after retries: %v\n", err)
	}

	log.Printf("Task succeeded! Final result: %s\n", result)
}
