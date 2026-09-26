package main
import (
	"log"
	amqp "github.com/rabbitmq/amqp091-go"
)
func main() {
	conn, _ := amqp.Dial("amqp://guest:guest@localhost:5672/")
	defer conn.Close()
	ch, _ := conn.Channel()
	defer ch.Close()
	ch.ExchangeDeclare("logs", "fanout", true, false, false, false, nil)
	q, _ := ch.QueueDeclare("", false, false, true, false, nil)
	ch.QueueBind(q.Name, "", "logs", false, nil)
	msgs, _ := ch.Consume(q.Name, "", true, false, false, false, nil)

	var forever chan struct{}
	go func() {
		for d := range msgs {
			log.Printf(" [x] %s", d.Body)
		}
	}()
	log.Printf(" [*] Waiting for logs. To exit press CTRL+C")
	<-forever
}\n