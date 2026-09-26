from confluent_kafka import Producer
import random, time

p = Producer({'bootstrap.servers': 'localhost:9092'})

for i in range(50):
    key = f"user-{random.randint(1, 10)}"
    p.produce('group-topic', key=key, value=f"Event {i}")
    p.poll(0)
    time.sleep(0.2)
p.flush()
