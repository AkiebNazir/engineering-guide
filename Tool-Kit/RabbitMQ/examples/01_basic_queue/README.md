# 01 Basic Queue (Python)

**Goal:** Demonstrates the simplest form of RabbitMQ messaging with a single producer sending a message to a single consumer via a default exchange and a named queue.

**Deep Concept Explanation:**
In RabbitMQ, a producer never sends messages directly to a queue. It sends messages to an *exchange*. However, in this basic example, we use the default exchange (identified by an empty string `""`). The default exchange implicitly routes messages to the queue with the exact name specified in the routing key.

**Prerequisites:** 
- RabbitMQ running: `docker run -d --name rabbitmq -p 5672:5672 rabbitmq`
- Python installed. Initialize: `pip install pika`

**Execution:** 
1. Start the consumer: `python consumer.py`
2. Run the producer: `python producer.py`\n