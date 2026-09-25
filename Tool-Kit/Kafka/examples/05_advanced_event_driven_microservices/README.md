# Advanced Event-Driven Microservices

**Goal:** Completely encapsulates the power of Kafka by showing how multiple independent microservices can react to the same event stream without tightly coupling their APIs.

**Key Concepts:** [Event Streaming Paradigm](../Kafka.md#1-ground-zero-what-is-event-streaming) and [Consumer Groups](../Kafka.md#the-building-blocks).

**Prerequisites:** 
- Docker and Docker Compose installed

**Step-by-Step Execution:** 
1. Build and run all services using Docker Compose:
   ```bash
   docker-compose up --build
   ```
2. **Expected Output:** 
   - The **Order Service** creates an order and drops an `OrderCreated` event into Kafka.
   - The **Inventory Service** (with its own `group.id`) listens and deducts stock independently.
   - The **Notification Service** (with a different `group.id`) listens and sends an email.
   - Both the Inventory and Notification services process the exact same event in parallel, demonstrating pub/sub event streaming decoupling.

**Try it yourself:** Stop the Notification Service container (`docker-compose stop notification-service`), produce a few more orders, and then restart the Notification Service. Watch it catch up on missed events instantly from where it left off, proving Kafka's durable stream replayability!

**Teardown:** 
1. Stop and remove all containers and their volumes:
   ```bash
   docker-compose down -v
   ```
