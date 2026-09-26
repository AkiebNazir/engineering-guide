import os
import json
import logging
from confluent_kafka import Consumer, KafkaException, KafkaError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_consumer(brokers: str, group_id: str) -> Consumer:
    """Create and return a Kafka Consumer instance."""
    conf = {
        'bootstrap.servers': brokers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    }
    return Consumer(conf)

def process_cdc_event(event_value: bytes):
    """Process a single CDC event."""
    try:
        payload = json.loads(event_value.decode('utf-8'))
        op = payload.get("op") # typical Debezium op code: 'c' (create), 'u' (update), 'd' (delete)
        if op in ['c', 'u']:
            logging.info(f"Event detected (INSERT/UPDATE): {payload}")
        elif op == 'd':
            logging.info(f"Event detected (DELETE): {payload}")
    except json.JSONDecodeError:
        logging.warning(f"Could not parse event as JSON: {event_value}")

def main():
    logging.info('Starting Data Engineering Project: 03_cdc_log_tailer (Kafka Consumer)')
    
    brokers = os.getenv("KAFKA_BROKERS", "localhost:9092")
    topic = os.getenv("KAFKA_CDC_TOPIC", "dbserver1.inventory.customers")
    group_id = os.getenv("KAFKA_GROUP_ID", "cdc-tailer-group")
    
    consumer = create_consumer(brokers, group_id)
    consumer.subscribe([topic])
    
    logging.info(f"Subscribed to topic {topic}. Waiting for events...")
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition
                    continue
                else:
                    raise KafkaException(msg.error())
            
            # Process event
            process_cdc_event(msg.value())
            
            # Commit offsets manually after processing for at-least-once delivery
            consumer.commit(asynchronous=False)
            
    except KeyboardInterrupt:
        logging.info("Stopping CDC consumer...")
    except Exception as e:
        logging.error("Consumer error", exc_info=True)
    finally:
        consumer.close()

if __name__ == '__main__':
    main()
