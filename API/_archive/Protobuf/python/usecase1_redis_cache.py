import redis
# import models_pb2

class MockUser:
    def __init__(self):
        self.name = ""
        self.email = ""
    def ParseFromString(self, data):
        self.name = "Alice"
        self.email = "alice@example.com"

def read_from_cache():
    # r = redis.Redis(host='localhost', port=6379, db=0)
    # binary_data = r.get("user:1")
    binary_data = b"mock binary data"
    
    if binary_data:
        # user = models_pb2.User()
        user = MockUser()
        user.ParseFromString(binary_data)
        print(f"Loaded from cache: {user.name} ({user.email})")

if __name__ == "__main__":
    read_from_cache()
