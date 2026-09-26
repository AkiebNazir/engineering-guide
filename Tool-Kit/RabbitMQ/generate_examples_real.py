import os

base = "/Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ"
files = {}

# Python Examples
files["examples/01_basic_queue/README.md"] = """# 01 Basic Queue (Python)

**Goal:** Demonstrates the simplest form of RabbitMQ messaging with a single producer sending a message to a single consumer via a default exchange and a named queue.

**Deep Concept Explanation:**
In RabbitMQ, a producer never sends messages directly to a queue. It sends messages to an *exchange*. However, in this basic example, we use the default exchange (identified by an empty string `""`). The default exchange implicitly routes messages to the queue with the exact name specified in the routing key.

**Prerequisites:** 
- RabbitMQ running: `docker run -d --name rabbitmq -p 5672:5672 rabbitmq`
- Python installed. Initialize: `pip install pika`

**Execution:** 
1. Start the consumer: `python consumer.py`
2. Run the producer: `python producer.py`
"""
files["examples/01_basic_queue/producer.py"] = """import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare a queue
channel.queue_declare(queue='hello')

# Publish to default exchange
channel.basic_publish(exchange='', routing_key='hello', body='Hello World!')
print(" [x] Sent 'Hello World!'")
connection.close()
"""
files["examples/01_basic_queue/consumer.py"] = """import pika
import sys
import os

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare queue (idempotent, ensures it exists)
    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        print(f" [x] Received {body.decode()}")

    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
"""

files["examples/02_worker_queue/README.md"] = """# 02 Worker Queue (Python)

**Goal:** Distributes time-consuming tasks among multiple workers.

**Deep Concept Explanation:**
Worker Queues (or Task Queues) are used to distribute time-consuming tasks among multiple workers to avoid running resource-intensive tasks synchronously. 
RabbitMQ dispatches messages to consumers using **Round-Robin** by default. We use `channel.basic_qos(prefetch_count=1)` to tell RabbitMQ not to give more than one message to a worker at a time, ensuring fair dispatch.
"""
files["examples/02_worker_queue/new_task.py"] = """import pika
import sys

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Durable queue survives broker restarts
channel.queue_declare(queue='task_queue', durable=True)

message = ' '.join(sys.argv[1:]) or "Hello World!"
channel.basic_publish(
    exchange='',
    routing_key='task_queue',
    body=message,
    properties=pika.BasicProperties(
        delivery_mode=pika.DeliveryMode.Persistent
    ))
print(f" [x] Sent {message}")
connection.close()
"""
files["examples/02_worker_queue/worker.py"] = """import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    time.sleep(body.count(b'.'))
    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Fair dispatch
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)
channel.start_consuming()
"""

files["examples/03_pubsub_fanout/README.md"] = """# 03 PubSub Fanout (Python)

**Goal:** Deliver a message to multiple consumers at once.

**Deep Concept Explanation:**
The `fanout` exchange broadcasts all the messages it receives to all the queues it knows. Here, we create temporary, exclusive queues for our consumers and bind them to the fanout exchange.
"""
files["examples/03_pubsub_fanout/emit_log.py"] = """import pika
import sys

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='logs', exchange_type='fanout')

message = ' '.join(sys.argv[1:]) or "info: Hello World!"
channel.basic_publish(exchange='logs', routing_key='', body=message)
print(f" [x] Sent {message}")
connection.close()
"""
files["examples/03_pubsub_fanout/receive_logs.py"] = """import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='logs', exchange_type='fanout')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

channel.queue_bind(exchange='logs', queue=queue_name)
print(' [*] Waiting for logs. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] {body.decode()}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()
"""

files["examples/04_routing_direct/README.md"] = """# 04 Routing Direct (Python)

**Goal:** Route messages selectively to different queues based on a routing key.

**Deep Concept Explanation:**
The `direct` exchange routes messages to queues whose binding key exactly matches the routing key of the message. This allows us to subscribe to only a subset of messages (e.g. only 'error' logs).
"""
files["examples/04_routing_direct/emit_log_direct.py"] = """import pika
import sys

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='direct_logs', exchange_type='direct')

severity = sys.argv[1] if len(sys.argv) > 1 else 'info'
message = ' '.join(sys.argv[2:]) or 'Hello World!'
channel.basic_publish(exchange='direct_logs', routing_key=severity, body=message)
print(f" [x] Sent {severity}:{message}")
connection.close()
"""
files["examples/04_routing_direct/receive_logs_direct.py"] = """import pika
import sys

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

severities = sys.argv[1:]
if not severities:
    sys.stderr.write("Usage: %s [info] [warning] [error]\n" % sys.argv[0])
    sys.exit(1)

for severity in severities:
    channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=severity)

print(' [*] Waiting for logs. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] {method.routing_key}:{body.decode()}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()
"""

