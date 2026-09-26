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
