# from kafka import KafkaConsumer
# import models_pb2

class MockUser:
    def ParseFromString(self, data):
        self.id = 1

def consume_events():
    print("Connecting to Kafka to consume Protobuf events...")
    # consumer = KafkaConsumer('user_events', bootstrap_servers='localhost:9092')
    # for msg in consumer:
    #     user_event = models_pb2.User()
    #     user_event.ParseFromString(msg.value)
    #     print(f"Processed Event for User: {user_event.id}")
    
    # Mocking
    user_event = MockUser()
    user_event.ParseFromString(b"")
    print(f"Processed Event for User: {user_event.id}")

if __name__ == "__main__":
    consume_events()
