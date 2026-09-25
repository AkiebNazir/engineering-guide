package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/segmentio/kafka-go"
)

func main() {
	topic := "events-topic"
	partition := 0

	// Dial the leader of the partition
	conn, err := kafka.DialLeader(context.Background(), "tcp", "localhost:9092", topic, partition)
	if err != nil {
		log.Fatalf("failed to dial leader: %v", err)
	}
	defer conn.Close()

	// Produce 10 messages
	for i := 1; i <= 10; i++ {
		msg := fmt.Sprintf("Event %d", i)
		_, err := conn.WriteMessages(
			kafka.Message{Value: []byte(msg)},
		)
		if err != nil {
			log.Fatalf("failed to write messages: %v", err)
		}
		fmt.Printf("Produced message: %s\n", msg)
		time.Sleep(500 * time.Millisecond) // Simulate delay between events
	}
}
