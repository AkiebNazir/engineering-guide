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
	inputTopic  = "sensor_data"
)

type SensorEvent struct {
	SensorID  string  `json:"sensor_id"`
	Value     float64 `json:"value"`
	Timestamp int64   `json:"timestamp"` // Unix timestamp in seconds
}

// Bucket represents a 1-minute slice of data
type Bucket struct {
	StartTime int64
	Sums      map[string]float64
}

type SlidingWindow struct {
	mu          sync.Mutex
	buckets     []*Bucket
	windowSize  int // in minutes
}

func NewSlidingWindow(sizeInMinutes int) *SlidingWindow {
	return &SlidingWindow{
		buckets:    make([]*Bucket, 0),
		windowSize: sizeInMinutes,
	}
}

func (sw *SlidingWindow) AddEvent(event SensorEvent) {
	sw.mu.Lock()
	defer sw.mu.Unlock()

	// Determine bucket start time (truncate to minute)
	bucketStart := event.Timestamp - (event.Timestamp % 60)

	// Find or create bucket
	var targetBucket *Bucket
	for _, b := range sw.buckets {
		if b.StartTime == bucketStart {
			targetBucket = b
			break
		}
	}

	if targetBucket == nil {
		targetBucket = &Bucket{
			StartTime: bucketStart,
			Sums:      make(map[string]float64),
		}
		sw.buckets = append(sw.buckets, targetBucket)
	}

	targetBucket.Sums[event.SensorID] += event.Value
}

func (sw *SlidingWindow) CleanupAndEvaluate() {
	sw.mu.Lock()
	defer sw.mu.Unlock()

	now := time.Now().Unix()
	currentMinute := now - (now % 60)
	windowStart := currentMinute - int64(sw.windowSize*60)

	var activeBuckets []*Bucket
	aggregatedSums := make(map[string]float64)

	for _, b := range sw.buckets {
		// Keep buckets within the window
		if b.StartTime >= windowStart {
			activeBuckets = append(activeBuckets, b)
			// Aggregate values across active buckets
			for sensor, val := range b.Sums {
				aggregatedSums[sensor] += val
			}
		}
	}

	sw.buckets = activeBuckets

	if len(aggregatedSums) > 0 {
		log.Println("=== 5-Minute Sliding Window Aggregation ===")
		for sensor, total := range aggregatedSums {
			log.Printf("Sensor: %s | Total Value: %.2f", sensor, total)
		}
		log.Println("===========================================")
	}
}

func main() {
	fmt.Println("Starting Sliding Window Aggregator...")

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
		GroupID:  "sliding-window-group",
		MinBytes: 10e3,
		MaxBytes: 10e6,
	})
	defer reader.Close()

	sw := NewSlidingWindow(5) // 5 minutes window

	// Evaluate sliding window every minute
	go func() {
		ticker := time.NewTicker(1 * time.Minute)
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				sw.CleanupAndEvaluate()
			case <-ctx.Done():
				return
			}
		}
	}()

	log.Printf("Listening for sensor data on topic '%s'...", inputTopic)

	for {
		m, err := reader.ReadMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				break
			}
			log.Printf("Error reading message: %v", err)
			continue
		}

		var event SensorEvent
		if err := json.Unmarshal(m.Value, &event); err != nil {
			log.Printf("Error unmarshalling event: %v", err)
			continue
		}

		// Fallback to current time if event lacks timestamp
		if event.Timestamp == 0 {
			event.Timestamp = time.Now().Unix()
		}

		sw.AddEvent(event)
	}

	log.Println("Sliding Window Aggregator stopped.")
}
