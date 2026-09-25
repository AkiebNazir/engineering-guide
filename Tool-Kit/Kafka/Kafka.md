# Kafka and Event Streaming

Welcome to the comprehensive guide on Apache Kafka. Kafka is not just a message queue; it is a distributed, highly scalable, elastic, fault-tolerant, and secure event streaming platform.

If you are building microservices that need to communicate asynchronously, or if you need to ingest millions of events per second (like website clicks, financial transactions, or IoT sensor data), Kafka is the industry standard.

---

## 1. Ground Zero: What is Event Streaming?

Before Kafka, systems typically communicated in one of two ways:
1.  **Synchronous API Calls (REST/gRPC):** Service A waits for Service B to respond. If Service B is down, Service A fails.
2.  **Batch Processing (Cron Jobs):** A database is polled every hour for new records. This means data is always stale by up to an hour.

**Event Streaming** is a paradigm shift. Instead of polling for data, or blocking on API calls, Service A simply emits a "fact" (an Event) that something happened (e.g., `UserCreated`). It drops this event into Kafka and immediately moves on. Service B, Service C, and Service D can all independently listen to Kafka and react to that event in real-time.

> [!TIP]
> Explore a complete dockerized architecture with multiple decoupled microservices in the [Advanced Event-Driven Microservices](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Kafka/examples/05_advanced_event_driven_microservices) example.

## Interactive Examples

To help you bridge theory and practice, this guide includes several interactive examples in the `examples/` directory:
- [Basic Producer & Consumer](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Kafka/examples/01_basic_producer_consumer)
- [Intermediate Consumer Groups](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Kafka/examples/02_intermediate_consumer_groups)
- [Intermediate Schema Registry](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Kafka/examples/03_intermediate_schema_registry)
- [Advanced Exactly Once](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Kafka/examples/04_advanced_exactly_once)
- [Advanced Event-Driven Microservices](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Kafka/examples/05_advanced_event_driven_microservices)

---

## 2. Kafka Core Architecture

Unlike traditional message queues (like RabbitMQ) which delete messages immediately after they are read, **Kafka stores streams of records durably in an append-only log**. This allows many different consumers to read the same data at their own pace, and even "rewind time" to re-read old messages.

> [!TIP]
> Check out the [Basic Producer & Consumer](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Kafka/examples/01_basic_producer_consumer) example to see these building blocks in action.

```arch
node p "Producer" at 1,0 icon=client

group cluster "Kafka Cluster" color=blue
node b1 "Broker 1" at 0,1 in cluster icon=kafka-icon sub="Partition 0"
node b2 "Broker 2" at 1,1 in cluster icon=kafka-icon sub="Partition 1"
node b3 "Broker 3" at 2,1 in cluster icon=kafka-icon sub="Partition 2"

group cg "Consumer Group A" color=purple
node c1 "Consumer 1" at 0.5,2 in cg icon=worker
node c2 "Consumer 2" at 2,2 in cg icon=worker

p -> b1 : "hash(key) % 3"
p -> b2
p -> b3

b1 -> c1 : "reads"
b2 -> c1 : "reads"
b3 -> c2 : "reads"
```

### The Building Blocks
*   **Topic:** A named stream of records (events). Think of it like a table in a database.
*   **Partition:** A topic is split into multiple Partitions. This is Kafka's primary mechanism for **parallelism**. If a topic has 3 partitions, it can be processed by up to 3 consumers concurrently.
*   **Broker:** A single Kafka server. Partitions are distributed across brokers so no single server holds all the data.
*   **Producer:** An application that writes events to Kafka. It usually hashes a "key" (e.g., `user_id`) to ensure all events for the same user land in the exact same partition, guaranteeing they are processed in order.
*   **Consumer:** An application that reads events from Kafka.
*   **Consumer Group:** A set of consumers working together to process a topic. **Rule:** Each partition is assigned to exactly *one* consumer in a group.

> [!TIP]
> See how Kafka distributes partitions and guarantees ordering in the [Intermediate Consumer Groups](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Kafka/examples/02_intermediate_consumer_groups) example.

