# 02 Worker Queue (Python)

**Goal:** Distributes time-consuming tasks among multiple workers.

**Deep Concept Explanation:**
Worker Queues (or Task Queues) are used to distribute time-consuming tasks among multiple workers to avoid running resource-intensive tasks synchronously. 
RabbitMQ dispatches messages to consumers using **Round-Robin** by default. We use `channel.basic_qos(prefetch_count=1)` to tell RabbitMQ not to give more than one message to a worker at a time, ensuring fair dispatch.\n