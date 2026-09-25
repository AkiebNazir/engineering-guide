import os

base_dir = '/Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples'

readmes = {
    '01_basic_queue': """# 01 Basic Queue

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
""",
    
    '02_basic_worker_queue': """# 02 Basic Worker Queue

**Goal:** Demonstrates how to distribute time-consuming tasks among multiple workers (competing consumers pattern).

**Key Concepts:** [Message Acknowledgment and Queues](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/RabbitMQ.md)

**Prerequisites:** 
- RabbitMQ running (e.g., via `docker-compose up -d` in the `examples/` root)
- Python 3 and `pika` library installed (`pip install pika`)

**Step-by-Step Execution:** 
1. Open two terminals and start a worker in each:
   ```bash
   python worker.py
   ```
2. Open a third terminal and publish some tasks:
   ```bash
   python new_task.py "First message."
   python new_task.py "Second message.."
   python new_task.py "Third message..."
   ```
   *Note: Dots represent the number of seconds the task will take.*
3. Observe how RabbitMQ distributes the messages between the two workers (round-robin by default).

**Try it yourself:** Stop one of the workers while it is processing a task (using `CTRL+C`). Notice how the unacknowledged message is requeued and picked up by the other worker.

**Teardown:** Stop all workers with `CTRL+C`.
""",

    '03_intermediate_pubsub_fanout': """# 03 Intermediate Pub/Sub Fanout

**Goal:** Demonstrates the publish/subscribe pattern where one message is broadcast to multiple consumers using a `fanout` exchange.

**Key Concepts:** [Fanout Exchange](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/RabbitMQ.md)

**Prerequisites:** 
- RabbitMQ running
- Python 3 and `pika` installed

**Step-by-Step Execution:** 
1. Open two or more terminals and start a receiver in each:
   ```bash
   python receive_logs.py
   ```
2. Open another terminal and emit a log message:
   ```bash
   python emit_log.py "System is booting up..."
   ```
3. Observe that *all* receivers get the broadcasted message.

**Try it yourself:** Start a new `receive_logs.py` instance *after* emitting a log. Does it get the old logs? (Hint: No, fanout only sends to currently bound queues).

**Teardown:** Stop all receivers with `CTRL+C`.
""",

    '04_intermediate_routing_topic': """# 04 Intermediate Routing Topic

**Goal:** Demonstrates complex routing using a `topic` exchange, where messages are routed to queues based on wildcard matching of routing keys.

**Key Concepts:** [Topic Exchange](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/RabbitMQ.md)

**Prerequisites:** 
- RabbitMQ running
- Python 3 and `pika` installed

**Step-by-Step Execution:** 
1. Start a receiver listening for all database logs:
   ```bash
   python receive_logs_topic.py "*.db"
   ```
2. Start another receiver listening only for errors:
   ```bash
   python receive_logs_topic.py "error.*"
   ```
3. Emit a database error log:
   ```bash
   python emit_log_topic.py "error.db" "A critical database error occurred!"
   ```
   *Both receivers should get this message.*
4. Emit a general database info log:
   ```bash
   python emit_log_topic.py "info.db" "Database connection established."
   ```
   *Only the first receiver should get this message.*

**Try it yourself:** Try routing keys like `error.auth` or `warning.db` and see which receivers pick them up.

**Teardown:** Stop all receivers with `CTRL+C`.
""",

    '05_advanced_dlx_ttl': """# 05 Advanced DLX TTL

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
"""
}

for folder, content in readmes.items():
    path = os.path.join(base_dir, folder, 'README.md')
    with open(path, 'w') as f:
        f.write(content)

