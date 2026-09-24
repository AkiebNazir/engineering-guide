# REAL-WORLD EXAMPLE: grpclib (External 2)
# Demonstrates: Pure Asyncio implementation, Server Streaming
import asyncio
from grpclib.server import Server

# Mock generated code imports
# from user_grpc import UserServiceBase
# from user_pb2 import GetUserResponse, User

class MockStream:
    async def recv_message(self):
        class Req: id = "1"
        return Req()
    async def send_message(self, msg):
        print(f"Sending async message: {msg}")

class UserService: # Inherits from UserServiceBase
    async def GetUser(self, stream):
        # 1. Receive Request Async
        request = await stream.recv_message()
        
        # 2. Database call would go here (e.g., asyncpg / Motor)
        await asyncio.sleep(0.1) 
        
        # 3. Send Response Async
        await stream.send_message({"user": {"name": "Alice"}})

async def main():
    server = Server([UserService()])
    print("Async gRPC server starting on 127.0.0.1:50051")
    await server.start("127.0.0.1", 50051)
    await server.wait_closed()

if __name__ == "__main__":
    # asyncio.run(main())
    print("Run inside an asyncio event loop")
