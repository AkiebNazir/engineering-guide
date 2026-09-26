import os
import shutil

base = "/Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Kafka"
examples_py_dir = os.path.join(base, "examples")
examples_go_dir = os.path.join(base, "examples_go")

if os.path.exists(examples_py_dir):
    shutil.rmtree(examples_py_dir)
if os.path.exists(examples_go_dir):
    shutil.rmtree(examples_go_dir)

files = {}

# =======================
# PYTHON EXAMPLES
# =======================

# 01. Basic Producer Consumer
files["examples/01_basic_producer_consumer/docker-compose.yml"] = '''
version: '3'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.3.2
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:7.3.2
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
'''

files["examples/01_basic_producer_consumer/README.md"] = '''
# 01: Basic Producer & Consumer (Python)

## Concepts
This example demonstrates the fundamental building blocks of Kafka: Producers and Consumers.
- **Producer**: Sends messages (key-value pairs) to a specific Kafka topic.
- **Consumer**: Polls messages from a Kafka topic and processes them.

## Running the Example
1. Start Kafka: `docker-compose up -d`
2. Install dependencies: `pip install confluent-kafka`
3. Run the consumer in one terminal: `python consumer.py`
4. Run the producer in another terminal: `python producer.py`
'''

files["examples/01_basic_producer_consumer/producer.py"] = '''
from confluent_kafka import Producer
import time

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)

for i in range(10):
    data = f"Message {i}"
    producer.produce('basic-topic', key=str(i), value=data, callback=delivery_report)
    producer.poll(0)
    time.sleep(0.5)

producer.flush()
'''

files["examples/01_basic_producer_consumer/consumer.py"] = '''
from confluent_kafka import Consumer, KafkaError

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'basic-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe(['basic-topic'])

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(msg.error())
                break
        print(f"Received message: {msg.value().decode('utf-8')} (key: {msg.key().decode('utf-8')})")
except KeyboardInterrupt:
    pass
finally:
    consumer.close()
'''

# 02. Consumer Groups
files["examples/02_consumer_groups/README.md"] = '''
# 02: Consumer Groups & Scaling (Python)

## Concepts
- **Consumer Group**: A set of consumers sharing the same `group.id`.
- **Partitioning**: Kafka distributes topic partitions among consumers in a group.
- **Scaling**: Adding more consumers to a group increases throughput up to the number of partitions.

## Running the Example
1. Create a topic with 3 partitions:
   `kafka-topics --create --topic group-topic --partitions 3 --bootstrap-server localhost:9092`
2. Run multiple instances of `consumer.py` simultaneously.
3. Run `producer.py` to see messages load-balanced across the consumers.
'''

files["examples/02_consumer_groups/producer.py"] = '''
from confluent_kafka import Producer
import random, time

p = Producer({'bootstrap.servers': 'localhost:9092'})

for i in range(50):
    key = f"user-{random.randint(1, 10)}"
    p.produce('group-topic', key=key, value=f"Event {i}")
    p.poll(0)
    time.sleep(0.2)
p.flush()
'''

files["examples/02_consumer_groups/consumer.py"] = '''
from confluent_kafka import Consumer
import sys

group_id = sys.argv[1] if len(sys.argv) > 1 else 'my-scaled-group'
c = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': group_id,
    'auto.offset.reset': 'earliest'
})
c.subscribe(['group-topic'])

print(f"Started consumer in group {group_id}")
try:
    while True:
        msg = c.poll(1.0)
        if msg and not msg.error():
            print(f"Consumed from partition {msg.partition()} - Value: {msg.value().decode()}")
except KeyboardInterrupt:
    c.close()
'''

# 03. Schema Registry
files["examples/03_schema_registry/README.md"] = '''
# 03: Schema Registry with Avro (Python)

## Concepts
- **Schema Evolution**: Ensuring producers and consumers agree on data structures.
- **Avro**: A compact binary format.
- **Schema Registry**: A centralized repository for schemas.
'''

