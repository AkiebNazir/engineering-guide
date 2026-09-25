# RabbitMQ & Message Brokers

RabbitMQ is the most widely deployed open-source message broker. It implements the Advanced Message Queuing Protocol (AMQP) which provides robust messaging for applications.


## Interactive Examples

We provide several practical examples in the `examples/` directory to help you understand RabbitMQ concepts hands-on:
- [01 Basic Queue](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/01_basic_queue)
- [02 Basic Worker Queue](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/02_basic_worker_queue)
- [03 Intermediate PubSub Fanout](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/03_intermediate_pubsub_fanout)
- [04 Intermediate Routing Topic](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/04_intermediate_routing_topic)
- [05 Advanced DLX TTL](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/05_advanced_dlx_ttl)

## AMQP Architecture

The core of RabbitMQ's messaging model involves several key components:

1. **Publishers**: Applications that send messages to the broker.
2. **Exchanges**: The post offices of RabbitMQ. Publishers send messages to exchanges, not directly to queues. An exchange is responsible for routing the messages to zero or more queues.
3. **Queues**: Buffers that store messages. Consumers receive messages from queues.
   > [!TIP]
   > Check out the [Basic Queue example](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/01_basic_queue) and [Worker Queue example](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/02_basic_worker_queue) to see this in action.
4. **Bindings**: Rules that link an exchange to a queue.
5. **Routing Keys**: A message attribute that the exchange uses to decide how to route the message to queues (used in combination with bindings).

### Exchange Types

* **Direct**: Routes messages to a queue whose binding key exactly matches the routing key of the message.
* **Topic**: Routes messages to one or many queues based on a wildcard match between the routing key and the routing pattern specified in the binding.
  > [!TIP]
  > See the [Routing Topic example](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/04_intermediate_routing_topic) for wildcard routing.
* **Fanout**: Broadcasts all messages it receives to all queues it knows about (routing keys are ignored).
  > [!TIP]
  > See the [PubSub Fanout example](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/03_intermediate_pubsub_fanout) for broadcasting messages.
* **Headers**: Routes based on multiple attributes that are more easily expressed as message headers than a routing key.

## Architecture Diagram

```arch
node pub "Publisher" at 0,1 icon=client
node exch "Direct Exchange" at 1,1 icon=network
node q1 "Queue: errors" at 2,0 icon=db
node q2 "Queue: logs" at 2,2 icon=db
node work1 "Worker 1" at 3,0 icon=worker
node work2 "Worker 2" at 3,2 icon=worker

pub -> exch
exch -> q1 : "routing_key=error"
exch -> q2 : "routing_key=info"
q1 -> work1
q2 -> work2
```

## Dead Letter Exchanges (DLX) and Message TTL

> [!TIP]
> Try the [Advanced DLX TTL example](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/05_advanced_dlx_ttl) to handle failed messages and expirations.

**Dead Letter Exchanges (DLX)** are normal exchanges that receive messages from queues when they cannot be delivered successfully to a consumer. A message can be "dead-lettered" for several reasons:
* The message is rejected (`basic.reject` or `basic.nack`) with `requeue=false`.
* The TTL (Time-To-Live) for the message expires.
* The queue length limit is exceeded.

**Message TTL** allows you to specify how long a message should stay in a queue before it is discarded or dead-lettered. This is useful for building features like delayed queues or ensuring timely processing.

## Production-Grade Code Examples

### Golang (`rabbitmq/amqp091-go`)

```go
package main

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

	// Declare an exchange
	err = ch.ExchangeDeclare(
		"logs_direct", // name
		"direct",      // type
		true,          // durable
		false,         // auto-deleted
		false,         // internal
		false,         // no-wait
		nil,           // arguments
	)
	failOnError(err, "Failed to declare an exchange")

	// Declare a queue
	q, err := ch.QueueDeclare(
		"error_logs", // name
		true,         // durable
		false,        // delete when unused
		false,        // exclusive
		false,        // no-wait
		nil,          // arguments
	)
	failOnError(err, "Failed to declare a queue")

	// Bind the queue to the exchange
	err = ch.QueueBind(
		q.Name,        // queue name
		"error",       // routing key
		"logs_direct", // exchange
		false,
		nil,
	)
	failOnError(err, "Failed to bind a queue")

	// Publish a message
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	body := "Critical error occurred!"
	err = ch.PublishWithContext(ctx,
		"logs_direct", // exchange
		"error",       // routing key
		false,         // mandatory
		false,         // immediate
		amqp.Publishing{
			ContentType:  "text/plain",
			DeliveryMode: amqp.Persistent,
			Body:         []byte(body),
		})
	failOnError(err, "Failed to publish a message")
	log.Printf(" [x] Sent %s", body)

	// Consume messages
	msgs, err := ch.Consume(
		q.Name, // queue
		"",     // consumer
		false,  // auto-ack
		false,  // exclusive
		false,  // no-local
		false,  // no-wait
		nil,    // args
	)
	failOnError(err, "Failed to register a consumer")

	var forever chan struct{}

	go func() {
		for d := range msgs {
			log.Printf("Received a message: %s", d.Body)
			// Acknowledge the message
			d.Ack(false)
		}
	}()

	log.Printf(" [*] Waiting for messages. To exit press CTRL+C")
	<-forever
}
```

