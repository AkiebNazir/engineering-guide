# 03 Intermediate Pub/Sub Fanout

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
