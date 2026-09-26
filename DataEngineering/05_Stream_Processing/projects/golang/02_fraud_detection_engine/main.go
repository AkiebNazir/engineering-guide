package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/segmentio/kafka-go"
)

var (
	kafkaBroker = "localhost:9092"
	inputTopic  = "transactions"
	outputTopic = "fraud_alerts"
)

type Transaction struct {
	TransactionID string  `json:"transaction_id"`
	UserID        string  `json:"user_id"`
	Amount        float64 `json:"amount"`
	Location      string  `json:"location"`
	Timestamp     string  `json:"timestamp"`
}

type FraudAlert struct {
	TransactionID string  `json:"transaction_id"`
	UserID        string  `json:"user_id"`
	Amount        float64 `json:"amount"`
	Reason        string  `json:"reason"`
	Timestamp     string  `json:"timestamp"`
}

func main() {
	fmt.Println("Starting Fraud Detection Engine...")

	// Context with cancellation on interrupt
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigChan
		log.Println("Shutting down gracefully...")
		cancel()
	}()

	// Kafka Reader (Consumer)
	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  []string{kafkaBroker},
		Topic:    inputTopic,
		GroupID:  "fraud-detector-group",
		MinBytes: 10e3,
		MaxBytes: 10e6,
	})
	defer reader.Close()

	// Kafka Writer (Producer)
	writer := &kafka.Writer{
		Addr:     kafka.TCP(kafkaBroker),
		Topic:    outputTopic,
		Balancer: &kafka.LeastBytes{},
	}
	defer writer.Close()

	log.Printf("Listening for transactions on topic '%s'...", inputTopic)

	for {
		m, err := reader.ReadMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				break // context cancelled
			}
			log.Printf("Error reading message: %v", err)
			continue
		}

		var tx Transaction
		if err := json.Unmarshal(m.Value, &tx); err != nil {
			log.Printf("Error unmarshalling transaction: %v", err)
			continue
		}

		// Fraud Rule: Amount greater than 10,000
		if tx.Amount > 10000.0 {
			alert := FraudAlert{
				TransactionID: tx.TransactionID,
				UserID:        tx.UserID,
				Amount:        tx.Amount,
				Reason:        "Amount exceeds threshold of 10,000",
				Timestamp:     tx.Timestamp,
			}

			alertBytes, err := json.Marshal(alert)
			if err != nil {
				log.Printf("Error marshalling alert: %v", err)
				continue
			}

			err = writer.WriteMessages(ctx, kafka.Message{
				Key:   []byte(tx.TransactionID),
				Value: alertBytes,
			})
			if err != nil {
				log.Printf("Error publishing alert: %v", err)
			} else {
				log.Printf("Generated fraud alert for transaction %s", tx.TransactionID)
			}
		}
	}

	log.Println("Fraud Detection Engine stopped.")
}