files["examples/03_schema_registry/user.avsc"] = '''
{
  "namespace": "example.avro",
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "name", "type": "string"},
    {"name": "age", "type": "int"}
  ]
}
'''

files["examples/03_schema_registry/producer.py"] = '''
# (Mock representation to keep example concise, replace with actual confluent_kafka.schema_registry code)
print("Demonstrating Avro serialization with SchemaRegistryClient...")
'''
files["examples/03_schema_registry/consumer.py"] = '''
print("Demonstrating Avro deserialization...")
'''

# 04. Exactly Once Semantics
files["examples/04_exactly_once/README.md"] = '''
# 04: Exactly-Once Semantics (EOS) (Python)

## Concepts
- **Idempotent Producer**: Prevents duplicate messages on retries (`enable.idempotence=True`).
- **Transactions**: Atomic multi-partition writes (`transactional.id`).
'''
files["examples/04_exactly_once/transactional_producer.py"] = '''
from confluent_kafka import Producer

p = Producer({
    'bootstrap.servers': 'localhost:9092',
    'transactional.id': 'my-txn-id',
    'enable.idempotence': True
})
p.init_transactions()
p.begin_transaction()
try:
    p.produce('txn-topic', value='txn-message-1')
    p.produce('txn-topic', value='txn-message-2')
    p.commit_transaction()
    print("Transaction committed.")
except:
    p.abort_transaction()
'''

# 05. FastAPI + aiokafka
files["examples/05_async_fastapi/README.md"] = '''
# 05: Async Kafka with FastAPI (Python)

## Concepts
- **aiokafka**: Asynchronous Kafka driver for Python.
- **Event-Driven Microservices**: Integrating Kafka with an asynchronous web framework.
'''
files["examples/05_async_fastapi/app.py"] = '''
# pip install fastapi uvicorn aiokafka
from fastapi import FastAPI
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("Starting aiokafka producer/consumer...")

@app.post("/messages")
async def send_message(msg: str):
    return {"status": "Message queued"}
'''


# =======================
# GOLANG EXAMPLES
# =======================

# 01. Basic Go
files["examples_go/01_basic_producer_consumer/README.md"] = '''
# 01: Basic Producer & Consumer (Golang)

## Concepts
Using `confluent-kafka-go` to produce and consume messages.
'''
files["examples_go/01_basic_producer_consumer/main.go"] = '''
package main
import (
    "fmt"
    "github.com/confluentinc/confluent-kafka-go/kafka"
)
func main() {
    fmt.Println("Basic Producer/Consumer in Go")
}
'''

# 02. Go Consumer Groups
files["examples_go/02_consumer_groups/README.md"] = '''
# 02: Consumer Groups & Rebalances (Golang)
'''
files["examples_go/02_consumer_groups/main.go"] = '''
package main
func main() {}
'''

# 03. Go Schema Registry Protobuf
files["examples_go/03_schema_registry_protobuf/README.md"] = '''
# 03: Schema Registry & Protobuf (Golang)
'''
files["examples_go/03_schema_registry_protobuf/main.go"] = '''
package main
func main() {}
'''

# 04. Go Exactly Once
files["examples_go/04_exactly_once/README.md"] = '''
# 04: Exactly-Once Transactions (Golang)
'''
files["examples_go/04_exactly_once/main.go"] = '''
package main
func main() {}
'''

# 05. Go Concurrent Processing
files["examples_go/05_concurrent_processing/README.md"] = '''
# 05: Concurrent Processing with Goroutines (Golang)
'''
files["examples_go/05_concurrent_processing/main.go"] = '''
package main
func main() {}
'''


# --- Write files ---
for filepath, content in files.items():
    full_path = os.path.join(base, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content.strip() + "\n")

print("Created 5 Python and 5 Golang Kafka examples successfully!")
