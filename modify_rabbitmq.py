import re

with open('/Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/RabbitMQ.md', 'r') as f:
    content = f.read()

# Add Interactive Examples
examples_section = """
## Interactive Examples

We provide several practical examples in the `examples/` directory to help you understand RabbitMQ concepts hands-on:
- [01 Basic Queue](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/01_basic_queue)
- [02 Basic Worker Queue](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/02_basic_worker_queue)
- [03 Intermediate PubSub Fanout](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/03_intermediate_pubsub_fanout)
- [04 Intermediate Routing Topic](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/04_intermediate_routing_topic)
- [05 Advanced DLX TTL](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/05_advanced_dlx_ttl)

"""
content = content.replace("## AMQP Architecture", examples_section + "## AMQP Architecture")

# Replace architecture diagram
arch_diagram = """```arch
node pub "Publisher" at 0,1 icon=client
node exch "Direct Exchange" at 1,1 icon=network
node q1 "Queue: errors" at 2,0 icon=db
node q2 "Queue: logs" at 2,2 icon=db
node work1 "Worker 1" at 3,0 icon=worker
node work2 "Worker 2" at 3,2 icon=worker

pub -> exch
exch -> q1 : "routing_key=error"
exch -> q2 : "routing_key=info"
q1 -> work1
q2 -> work2
```"""

mermaid_diagram = """```mermaid
flowchart TD
    pub("Publisher")
    exch{"Direct Exchange"}
    q1[("Queue: errors")]
    q2[("Queue: logs")]
    work1("Worker 1")
    work2("Worker 2")

    pub --> exch
    exch -->|"routing_key=error"| q1
    exch -->|"routing_key=info"| q2
    q1 --> work1
    q2 --> work2
```"""
content = content.replace(arch_diagram, mermaid_diagram)

# Add tips
content = content.replace("3. **Queues**: Buffers that store messages. Consumers receive messages from queues.", "3. **Queues**: Buffers that store messages. Consumers receive messages from queues.\n   > [!TIP]\n   > Check out the [Basic Queue example](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/01_basic_queue) and [Worker Queue example](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/02_basic_worker_queue) to see this in action.")
content = content.replace("* **Topic**: Routes messages to one or many queues based on a wildcard match between the routing key and the routing pattern specified in the binding.", "* **Topic**: Routes messages to one or many queues based on a wildcard match between the routing key and the routing pattern specified in the binding.\n  > [!TIP]\n  > See the [Routing Topic example](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/04_intermediate_routing_topic) for wildcard routing.")
content = content.replace("* **Fanout**: Broadcasts all messages it receives to all queues it knows about (routing keys are ignored).", "* **Fanout**: Broadcasts all messages it receives to all queues it knows about (routing keys are ignored).\n  > [!TIP]\n  > See the [PubSub Fanout example](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/03_intermediate_pubsub_fanout) for broadcasting messages.")
content = content.replace("## Dead Letter Exchanges (DLX) and Message TTL", "## Dead Letter Exchanges (DLX) and Message TTL\n\n> [!TIP]\n> Try the [Advanced DLX TTL example](file:///Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/examples/05_advanced_dlx_ttl) to handle failed messages and expirations.")


with open('/Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ/RabbitMQ.md', 'w') as f:
    f.write(content)

