# 02 Basic Worker Queue

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
