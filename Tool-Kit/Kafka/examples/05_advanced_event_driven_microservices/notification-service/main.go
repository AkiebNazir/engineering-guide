package main
import (
	"context"
	"fmt"
	"github.com/segmentio/kafka-go"
)
func main() {
	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers: []string{"kafka:9092"},
		GroupID: "notification-group", // Independent consumer group
		Topic:   "orders-topic",
	})
	defer r.Close()
	fmt.Println("[Notification Service] Listening for orders...")
	for {
		msg, _ := r.ReadMessage(context.Background())
		fmt.Printf("[Notification Service] Emailing receipt for: %s\n", string(msg.Value))
	}
}
