package main

import (
	"fmt"
	"time"
)

func dataPull() {
	fmt.Printf("[%s] Pulling data from source...\n", time.Now().Format("2006-01-02 15:04:05"))
	time.Sleep(1 * time.Second)
	fmt.Printf("[%s] Data pull complete.\n", time.Now().Format("2006-01-02 15:04:05"))
}

func runScheduler(interval time.Duration, duration time.Duration) {
	fmt.Printf("Starting cron scheduler (interval: %v, duration: %v)\n", interval, duration)
	
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	
	timer := time.NewTimer(duration)
	defer timer.Stop()

	// Run initially
	go dataPull()

	for {
		select {
		case <-ticker.C:
			go dataPull()
		case <-timer.C:
			fmt.Println("Scheduler finished.")
			// Small delay to allow the last routine to finish if it just started
			time.Sleep(2 * time.Second)
			return
		}
	}
}

func main() {
	runScheduler(3*time.Second, 10*time.Second)
}
