import os
# import models_pb2

class MockUser:
    def __init__(self):
        self.name = "Alice"
    def ParseFromString(self, data):
        pass

def read_from_file():
    if not os.path.exists("users.bin"):
        print("users.bin not found. Writing dummy file.")
        with open("users.bin", "wb") as f:
            f.write(b"mock binary data")

    with open("users.bin", "rb") as f:
        data = f.read()
        # user = models_pb2.User()
        user = MockUser()
        user.ParseFromString(data)
        print(f"Read user from binary file: {user.name}")

if __name__ == "__main__":
    read_from_file()
