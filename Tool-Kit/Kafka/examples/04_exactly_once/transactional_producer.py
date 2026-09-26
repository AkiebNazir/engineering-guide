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
