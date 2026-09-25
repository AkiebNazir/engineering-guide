from confluent_kafka import Producer
import json
import time

p = Producer({'bootstrap.servers': 'kafka:9092'})
order_id = 1

while True:
    event = {"order_id": order_id, "item": "Laptop", "price": 1200}
    p.produce('orders-topic', key=str(order_id), value=json.dumps(event))
    p.flush()
    print(f"[Order Service] Created Order {order_id}")
    order_id += 1
    time.sleep(3)
