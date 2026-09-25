# Advanced Exactly-Once Semantics (Transactions)

**Goal:** Demonstrates how to achieve Exactly-Once semantics using Kafka's Transaction API in Python to atomically read from one topic, process the message, and write it to another topic, preventing duplicate processing if a crash occurs.

**Key Concepts:** [Delivery Semantics and Offsets](../Kafka.md#4-delivery-semantics-and-offsets) (Exactly-once).

**Prerequisites:** 
- A local Kafka cluster running on `localhost:9092`
- Python 3 installed
- Install dependencies: `pip install confluent-kafka`

**Step-by-Step Execution:** 
1. Ensure your local Kafka cluster is running.
2. Run the transactional processor script:
   ```bash
   python processor.py
   ```
3. (In a separate terminal) Produce some messages to the `input-topic` (e.g. using `kafka-console-producer.sh`).
4. **Expected Output:** The script will read messages, convert their contents to uppercase, and atomically commit the consumer offset and the output message to the `output-topic`. You will see `Transaction committed successfully.` for each processed batch.

**Try it yourself:** Simulate a failure by throwing an exception inside the `try` block before `producer.commit_transaction()`. Notice how `producer.abort_transaction()` prevents the output from being visible in `output-topic` and keeps the consumer offset unchanged, allowing exactly-once reprocessing when the script restarts.

**Teardown:** Stop the script with `Ctrl+C`.
