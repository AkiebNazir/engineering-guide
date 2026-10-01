import socket
# import models_pb2

class MockUser:
    def __init__(self):
        self.name = ""
    def ParseFromString(self, data):
        self.name = "UDP User"

def listen_udp():
    print("Listening for Protobuf packets on UDP 8080...")
    # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # sock.bind(("127.0.0.1", 8080))
    # while True:
    #     data, addr = sock.recvfrom(1024)
    #     user = models_pb2.User()
    #     user.ParseFromString(data)
    #     print(f"UDP Packet received from {addr}: {user.name}")

if __name__ == "__main__":
    pass
