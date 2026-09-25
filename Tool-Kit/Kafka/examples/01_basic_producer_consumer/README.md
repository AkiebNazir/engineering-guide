# Basic Producer & Consumer

**Goal:** Demonstrates the fundamental API to send and receive string messages to and from Kafka using Python's `confluent-kafka` library.

**Key Concepts:** [Kafka Core Architecture](../Kafka.md#2-kafka-core-architecture) (Producers and Consumers).

**Prerequisites:** 
- A local Kafka cluster running on `localhost:9092` (e.g., via Docker)
- Python 3 installed
- Install dependencies: `pip install confluent-kafka`

**Step-by-Step Execution:** 
1. Open two terminal windows.
2. In the first terminal, start the consumer script to listen for messages:
   ```bash
   python consumer.py
   ```
3. In the second terminal, run the producer script to send messages:
   ```bash
   python producer.py
   ```
4. **Expected Output:** The consumer terminal should print out messages such as `Received message: Hello Kafka <number>` in real-time as the producer sends them.

**Try it yourself:** Change the `group.id` in `consumer.py` to a brand new string, restart the consumer, and watch it read all the messages from the beginning again (this works thanks to `auto.offset.reset: earliest`).

**Teardown:** Stop both scripts by pressing `Ctrl+C`.
