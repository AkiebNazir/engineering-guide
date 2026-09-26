package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/segmentio/kafka-go"
)

var (
	kafkaBroker = "localhost:9092"
	inputTopic  = "clickstream"
)

type ClickEvent struct {
	UserID    string `json:"user_id"`
	PageURL   string `json:"page_url"`
	Action    string `json:"action"`
	EventTime string `json:"event_time"`
}

type WindowAggregator struct {
	mu     sync.Mutex
	counts map[string]int
}

func NewWindowAggregator() *WindowAggregator {
	return &WindowAggregator{
		counts: make(map[string]int),
	}
}

func (w *WindowAggregator) Add(pageURL string) {
	w.mu.Lock()
	defer w.mu.Unlock()
	w.counts[pageURL]++
}

func (w *WindowAggregator) ResetAndReport() {
	w.mu.Lock()
	defer w.mu.Unlock()
	
	if len(w.counts) == 0 {
		return
	}

	log.Println("--- 1 Minute Clickstream Summary ---")
	for page, count := range w.counts {
		log.Printf("Page: %s | Clicks: %d", page, count)
	}
	log.Println("------------------------------------")
	
	// Reset the map for the next window
	w.counts = make(map[string]int)
}

func main() {
	fmt.Println("Starting Clickstream Analyzer...")

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigChan
		log.Println("Shutting down gracefully...")
		cancel()
	}()

	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  []string{kafkaBroker},
		Topic:    inputTopic,
		GroupID:  "clickstream-analyzer-group",
		MinBytes: 10e3,
		MaxBytes: 10e6,
	})
	defer reader.Close()

	aggregator := NewWindowAggregator()

	// Trigger window aggregation every minute
	go func() {
		ticker := time.NewTicker(1 * time.Minute)
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				aggregator.ResetAndReport()
			case <-ctx.Done():
				return
			}
		}
	}()

	log.Printf("Listening for clickstream events on topic '%s'...", inputTopic)

	for {
		m, err := reader.ReadMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				break
			}
			log.Printf("Error reading message: %v", err)
			continue
		}

		var event ClickEvent
		if err := json.Unmarshal(m.Value, &event); err != nil {
			log.Printf("Error unmarshalling event: %v", err)
			continue
		}

		// Increment the page view count
		aggregator.Add(event.PageURL)
	}

	log.Println("Clickstream Analyzer stopped.")
}
