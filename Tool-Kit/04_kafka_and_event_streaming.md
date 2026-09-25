# Kafka and Event Streaming

Apache Kafka is an event streaming platform. Unlike traditional message queues which delete messages after they are read, Kafka stores streams of records durably in an append-only log, allowing many consumers to read the same data at their own pace.

## 1. The Core Architecture

```arch
%% caption: Kafka partitions topics across brokers; consumer groups allow parallel processing of partitions.
group cluster "Kafka Cluster" color=slate style=dashed
node b1 "Broker 1\\n(Partition 0)" at 0,1 in cluster icon=server color=blue
node b2 "Broker 2\\n(Partition 1)" at 2,1 in cluster icon=server color=blue
node b3 "Broker 3\\n(Partition 2)" at 4,1 in cluster icon=server color=blue

node p "Producer" at 2,0 icon=client color=amber

group cg "Consumer Group A" color=slate style=dashed
node c1 "Consumer 1" at 0,2 in cg icon=worker color=green
node c2 "Consumer 2" at 4,2 in cg icon=worker color=green

p -> b1 : "hash(key) % 3"
p -> b2
p -> b3

b1 -> c1 : "reads"
b2 -> c1 : "reads"
b3 -> c2 : "reads"
```

- **Topic**: A named stream of records. Think of it like a table in a database.
- **Partition**: Topics are split into partitions. This is the unit of parallelism. If a topic has 3 partitions, it can be processed by at most 3 consumers concurrently in the same group.
- **Broker**: A single Kafka server. Partitions are distributed across brokers.
- **Producer**: An application that writes events to Kafka. It usually hashes a "key" (e.g., `user_id`) to ensure all events for the same user land in the same partition, guaranteeing order.
- **Consumer Group**: A set of consumers working together to process a topic. Each partition is assigned to exactly *one* consumer in the group.

## 2. Retention and Compaction

Because Kafka is a log, it doesn't delete messages when read. It deletes them based on policies:
- **Time-based**: Delete messages older than 7 days.
- **Size-based**: Delete the oldest messages when the partition hits 10GB.
- **Log Compaction**: Instead of deleting by time, keep only the *latest* value for each key (useful for syncing database state).

## 3. Delivery Semantics and Offsets

Consumers track their progress by committing an **offset** (an integer representing the message ID).

- **At-most-once**: The consumer reads the message, immediately commits the offset, and *then* processes it. If it crashes during processing, the message is lost.
- **At-least-once**: The consumer reads the message, processes it, and *then* commits the offset. If it crashes after processing but before committing, the next consumer will re-read and re-process the message (requires idempotent processing).
- **Exactly-once**: Kafka provides a Transactional API to ensure a message is processed and written to an output topic exactly once.

## 4. Kafka vs. RabbitMQ

| Feature | Kafka (Event Stream) | RabbitMQ (Message Broker) |
|---|---|---|
| **Storage** | Durable append-only log | Transient queues (deletes on ack) |
| **Routing** | Simple topic partitions | Complex routing keys and exchanges |
| **Replayability** | Yes, rewind the offset to re-read | No, once consumed, it is gone |
| **Ordering** | Guaranteed per partition | Can be tricky with dead-letter queues |
| **Best for** | High throughput, event sourcing, stream processing | Task queues, complex routing, RPC over AMQP |

## 5. The Schema Registry

In a large company, Producers and Consumers might be written by different teams in different languages. If a Producer changes the JSON structure of an event, the Consumer might crash.

The **Confluent Schema Registry** forces Producers to serialize events using a strict schema (like Avro or Protobuf) and register it. Consumers fetch the schema to deserialize the event. If a Producer tries to send an event that breaks backwards compatibility, the Schema Registry rejects it.