files["examples/05_advanced_topics/README.md"] = """# 05 Advanced Topics (Python)

**Goal:** Route messages to queues based on multiple criteria using wildcard patterns.

**Deep Concept Explanation:**
The `topic` exchange routes messages to queues based on a wildcard match between the routing key and the routing pattern specified in the queue binding.
- `*` (star) can substitute for exactly one word.
- `#` (hash) can substitute for zero or more words.
"""
files["examples/05_advanced_topics/emit_log_topic.py"] = """import pika
import sys

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='topic_logs', exchange_type='topic')

routing_key = sys.argv[1] if len(sys.argv) > 2 else 'anonymous.info'
message = ' '.join(sys.argv[2:]) or 'Hello World!'
channel.basic_publish(exchange='topic_logs', routing_key=routing_key, body=message)
print(f" [x] Sent {routing_key}:{message}")
connection.close()
"""
files["examples/05_advanced_topics/receive_logs_topic.py"] = """import pika
import sys

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='topic_logs', exchange_type='topic')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

binding_keys = sys.argv[1:]
if not binding_keys:
    sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
    sys.exit(1)

for binding_key in binding_keys:
    channel.queue_bind(exchange='topic_logs', queue=queue_name, routing_key=binding_key)

print(' [*] Waiting for logs. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] {method.routing_key}:{body.decode()}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()
"""


# Golang Examples
files["examples_go/01_basic_queue/README.md"] = """# 01 Basic Queue (Golang)

**Goal:** Demonstrates the simplest form of RabbitMQ messaging with a single producer sending a message to a single consumer via a default exchange and a named queue.

**Deep Concept Explanation:**
In RabbitMQ, a producer never sends messages directly to a queue. It sends messages to an *exchange*. However, in this basic example, we use the default exchange (identified by an empty string `""`). The default exchange implicitly routes messages to the queue with the exact name specified in the routing key.
We also declare the queue in both the producer and consumer. This is a best practice to ensure the queue exists regardless of which program starts first. 

**Prerequisites:** 
- RabbitMQ running: `docker run -d --name rabbitmq -p 5672:5672 rabbitmq`
- Go installed. Initialize the module: `go mod init basic_queue && go get github.com/rabbitmq/amqp091-go`

**Execution:** 
1. Start the consumer: `go run consumer.go`
2. Run the producer: `go run producer.go`
"""
files["examples_go/01_basic_queue/producer.go"] = """package main

import (
	"context"
	"log"
	"time"

	amqp "github.com/rabbitmq/amqp091-go"
)

func failOnError(err error, msg string) {
	if err != nil {
		log.Panicf("%s: %s", msg, err)
	}
}

func main() {
	conn, err := amqp.Dial("amqp://guest:guest@localhost:5672/")
	failOnError(err, "Failed to connect to RabbitMQ")
	defer conn.Close()

	ch, err := conn.Channel()
	failOnError(err, "Failed to open a channel")
	defer ch.Close()

	q, err := ch.QueueDeclare(
		"hello", // name
		false,   // durable
		false,   // delete when unused
		false,   // exclusive
		false,   // no-wait
		nil,     // arguments
	)
	failOnError(err, "Failed to declare a queue")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	body := "Hello World from Golang!"
	err = ch.PublishWithContext(ctx,
		"",     // exchange
		q.Name, // routing key
		false,  // mandatory
		false,  // immediate
		amqp.Publishing{
			ContentType: "text/plain",
			Body:        []byte(body),
		})
	failOnError(err, "Failed to publish a message")
	log.Printf(" [x] Sent %s\\n", body)
}
"""
files["examples_go/01_basic_queue/consumer.go"] = """package main

import (
	"log"

	amqp "github.com/rabbitmq/amqp091-go"
)

func failOnError(err error, msg string) {
	if err != nil {
		log.Panicf("%s: %s", msg, err)
	}
}

func main() {
	conn, err := amqp.Dial("amqp://guest:guest@localhost:5672/")
	failOnError(err, "Failed to connect to RabbitMQ")
	defer conn.Close()

	ch, err := conn.Channel()
	failOnError(err, "Failed to open a channel")
	defer ch.Close()

	q, err := ch.QueueDeclare("hello", false, false, false, false, nil)
	failOnError(err, "Failed to declare a queue")

	msgs, err := ch.Consume(q.Name, "", true, false, false, false, nil)
	failOnError(err, "Failed to register a consumer")

	var forever chan struct{}
	go func() {
		for d := range msgs {
			log.Printf("Received a message: %s", d.Body)
		}
	}()

	log.Printf(" [*] Waiting for messages. To exit press CTRL+C")
	<-forever
}
"""

