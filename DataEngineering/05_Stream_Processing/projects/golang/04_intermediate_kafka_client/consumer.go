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

	// Dial the leader
	conn, err := kafka.DialLeader(context.Background(), "tcp", "localhost:9092", topic, partition)
	if err != nil {
		log.Fatalf("failed to dial leader: %v", err)
	}
	defer conn.Close()

	// Only read for 10 seconds to gracefully exit if no messages
	conn.SetReadDeadline(time.Now().Add(10 * time.Second))
	for {
		m, err := conn.ReadMessage(10e3)
		if err != nil {
			log.Printf("Consumer exiting (timeout or error): %v", err)
			break
		}
		fmt.Printf("Consumed message: %s\n", string(m.Value))
	}
}
