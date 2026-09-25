# RabbitMQ and Message Brokers

While Kafka is a durable, replayable log for stream processing, RabbitMQ is a traditional message broker built for complex routing and task queues. It implements the AMQP (Advanced Message Queuing Protocol).

## 1. Exchanges, Bindings, and Queues

In Kafka, producers write directly to a Topic. In RabbitMQ, producers *never* write directly to a queue. They write to an **Exchange**, which routes the message to zero or more **Queues** based on **Bindings**.

```arch
%% caption: Producers publish to an Exchange, which uses Binding rules to route the message to specific Queues.
route straight
node p "Producer" at 1,0 icon=client color=blue
node ex "Exchange" at 1,1 icon=network color=amber
node q1 "Queue 1" at 0,2 icon=queue color=slate
node q2 "Queue 2" at 2,2 icon=queue color=slate
node c1 "Consumer 1" at 0,3 icon=worker color=green
node c2 "Consumer 2" at 2,3 icon=worker color=green

p -> ex : "publishes"
ex -> q1 : "routing: email.*"
ex -> q2 : "routing: *.error"
q1 -> c1
q2 -> c2
```

### Exchange Types
- **Direct**: Routes to a queue if the routing key exactly matches the binding key (e.g., `pdf_processor`).
- **Topic**: Routes based on wildcard patterns (e.g., `logs.error.*` matches `logs.error.auth`).
- **Fanout**: Ignores the routing key and broadcasts the message to *all* bound queues (like a pub/sub system).
- **Headers**: Routes based on HTTP-style headers instead of the routing key string.

## 2. Competing Consumers and Fair Dispatch

If you have one queue (e.g., `image_resizing`) and 5 consumers attached to it, RabbitMQ round-robins the messages to them (Competing Consumers pattern). 

To prevent one consumer from getting overwhelmed with large tasks while others sit idle, use **Prefetch Count (QoS = 1)**. This tells RabbitMQ not to send a new message to a consumer until it has acknowledged (ACKed) the previous one.

## 3. Reliability and Acknowledgements

Unlike Kafka, RabbitMQ deletes a message from the queue once it is processed.

- **Auto-ACK**: RabbitMQ considers the message delivered and deletes it the moment it sends it over the network. If the consumer crashes before finishing the work, the message is lost.
- **Manual-ACK**: The consumer explicitly sends an `ack` back to RabbitMQ after it finishes the work. If the network connection drops before the `ack` is received, RabbitMQ re-queues the message.

## 4. Dead Letter Exchanges (DLX)

If a message cannot be processed (e.g., the consumer throws an exception because the JSON is malformed), you don't want it to clog the queue forever.

You can configure a queue to route rejected messages (or messages that expire via TTL) to a Dead Letter Exchange. This routes them to a Dead Letter Queue (DLQ) where an engineer can manually inspect them later.

## 5. When to Choose RabbitMQ over Kafka

- You need complex routing rules (Topic/Direct exchanges).
- You are building a task/job queue (like sending emails or resizing images) where messages can be safely deleted after processing.
- You want "Competing Consumers" to pull from the exact same queue without having to configure exact partition counts (Kafka forces you to have at least as many partitions as consumers).
- You want built-in Dead Lettering and delayed/scheduled messages (via plugins).
