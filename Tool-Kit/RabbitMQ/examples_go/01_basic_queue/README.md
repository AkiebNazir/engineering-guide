# 01 Basic Queue (Golang)

**Goal:** Demonstrates the simplest form of RabbitMQ messaging with a single producer sending a message to a single consumer via a default exchange and a named queue.

**Deep Concept Explanation:**
In RabbitMQ, a producer never sends messages directly to a queue. It sends messages to an *exchange*. However, in this basic example, we use the default exchange (identified by an empty string `""`). The default exchange implicitly routes messages to the queue with the exact name specified in the routing key.
We also declare the queue in both the producer and consumer. This is a best practice to ensure the queue exists regardless of which program starts first. 

**Prerequisites:** 
- RabbitMQ running: `docker run -d --name rabbitmq -p 5672:5672 rabbitmq`
- Go installed. Initialize the module: `go mod init basic_queue && go get github.com/rabbitmq/amqp091-go`

**Execution:** 
1. Start the consumer: `go run consumer.go`
2. Run the producer: `go run producer.go`\n