# Consumer Groups & Partitions

**Goal:** Demonstrates how Kafka scales by distributing topic partitions across multiple consumers within the same consumer group, ensuring guaranteed message ordering by key using Golang.

**Key Concepts:** [Consumer Groups](../Kafka.md#the-building-blocks) and [Delivery Semantics](../Kafka.md#4-delivery-semantics-and-offsets).

**Prerequisites:** 
- Docker and Docker Compose installed
- Go installed
- Initialize the Go module and install dependencies (e.g., `go mod init example` and `go get github.com/segmentio/kafka-go`)

**Step-by-Step Execution:** 
1. Start the local Kafka cluster using the provided Docker compose file:
   ```bash
   docker-compose up -d
   ```
2. Run the Go application which spawns multiple consumers and a producer:
   ```bash
   go run main.go
   ```
3. **Expected Output:** You will see 3 consumers spinning up in the same group. The producer sends messages using a "User ID" as the Kafka Key. Notice how Kafka ensures that all messages for a specific user (e.g., `user-1`) are consistently routed to the exact same partition, and therefore processed by the exact same consumer, guaranteeing order!

**Try it yourself:** Change the number of consumers created in `main.go` from 3 to 4. Notice that the 4th consumer stays idle because there are only 3 partitions. If you kill one of the active consumers, the 4th one will take over during the rebalance.

**Teardown:** 
1. Stop the application with `Ctrl+C`.
2. Stop the Kafka cluster:
   ```bash
   docker-compose down
   ```
