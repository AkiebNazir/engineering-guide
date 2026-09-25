package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/segmentio/kafka-go"
)

// This example demonstrates Consumer Groups.
// It creates a topic with 3 partitions, spins up 3 identical consumers in the SAME group,
// and produces messages. You will see Kafka automatically load-balance the partitions across the 3 consumers.

func main() {
	topic := "partitioned-topic"
	brokers := []string{"localhost:9092"}

	// 1. Create Topic with 3 partitions (Requires Kafka to be running)
	// In production, topic creation is usually done via CI/CD or Terraform, not code.
	
	var wg sync.WaitGroup
	ctx, cancel := context.WithCancel(context.Background())

	// Spin up 3 consumers sharing the same Group ID
	for i := 1; i <= 3; i++ {
		wg.Add(1)
		go runConsumer(ctx, &wg, brokers, topic, "my-scalable-group", i)
	}

	// Spin up 1 producer
	time.Sleep(2 * time.Second) // Wait for consumers to connect and rebalance
	go runProducer(brokers, topic)

	// Wait for Ctrl+C
	sigchan := make(chan os.Signal, 1)
	signal.Notify(sigchan, syscall.SIGINT, syscall.SIGTERM)
	<-sigchan
	fmt.Println("Shutting down...")
	cancel()
	wg.Wait()
}

func runConsumer(ctx context.Context, wg *sync.WaitGroup, brokers []string, topic, groupID string, id int) {
	defer wg.Done()
	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  brokers,
		GroupID:  groupID,
		Topic:    topic,
		MaxBytes: 10e6, // 10MB
	})
	defer r.Close()

	for {
		select {
		case <-ctx.Done():
			return
		default:
			msg, err := r.ReadMessage(ctx)
			if err != nil {
				continue
			}
			fmt.Printf("Consumer %d | Partition: %d | Message: %s\n", id, msg.Partition, string(msg.Value))
		}
	}
}

func runProducer(brokers []string, topic string) {
	w := &kafka.Writer{
		Addr:     kafka.TCP(brokers...),
		Topic:    topic,
		Balancer: &kafka.Hash{}, // Routes messages with same key to same partition
	}
	defer w.Close()

	for i := 0; i < 20; i++ {
		key := fmt.Sprintf("user-%d", i%5) // 5 unique users
		err := w.WriteMessages(context.Background(),
			kafka.Message{
				Key:   []byte(key),
				Value: []byte(fmt.Sprintf("Event %d for %s", i, key)),
			},
		)
		if err != nil {
			fmt.Println("Failed to write:", err)
		}
		time.Sleep(500 * time.Millisecond)
	}
}
