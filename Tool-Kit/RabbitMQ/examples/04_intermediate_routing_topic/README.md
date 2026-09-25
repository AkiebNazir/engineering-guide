# 04 Intermediate Routing Topic

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
