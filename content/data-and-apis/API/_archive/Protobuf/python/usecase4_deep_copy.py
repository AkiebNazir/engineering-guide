# import models_pb2

class MockUser:
    def __init__(self, id, name):
        self.id = id
        self.name = name
    def SerializeToString(self):
        return b"mock"
    def ParseFromString(self, data):
        self.id = 1
        self.name = "Alice"

def clone_user(original) -> MockUser:
    # cloned = models_pb2.User()
    cloned = MockUser(0, "")
    cloned.ParseFromString(original.SerializeToString())
    return cloned

if __name__ == "__main__":
    user = MockUser(1, "Alice")
    cloned = clone_user(user)
    print(f"Original ID: {id(user)}, Cloned ID: {id(cloned)}")
