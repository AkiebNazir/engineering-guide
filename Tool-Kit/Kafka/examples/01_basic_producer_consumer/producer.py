from confluent_kafka import Producer
import time

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

p = Producer({'bootstrap.servers': 'localhost:9092'})

for i in range(5):
    # Trigger any available delivery report callbacks from previous produce() calls
    p.poll(0)
    data = f"Hello Kafka {i}"
    # Asynchronously produce a message. The delivery report callback will be triggered when the message has been successfully delivered or failed permanently.
    p.produce('basic-topic', data.encode('utf-8'), callback=delivery_report)
    time.sleep(1)

# Wait for any outstanding messages to be delivered and delivery report callbacks to be triggered.
p.flush()