### Python (`pika`)

```python
import pika
import sys

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare an exchange
    channel.exchange_declare(exchange='logs_direct', exchange_type='direct', durable=True)

    # Declare a queue
    result = channel.queue_declare(queue='error_logs', durable=True)
    queue_name = result.method.queue

    # Bind queue to exchange
    channel.queue_bind(exchange='logs_direct', queue=queue_name, routing_key='error')

    # Publish a message
    message = "Critical error occurred!"
    channel.basic_publish(
        exchange='logs_direct',
        routing_key='error',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent
        ))
    print(f" [x] Sent {message}")

    # Consume messages
    def callback(ch, method, properties, body):
        print(f" [x] Received {body.decode()}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            pass
```

## MAANG-Level Interview Questions

1. **How does RabbitMQ differ from Kafka? When would you use one over the other?**
   * **Answer:** RabbitMQ is a traditional message broker focusing on complex routing and message delivery guarantees, built on AMQP. It excels at point-to-point communication and complex routing topologies. Kafka is a distributed streaming platform, effectively a distributed, append-only commit log. It excels at high-throughput, event sourcing, stream processing, and data replay. Use RabbitMQ for complex routing and task queues. Use Kafka for massive throughput, event streaming, and when you need to retain/replay historical data.

2. **Explain the purpose of Dead Letter Exchanges (DLX). How do you configure them?**
   * **Answer:** DLXs catch messages that cannot be processed successfully (e.g., rejected, TTL expired, queue length exceeded). They allow you to isolate failing messages for later analysis or manual intervention without blocking the main queues. They are configured via queue arguments (e.g., `x-dead-letter-exchange` and `x-dead-letter-routing-key`) when declaring the primary queue.

3. **How can you implement an RPC (Remote Procedure Call) pattern using RabbitMQ?**
   * **Answer:** An RPC client publishes a message to a request queue. The message includes a `reply_to` property (specifying an anonymous exclusive queue created by the client) and a `correlation_id` (a unique ID for the request). The RPC server consumes from the request queue, processes the work, and publishes the result to the queue specified in `reply_to`, carrying over the `correlation_id`. The client consumes from its `reply_to` queue and uses the `correlation_id` to match responses to requests.

4. **What is message acknowledgment and why is it important? Describe `auto-ack` vs. manual ack.**
   * **Answer:** Acknowledgment tells the broker a message has been successfully processed and can be removed from the queue. It ensures reliability. With `auto-ack` (fire-and-forget), the broker considers the message delivered immediately upon sending it to the consumer; if the consumer crashes before processing, the message is lost. Manual ack requires the consumer to explicitly send an ack (e.g., `basic.ack`) after processing. If the consumer crashes without acking, the broker requeues the message.

5. **How does a 'Topic' exchange work? Provide an example.**
   * **Answer:** A topic exchange routes messages based on a wildcard match of the routing key. Routing keys are typically words separated by dots (e.g., `log.error.db`). Bindings use wildcards: `*` matches exactly one word, and `#` matches zero or more words. For example, binding `*.error.*` matches `app.error.db`, while `log.#` matches `log.info` and `log.error.auth`.

6. **What is the significance of the `durable` flag in RabbitMQ exchanges and queues?**
   * **Answer:** Marking an exchange or queue as `durable` ensures that its metadata is saved to disk. If the RabbitMQ server restarts, the durable exchanges and queues will be automatically recreated. This is crucial for high availability but does *not* automatically persist the messages within them.

7. **How do you ensure messages survive a RabbitMQ server crash?**
   * **Answer:** You need three things: 1) The exchange must be `durable`. 2) The queue must be `durable`. 3) The messages themselves must be published with a delivery mode of `persistent` (e.g., `delivery_mode=2` in basic.publish). This instructs RabbitMQ to write the messages to disk.

8. **What is publisher confirms, and why is it preferred over transactions?**
   * **Answer:** Publisher confirms are an AMQP extension where the broker asynchronously acks back to the publisher when a message is successfully handled (e.g., routed to queues and persisted if required). AMQP transactions (`tx.select`, `tx.commit`) are synchronous and heavily degrade throughput. Publisher confirms provide reliable publishing with much better performance.

9. **Explain queue mirroring (classic mirrored queues) vs. Quorum Queues in RabbitMQ.**
   * **Answer:** Classic mirrored queues copy messages across multiple nodes for high availability, but suffer from synchronization issues and network partition vulnerabilities. Quorum Queues (introduced later) use the Raft consensus algorithm, providing stronger data safety guarantees, better predictable performance under load, and safer handling of network partitions. Quorum Queues are now the recommended approach for HA.

10. **How do you handle unroutable messages?**
    * **Answer:** By default, messages published with a routing key that matches no bindings are silently dropped. You can handle this by publishing with the `mandatory` flag. If the message cannot be routed to any queue, the broker will return the message to the publisher via a `basic.return` method, allowing the publisher to handle the failure. Alternatively, you can configure an Alternate Exchange for an exchange to route unhandled messages.
