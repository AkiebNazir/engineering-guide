from confluent_kafka import Producer, Consumer, KafkaError
import time

# To achieve EXACTLY ONCE semantics in Kafka, you read from Topic A, 
# process the data, and write to Topic B wrapped inside a single Transaction.
# If the consumer crashes before committing the transaction, the offset in Topic A is not moved, 
# and the message in Topic B is aborted (hidden from downstream consumers).

producer = Producer({
    'bootstrap.servers': 'localhost:9092',
    'transactional.id': 'my-transactional-app-1' # REQUIRED for exactly-once
})

consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'processor-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False # REQUIRED: We will commit offsets manually inside the transaction
})

# Initialize the producer's transactional state
producer.init_transactions()
consumer.subscribe(['input-topic'])

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None: continue
        if msg.error(): continue

        print(f"Processing message: {msg.value().decode('utf-8')}")

        # 1. Start the transaction
        producer.begin_transaction()

        try:
            # 2. Process data and write to output topic
            processed_data = msg.value().decode('utf-8').upper()
            producer.produce('output-topic', value=processed_data.encode('utf-8'))

            # 3. Send the consumer's offset to the transaction
            # This is the magic: The message write AND the offset commit are saved atomically.
            offsets = consumer.assignment()
            for tp in offsets:
                if tp.topic == msg.topic() and tp.partition == msg.partition():
                    tp.offset = msg.offset() + 1
            
            # Use the consumer's group metadata to commit the offset safely inside the transaction
            producer.send_offsets_to_transaction(offsets, consumer.consumer_group_metadata())
            
            # 4. Commit the transaction (makes output visible and moves consumer offset permanently)
            producer.commit_transaction()
            print("Transaction committed successfully.")

        except Exception as e:
            # If ANYTHING fails, abort the transaction. 
            # The downstream consumers won't see the output message, and the input offset won't move.
            print(f"Error processing. Aborting transaction: {e}")
            producer.abort_transaction()

except KeyboardInterrupt:
    pass
finally:
    consumer.close()
