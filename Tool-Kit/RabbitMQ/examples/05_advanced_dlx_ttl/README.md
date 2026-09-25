# 05 Advanced DLX TTL

**Goal:** Demonstrates how to use Dead Letter Exchanges (DLX) and Message Time-To-Live (TTL) to handle expired or rejected messages.

**Key Concepts:** [Dead Letter Exchanges (DLX) and Message TTL](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/RabbitMQ.md)

**Prerequisites:** 
- RabbitMQ running
- Python 3 and `pika` installed

**Step-by-Step Execution:** 
1. Start the consumer which listens on the Dead Letter Queue (DLQ):
   ```bash
   python consumer.py
   ```
2. In another terminal, run the producer to send a message with a 3-second TTL:
   ```bash
   python producer.py
   ```
3. Observe the consumer terminal. After exactly 3 seconds, the message will expire from the main queue and arrive in the DLQ, where the consumer will print it.

**Try it yourself:** Modify the TTL in `producer.py` or try rejecting a message using `basic_reject(requeue=False)` to see it immediately dead-lettered.

**Teardown:** Stop the consumer with `CTRL+C`.
