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
