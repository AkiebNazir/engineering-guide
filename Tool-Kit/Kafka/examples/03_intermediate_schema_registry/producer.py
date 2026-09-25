from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

# 1. Connect to Schema Registry
schema_registry_conf = {'url': 'http://localhost:8081'}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# 2. Load the Avro Schema
with open('user_schema.avsc', 'r') as f:
    schema_str = f.read()

avro_serializer = AvroSerializer(schema_registry_client, schema_str)

# 3. Configure the Producer to serialize values using Avro
producer_conf = {
    'bootstrap.servers': 'localhost:9092',
    'value.serializer': avro_serializer
}
producer = SerializingProducer(producer_conf)

# 4. Produce a valid record
user_data = {"name": "Alice", "favorite_number": 42, "favorite_color": "blue"}

print("Producing user record to Kafka...")
producer.produce(topic='avro-users', key=str(1), value=user_data)
producer.flush()
print("Success! Schema Registry validated and serialized the event.")
