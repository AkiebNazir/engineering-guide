import json
import time
from kafka import KafkaProducer

def get_producer():
    return KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def produce_events():
    producer = get_producer()
    topic = 'test_topic'
    
    for i in range(1, 11):
        event = {
            'event_id': i,
            'type': 'page_view',
            'timestamp': time.time()
        }
        print(f"Producing event: {event}")
        producer.send(topic, event)
        time.sleep(1)
        
    producer.flush()
    print("Finished producing events.")

if __name__ == "__main__":
    produce_events()
