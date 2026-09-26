package main

import (
	"context"
	"fmt"
	"log"
	"os/signal"
	"syscall"
	"time"

	"github.com/segmentio/kafka-go"
)

func main() {
	log.Println("Starting Data Engineering Project: 03_cdc_log_tailer (Kafka Consumer)")

	brokers := os.Getenv("KAFKA_BROKERS")
	if brokers == "" {
		brokers = "localhost:9092"
	}

	topic := os.Getenv("KAFKA_CDC_TOPIC")
	if topic == "" {
		topic = "dbserver1.inventory.customers"
	}

	groupID := os.Getenv("KAFKA_GROUP_ID")
	if groupID == "" {
		groupID = "cdc-tailer-group"
	}

	// Setup Kafka Reader
	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:        []string{brokers},
		GroupID:        groupID,
		Topic:          topic,
		MinBytes:       10e3, // 10KB
		MaxBytes:       10e6, // 10MB
		CommitInterval: time.Second,
		StartOffset:    kafka.FirstOffset,
	})
	defer reader.Close()

	log.Printf("Subscribed to topic %s. Waiting for events...", topic)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigs
		log.Println("Shutting down consumer...")
		cancel()
	}()

	for {
		m, err := reader.FetchMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				break // Shutdown gracefully
			}
			log.Printf("Failed to fetch message: %v", err)
			time.Sleep(1 * time.Second)
			continue
		}

		fmt.Printf("CDC Event Detected at offset %d: key=%s value=%s\n", m.Offset, string(m.Key), string(m.Value))

		if err := reader.CommitMessages(ctx, m); err != nil {
			log.Printf("Failed to commit message: %v", err)
		}
	}
	log.Println("Consumer stopped cleanly.")
}