### Zookeeper vs KRaft
Historically, Kafka relied on Apache ZooKeeper to manage cluster metadata (which broker holds which partition). In modern Kafka (versions 3.3+), ZooKeeper has been replaced by **KRaft** (Kafka Raft), allowing Kafka brokers to manage their own metadata internally. This makes Kafka much easier to deploy and scale.

---

## 3. High Availability and Durability

Kafka is designed to never lose data, even if servers catch fire.

### Replication Factor
When you create a topic, you specify a **Replication Factor**. If you set it to 3, Kafka ensures that every partition is copied to 3 different brokers.
One broker acts as the **Leader** (handling all reads and writes for that partition), and the others are **Followers** (passively copying data from the Leader).

### In-Sync Replicas (ISR)
A follower is considered "In-Sync" if it is fully caught up with the Leader. If the Leader crashes, Kafka automatically promotes one of the ISRs to become the new Leader in milliseconds.

### Producer ACKs
When a Producer sends a message, it can choose how safe it wants to be:
*   `acks=0`: "Fire and forget." The producer doesn't wait for a response. Fastest, but if the broker crashes before saving, the message is lost.
*   `acks=1`: The producer waits for the Leader to write the message to its disk.
*   `acks=all`: The producer waits for the Leader *and* all ISRs to write the message. Safest, but slowest.

---

## 4. Delivery Semantics and Offsets

Consumers track their progress by committing an **offset** (an integer representing the message ID).

*   **At-most-once:** The consumer reads the message, immediately commits the offset, and *then* processes it. If it crashes during processing, the message is lost (because the offset is already saved).
*   **At-least-once:** The consumer reads the message, processes it, and *then* commits the offset. If it crashes after processing but before committing, the next consumer will re-read and re-process the message. Your processing logic **must be idempotent** (safe to run twice).
*   **Exactly-once:** Kafka provides a Transactional API to ensure a message is processed and written to a downstream Kafka topic exactly once.

> [!TIP]
> Dive into the Transaction API to prevent duplicate processing during crashes with the [Advanced Exactly Once](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Kafka/examples/04_advanced_exactly_once) example.

---

## 5. Retention and Compaction

