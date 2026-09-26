package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/segmentio/kafka-go"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var (
	kafkaBroker = "localhost:9092"
	kafkaTopic  = "user_activity"
	dbDSN       = "host=localhost user=user password=password dbname=analytics_db port=5432 sslmode=disable"
)

type UserActivity struct {
	ID           uint      `gorm:"primaryKey"`
	UserID       string    `gorm:"index"`
	ActivityType string
	Value        float64
	Timestamp    time.Time
}

type ActivityMessage struct {
	UserID       string  `json:"user_id"`
	ActivityType string  `json:"activity_type"`
	Value        float64 `json:"value"`
	Timestamp    string  `json:"timestamp"`
}

func main() {
	fmt.Println("Starting Kafka to DB Consumer...")

	// Initialize Database connection
	db, err := gorm.Open(postgres.Open(dbDSN), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Error),
	})
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	// Auto Migrate the schema
	if err := db.AutoMigrate(&UserActivity{}); err != nil {
		log.Fatalf("Failed to migrate database: %v", err)
	}

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
		Topic:    kafkaTopic,
		GroupID:  "db-consumer-group",
		MinBytes: 10e3,
		MaxBytes: 10e6,
	})
	defer reader.Close()

	log.Printf("Listening for messages on topic '%s'...", kafkaTopic)

	batchSize := 100
	var batch []UserActivity

	for {
		m, err := reader.ReadMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				break
			}
			log.Printf("Error reading message: %v", err)
			continue
		}

		var msg ActivityMessage
		if err := json.Unmarshal(m.Value, &msg); err != nil {
			log.Printf("Error unmarshalling message: %v", err)
			continue
		}

		ts, err := time.Parse(time.RFC3339, msg.Timestamp)
		if err != nil {
			ts = time.Now()
		}

		activity := UserActivity{
			UserID:       msg.UserID,
			ActivityType: msg.ActivityType,
			Value:        msg.Value,
			Timestamp:    ts,
		}

		batch = append(batch, activity)

		if len(batch) >= batchSize {
			if err := db.Create(&batch).Error; err != nil {
				log.Printf("Error inserting batch to DB: %v", err)
			} else {
				log.Printf("Committed %d records to database.", len(batch))
			}
			batch = batch[:0] // Clear batch
		}
	}

	// Flush remaining batch
	if len(batch) > 0 {
		if err := db.Create(&batch).Error; err != nil {
			log.Printf("Error inserting final batch to DB: %v", err)
		} else {
			log.Printf("Committed final %d records to database.", len(batch))
		}
	}

	log.Println("Kafka to DB Consumer stopped.")
}
