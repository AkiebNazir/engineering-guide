package main
import (
	"context"
	"log"
	"os"
	"strings"
	"time"
	amqp "github.com/rabbitmq/amqp091-go"
)
func main() {
	conn, _ := amqp.Dial("amqp://guest:guest@localhost:5672/")
	defer conn.Close()
	ch, _ := conn.Channel()
	defer ch.Close()
	ch.ExchangeDeclare("logs_topic", "topic", true, false, false, false, nil)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	routingKey := "anonymous.info"
	if len(os.Args) > 1 {
		routingKey = os.Args[1]
	}
	body := "Hello World!"
	if len(os.Args) > 2 {
		body = strings.Join(os.Args[2:], " ")
	}

	ch.PublishWithContext(ctx, "logs_topic", routingKey, false, false, amqp.Publishing{
		ContentType: "text/plain",
		Body:        []byte(body),
	})
	log.Printf(" [x] Sent %s", body)
}\n