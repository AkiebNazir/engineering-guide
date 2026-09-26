package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/robfig/cron/v3"
)

func runDataPipeline(pipelineName string) {
	log.Printf("Executing pipeline: %s", pipelineName)
	// In a real scenario, this would trigger actual data extraction and loading
}

func main() {
	log.Println("Starting cron job scheduler...")

	// Create a new cron instance
	// We use the standard cron syntax
	c := cron.New()

	// Add a job using standard cron syntax
	// "* * * * *" runs at the beginning of every minute
	_, err := c.AddFunc("* * * * *", func() {
		runDataPipeline("Hourly_Sales_Aggregation")
	})
	if err != nil {
		log.Fatalf("Failed to schedule job: %v", err)
	}

	// Start the cron scheduler in its own goroutine
	c.Start()

	log.Println("Scheduler is running. Press Ctrl+C to exit.")

	// Set up a channel to listen for interrupt signals to gracefully shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Block until a signal is received
	<-sigChan

	log.Println("Shutting down scheduler...")
	c.Stop()
}
