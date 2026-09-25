# 01 Basic Queue

**Goal:** Demonstrates the simplest form of RabbitMQ messaging with a single producer sending a message to a single consumer via a direct queue.

**Key Concepts:** [Queues and Publishers](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/RabbitMQ.md)

**Prerequisites:** 
- RabbitMQ running (e.g., via `docker-compose up -d` in the `examples/` root)
- Python 3 and `pika` library installed (`pip install pika`)

**Step-by-Step Execution:** 
1. Open a terminal and start the consumer:
   ```bash
   python consumer.py
   ```
   *Expected output: `[*] Waiting for messages. To exit press CTRL+C`*
2. Open a second terminal and run the producer:
   ```bash
   python producer.py
   ```
   *Expected output: `[x] Sent 'Hello World!'`*
3. Check the first terminal.
   *Expected output: `[x] Received b'Hello World!'`*

**Try it yourself:** Modify `producer.py` to send a different message or send multiple messages in a loop.

**Teardown:** Stop the consumer with `CTRL+C`. Stop RabbitMQ if no longer needed.
