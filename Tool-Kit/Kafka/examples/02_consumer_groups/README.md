# 02: Consumer Groups & Scaling (Python)

## Concepts
- **Consumer Group**: A set of consumers sharing the same `group.id`.
- **Partitioning**: Kafka distributes topic partitions among consumers in a group.
- **Scaling**: Adding more consumers to a group increases throughput up to the number of partitions.

## Running the Example
1. Create a topic with 3 partitions:
   `kafka-topics --create --topic group-topic --partitions 3 --bootstrap-server localhost:9092`
2. Run multiple instances of `consumer.py` simultaneously.
3. Run `producer.py` to see messages load-balanced across the consumers.
