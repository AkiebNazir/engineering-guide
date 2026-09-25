package main
import (
	"context"
	"fmt"
	"github.com/segmentio/kafka-go"
)
func main() {
	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers: []string{"kafka:9092"},
		GroupID: "inventory-group", // Independent consumer group
		Topic:   "orders-topic",
	})
	defer r.Close()
	fmt.Println("[Inventory Service] Listening for orders...")
	for {
		msg, _ := r.ReadMessage(context.Background())
		fmt.Printf("[Inventory Service] Deducting stock for: %s\n", string(msg.Value))
	}
}
