# Intermediate Schema Registry (Avro)

**Goal:** Demonstrates how to use Confluent Schema Registry with Kafka to enforce a strict Avro schema on JSON payloads, preventing breaking changes between producers and consumers.

**Key Concepts:** [Schema Registry](../Kafka.md#9-interview-questions) (Question 6)

**Prerequisites:** 
- Docker and Docker Compose installed
- Python 3 installed
- Install dependencies: `pip install confluent-kafka[avro]`

**Step-by-Step Execution:** 
1. Spin up Kafka and the Schema Registry using Docker:
   ```bash
   docker-compose up -d
   ```
2. Run the producer script:
   ```bash
   python producer.py
   ```
3. **Expected Output:** The script reads the `user_schema.avsc` schema file, registers it, validates the Python dictionary against it, serializes it to compressed bytes, and successfully sends it to Kafka. You should see a success message like: `Success! Schema Registry validated and serialized the event.`

**Try it yourself:** Modify the `user_data` in `producer.py` to include an invalid type (e.g., change `favorite_number` to a string like `"forty-two"`) and run the script again. Observe how the Schema Registry immediately rejects it and raises a serialization error.

**Teardown:** 
1. Stop the Kafka cluster and Schema Registry:
   ```bash
   docker-compose down
   ```
