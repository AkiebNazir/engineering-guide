import json
from kafka import KafkaConsumer

def consume_events():
    consumer = KafkaConsumer(
        'test_topic',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='my-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    print("Listening for messages on 'test_topic'...")
    for message in consumer:
        event = message.value
        print(f"Consumed event: {event}")

if __name__ == "__main__":
    consume_events()