files["examples_go/02_worker_queue/README.md"] = """# 02 Worker Queue (Golang)

**Goal:** Distributes time-consuming tasks among multiple workers.
"""
files["examples_go/02_worker_queue/worker.go"] = """package main
import (
	"bytes"
	"log"
	"time"
	amqp "github.com/rabbitmq/amqp091-go"
)
func main() {
	conn, _ := amqp.Dial("amqp://guest:guest@localhost:5672/")
	defer conn.Close()
	ch, _ := conn.Channel()
	defer ch.Close()
	q, _ := ch.QueueDeclare("task_queue", true, false, false, false, nil)
	err := ch.Qos(1, 0, false)
	msgs, _ := ch.Consume(q.Name, "", false, false, false, false, nil)

	var forever chan struct{}
	go func() {
		for d := range msgs {
			log.Printf("Received a message: %s", d.Body)
			dotCount := bytes.Count(d.Body, []byte("."))
			t := time.Duration(dotCount)
			time.Sleep(t * time.Second)
			log.Printf("Done")
			d.Ack(false)
		}
	}()
	log.Printf(" [*] Waiting for messages. To exit press CTRL+C")
	<-forever
}
"""
files["examples_go/02_worker_queue/new_task.go"] = """package main
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
	q, _ := ch.QueueDeclare("task_queue", true, false, false, false, nil)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	body := bodyFrom(os.Args)
	ch.PublishWithContext(ctx, "", q.Name, false, false, amqp.Publishing{
		DeliveryMode: amqp.Persistent,
		ContentType:  "text/plain",
		Body:         []byte(body),
	})
	log.Printf(" [x] Sent %s", body)
}
func bodyFrom(args []string) string {
	var s string
	if (len(args) < 2) || os.Args[1] == "" {
		s = "hello"
	} else {
		s = strings.Join(args[1:], " ")
	}
	return s
}
"""

files["examples_go/03_pubsub_fanout/README.md"] = """# 03 PubSub Fanout (Golang)"""
files["examples_go/03_pubsub_fanout/receive_logs.go"] = """package main
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
}
"""
files["examples_go/03_pubsub_fanout/emit_log.go"] = """package main
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
	ch.ExchangeDeclare("logs", "fanout", true, false, false, false, nil)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	body := "info: Hello World!"
	if len(os.Args) > 1 {
		body = strings.Join(os.Args[1:], " ")
	}
	ch.PublishWithContext(ctx, "logs", "", false, false, amqp.Publishing{
		ContentType: "text/plain",
		Body:        []byte(body),
	})
	log.Printf(" [x] Sent %s", body)
}
"""

files["examples_go/04_routing_direct/README.md"] = """# 04 Routing Direct (Golang)"""
files["examples_go/04_routing_direct/receive_logs_direct.go"] = """package main
import (
	"log"
	"os"
	amqp "github.com/rabbitmq/amqp091-go"
)
func main() {
	conn, _ := amqp.Dial("amqp://guest:guest@localhost:5672/")
	defer conn.Close()
	ch, _ := conn.Channel()
	defer ch.Close()
	ch.ExchangeDeclare("logs_direct", "direct", true, false, false, false, nil)
	q, _ := ch.QueueDeclare("", false, false, true, false, nil)

	if len(os.Args) < 2 {
		log.Printf("Usage: %s [info] [warning] [error]", os.Args[0])
		os.Exit(0)
	}
	for _, s := range os.Args[1:] {
		ch.QueueBind(q.Name, s, "logs_direct", false, nil)
	}

	msgs, _ := ch.Consume(q.Name, "", true, false, false, false, nil)

	var forever chan struct{}
	go func() {
		for d := range msgs {
			log.Printf(" [x] %s", d.Body)
		}
	}()
	log.Printf(" [*] Waiting for logs. To exit press CTRL+C")
	<-forever
}
"""
files["examples_go/04_routing_direct/emit_log_direct.go"] = """package main
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
	ch.ExchangeDeclare("logs_direct", "direct", true, false, false, false, nil)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	severity := "info"
	if len(os.Args) > 1 {
		severity = os.Args[1]
	}
	body := "Hello World!"
	if len(os.Args) > 2 {
		body = strings.Join(os.Args[2:], " ")
	}

	ch.PublishWithContext(ctx, "logs_direct", severity, false, false, amqp.Publishing{
		ContentType: "text/plain",
		Body:        []byte(body),
	})
	log.Printf(" [x] Sent %s", body)
}
"""

files["examples_go/05_advanced_topics/README.md"] = """# 05 Advanced Topics (Golang)"""
files["examples_go/05_advanced_topics/receive_logs_topic.go"] = """package main
import (
	"log"
	"os"
	amqp "github.com/rabbitmq/amqp091-go"
)
func main() {
	conn, _ := amqp.Dial("amqp://guest:guest@localhost:5672/")
	defer conn.Close()
	ch, _ := conn.Channel()
	defer ch.Close()
	ch.ExchangeDeclare("logs_topic", "topic", true, false, false, false, nil)
	q, _ := ch.QueueDeclare("", false, false, true, false, nil)

	if len(os.Args) < 2 {
		log.Printf("Usage: %s [binding_key]...", os.Args[0])
		os.Exit(0)
	}
	for _, s := range os.Args[1:] {
		ch.QueueBind(q.Name, s, "logs_topic", false, nil)
	}

	msgs, _ := ch.Consume(q.Name, "", true, false, false, false, nil)

	var forever chan struct{}
	go func() {
		for d := range msgs {
			log.Printf(" [x] %s", d.Body)
		}
	}()
	log.Printf(" [*] Waiting for logs. To exit press CTRL+C")
	<-forever
}
"""
files["examples_go/05_advanced_topics/emit_log_topic.go"] = """package main
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
}
"""

for filepath, content in files.items():
    full_path = os.path.join(base, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content.strip() + "\\n")
