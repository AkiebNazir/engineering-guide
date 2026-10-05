import asyncio

class MockPlayerState:
    def __init__(self, x, y):
        self.x = x
        self.y = y

async def generate_player_movements():
    for x in range(5):
        yield MockPlayerState(float(x), 10.0)
        await asyncio.sleep(0.2)

async def sync_game():
    print("Starting Bidirectional Sync...")
    # async with grpc.aio.insecure_channel('localhost:50051') as channel:
    #     stub = api_pb2_grpc.MicroserviceSystemStub(channel)
    #     async for global_state in stub.GameSync(generate_player_movements()):
    
    async for move in generate_player_movements():
        print(f"Sent move X:{move.x}. Received game state update.")

if __name__ == '__main__':
    asyncio.run(sync_game())
