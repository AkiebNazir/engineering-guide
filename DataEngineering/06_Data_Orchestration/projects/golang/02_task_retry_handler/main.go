package main

import (
	"fmt"
	"math/rand"
	"time"
)

func flakyTask() error {
	if rand.Float64() < 0.7 {
		return fmt.Errorf("random failure occurred")
	}
	fmt.Println("Task succeeded!")
	return nil
}

func retryWithBackoff(task func() error, retries int, backoffBase time.Duration) error {
	for attempt := 0; attempt <= retries; attempt++ {
		err := task()
		if err == nil {
			return nil
		}

		if attempt == retries {
			fmt.Printf("Attempt %d failed. Max retries reached.\n", attempt+1)
			return err
		}

		// Exponential backoff with some jitter
		sleepTime := backoffBase * time.Duration(1<<attempt)
		jitter := time.Duration(rand.Int63n(int64(time.Second)))
		sleepTime += jitter

		fmt.Printf("Attempt %d failed: %v. Retrying in %v...\n", attempt+1, err, sleepTime)
		time.Sleep(sleepTime)
	}
	return fmt.Errorf("max retries exceeded")
}

func main() {
	rand.Seed(time.Now().UnixNano())

	err := retryWithBackoff(flakyTask, 3, 1*time.Second)
	if err != nil {
		fmt.Printf("Task ultimately failed: %v\n", err)
	}
}