Because Kafka is an immutable log, it doesn't delete messages when they are read. It deletes them based on policies:
*   **Time-based:** Delete messages older than 7 days (default).
*   **Size-based:** Delete the oldest messages when the partition hits 10GB.
*   **Log Compaction:** Instead of deleting by time, keep only the *latest* value for each key. This is incredibly useful for syncing database state (e.g., you only care about the user's *current* address, not their old ones).

---

## 6. Kafka vs. RabbitMQ

| Feature | Kafka (Event Stream) | RabbitMQ (Message Broker) |
|---|---|---|
| **Storage** | Durable append-only log | Transient queues (deletes on ack) |
| **Routing** | Simple topic partitions | Complex routing keys and exchanges |
| **Replayability** | Yes, rewind the offset to re-read | No, once consumed, it is gone |
| **Ordering** | Guaranteed per partition | Can be tricky with dead-letter queues |
| **Best for** | High throughput, event sourcing, stream processing | Task queues, complex routing, RPC over AMQP |

---

## 7. Essential Kafka CLI Commands

If you are SSH'd into a Kafka broker, these are the commands you use to debug:

*   **Create a topic:**
    `kafka-topics.sh --bootstrap-server localhost:9092 --create --topic my-topic --partitions 3 --replication-factor 2`
*   **List all topics:**
    `kafka-topics.sh --bootstrap-server localhost:9092 --list`
*   **Produce messages (interactive):**
    `kafka-console-producer.sh --broker-list localhost:9092 --topic my-topic`
*   **Consume messages (from the beginning):**
    `kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic my-topic --from-beginning`
*   **Check Consumer Group lag:**
    `kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group my-group` (Crucial for seeing if your consumers are falling behind the producers).

---

## 8. Real-world Code Examples (Go & Python)

### Python Example (`confluent-kafka`)

#### Producer
```python
import json
from confluent_kafka import Producer

def delivery_report(err, msg):
    """Called once for each message produced to indicate delivery result."""
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

# Configuration for the producer
conf = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'python-producer'
}

producer = Producer(conf)

topic = 'my-topic'
data = {'user_id': 123, 'action': 'login'}

# Serialize the data as JSON and encode to bytes
# Serialization is crucial because Kafka only accepts bytes
value = json.dumps(data).encode('utf-8')

# Produce the message. The key is used to ensure order within a partition.
producer.produce(topic, key=str(data['user_id']).encode('utf-8'), value=value, callback=delivery_report)

# Wait for any outstanding messages to be delivered and delivery reports to be received.
# Flush ensures that all buffered messages are sent to the broker before the script exits.
producer.flush()
```

#### Consumer
```python
import json
from confluent_kafka import Consumer, KafkaError

# Configuration for the consumer
conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'python-consumer-group',
    'auto.offset.reset': 'earliest', # Start reading from the beginning if no offset is found
    'enable.auto.commit': False # Disable auto-commit for at-least-once processing
}

consumer = Consumer(conf)
consumer.subscribe(['my-topic'])

try:
    while True:
        # Poll for new messages, waiting up to 1 second
        msg = consumer.poll(1.0)
        
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                print(f"End of partition reached {msg.topic()}/{msg.partition()}")
            else:
                print(f"Error: {msg.error()}")
            continue

        # Deserialize the message value
        value = json.loads(msg.value().decode('utf-8'))
        print(f"Received message: {value} with key {msg.key().decode('utf-8')}")

        # Commit the offset manually after processing the message (at-least-once semantics)
        # This prevents message loss if the consumer crashes before processing completes
        consumer.commit(asynchronous=False)
except KeyboardInterrupt:
    pass
finally:
    # Close down consumer to commit final offsets and leave the group cleanly
    consumer.close()
```

### Golang Example (`confluent-kafka-go`)

#### Producer
```go
package main

import (
	"fmt"
	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
)

func main() {
	p, err := kafka.NewProducer(&kafka.ConfigMap{"bootstrap.servers": "localhost:9092"})
	if err != nil {
		panic(err)
	}

	defer p.Close()

	// Delivery report handler for produced messages
	go func() {
		for e := range p.Events() {
			switch ev := e.(type) {
			case *kafka.Message:
				if ev.TopicPartition.Error != nil {
					fmt.Printf("Delivery failed: %v\n", ev.TopicPartition)
				} else {
					fmt.Printf("Delivered message to %v\n", ev.TopicPartition)
				}
			}
		}
	}()

	topic := "my-topic"
	key := "user_123"
	value := "{\"action\": \"login\"}" // In a real app, serialize a struct to JSON

	err = p.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &topic, Partition: kafka.PartitionAny},
		Key:            []byte(key),
		Value:          []byte(value),
	}, nil)

	if err != nil {
		fmt.Printf("Produce failed: %v\n", err)
	}

	// Wait for message deliveries before shutting down
	p.Flush(15 * 1000)
}
```

#### Consumer
```go
package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
)

func main() {
	c, err := kafka.NewConsumer(&kafka.ConfigMap{
		"bootstrap.servers": "localhost:9092",
		"group.id":          "go-consumer-group", // Consumer groups allow parallel processing
		"auto.offset.reset": "earliest",
		"enable.auto.commit": false, // Disable auto-commit for explicit control
	})

	if err != nil {
		panic(err)
	}

	c.SubscribeTopics([]string{"my-topic"}, nil)

	// Set up channel for graceful shutdown handling context cancellation
	sigchan := make(chan os.Signal, 1)
	signal.Notify(sigchan, syscall.SIGINT, syscall.SIGTERM)

	run := true
	for run {
		select {
		case sig := <-sigchan:
			fmt.Printf("Caught signal %v: terminating\n", sig)
			run = false
		default:
			ev := c.Poll(100)
			if ev == nil {
				continue
			}

			switch e := ev.(type) {
			case *kafka.Message:
				fmt.Printf("Message on %s: %s\n", e.TopicPartition, string(e.Value))
				// Manually commit offsets after successful processing (at-least-once)
				_, err := c.CommitMessage(e)
				if err != nil {
					fmt.Printf("Error committing offset: %v\n", err)
				}
			case kafka.Error:
				// Generic errors
				fmt.Fprintf(os.Stderr, "%% Error: %v\n", e)
				if e.Code() == kafka.ErrAllBrokersDown {
					run = false
				}
			}
		}
	}

	fmt.Printf("Closing consumer\n")
	c.Close()
}
```

---

## 9. Interview Questions

### 1. What is the difference between a Topic and a Partition?
**Answer:** A Topic is a logical category or feed name to which records are published. A Partition is the physical manifestation of a Topic. A Topic is split into multiple Partitions, which are distributed across different brokers to allow parallel processing and fault tolerance. 

### 2. How does Kafka guarantee message ordering?
**Answer:** Kafka only guarantees message ordering **within a single partition**. It does not guarantee global ordering across the entire topic. To ensure all events for a specific entity (like a `user_id` or `order_id`) are processed in order, the Producer must set that ID as the message "Key". Kafka hashes the key and ensures all messages with the same key are written to the exact same partition.

### 3. What happens if you have 4 consumers in a group, but the topic only has 3 partitions?
**Answer:** Each partition can only be assigned to one consumer within a specific consumer group. Therefore, 3 consumers will read from 1 partition each, and the 4th consumer will sit idle. It will only start processing if one of the other 3 consumers crashes.

### 4. What is a Consumer Group Rebalance?
**Answer:** A rebalance occurs when the number of partitions changes (a topic is expanded) or when the number of consumers changes (a consumer crashes, or a new one scales up). Kafka temporarily pauses consumption, revokes all partition assignments, and reassigns the partitions fairly among the currently active consumers in the group. During a rebalance, processing is temporarily halted.

### 5. Explain what "Lag" means in Kafka.
**Answer:** Lag is the difference between the latest message produced to a partition (the Log End Offset, or LEO) and the last message committed by the consumer (the Current Offset). A growing lag means the Producer is writing data faster than the Consumer can process it. You fix this by optimizing the consumer code or adding more partitions and scaling up the number of consumers.

### 6. What is the Schema Registry and why is it important?
**Answer:** In a large company, Producers and Consumers might be written by different teams in different languages. If a Producer changes the JSON structure of an event, the Consumer might crash. The Confluent Schema Registry forces Producers to serialize events using a strict, versioned schema (like Avro or Protobuf). Consumers fetch the schema to deserialize the event. If a Producer tries to send an event that breaks backwards compatibility, the Schema Registry rejects it.

> [!TIP]
> Learn to enforce strict payload structures using Avro and the Confluent Schema Registry in the [Intermediate Schema Registry](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Kafka/examples/03_intermediate_schema_registry) example.

### 7. What is Log Compaction?
**Answer:** Normally, Kafka deletes old messages based on time (e.g., after 7 days). Log Compaction is an alternative retention policy where Kafka ensures that it always retains at least the *last known value* for each message key within the log. It deletes older records with the same key. This is highly useful for rebuilding the current state of a system (e.g., a cache or a database replica) from the Kafka log.

### 8. What is the role of ZooKeeper in older Kafka clusters?
**Answer:** ZooKeeper was responsible for managing the cluster's metadata. It kept track of which brokers were alive, which broker was the Leader for which partition, and handled leader election if a broker died. (Note: Modern Kafka has replaced ZooKeeper with KRaft, internalizing this metadata management).

### 9. What does `acks=all` mean?
**Answer:** It is a producer configuration that guarantees the highest level of durability. When a producer sends a message with `acks=all`, the Leader broker will not acknowledge the write until the message has been written to the Leader's disk *and* fully replicated to all In-Sync Replicas (ISRs). This ensures the message is not lost even if the Leader broker completely fails immediately after acknowledging the write.

### 10. How can you implement a "Dead Letter Queue" (DLQ) in Kafka?
**Answer:** Unlike RabbitMQ, Kafka does not have built-in DLQs. If a consumer encounters a "poison pill" message it cannot parse, it will crash and infinitely retry reading the same offset. To implement a DLQ, the consumer application must catch the parsing exception, manually publish the bad message to a separate Kafka topic (e.g., `my-topic-dlq`), and then intentionally commit the offset on the main topic to move past the bad message.
