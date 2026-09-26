# 01: Basic Producer & Consumer (Python)

## Concepts
This example demonstrates the fundamental building blocks of Kafka: Producers and Consumers.
- **Producer**: Sends messages (key-value pairs) to a specific Kafka topic.
- **Consumer**: Polls messages from a Kafka topic and processes them.

## Running the Example
1. Start Kafka: `docker-compose up -d`
2. Install dependencies: `pip install confluent-kafka`
3. Run the consumer in one terminal: `python consumer.py`
4. Run the producer in another terminal: `python producer.py`
