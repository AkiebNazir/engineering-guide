# REAL-WORLD EXAMPLE: websockets (External 2)
# Demonstrates: Asyncio Event loops, Set-based connection tracking, Pub/Sub architecture
import asyncio
import websockets
import json

# Thread-safe set of connected clients
CONNECTED_CLIENTS = set()

async def handler(websocket, path):
    # 1. Register Client
    CONNECTED_CLIENTS.add(websocket)
    try:
        # 2. Listen to Client
        async for message in websocket:
            data = json.loads(message)
            
            # 3. Broadcast to all OTHER clients
            websockets.broadcast(
                (c for c in CONNECTED_CLIENTS if c != websocket),
                json.dumps({"type": "broadcast", "data": data})
            )
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # 4. Unregister Client
        CONNECTED_CLIENTS.remove(websocket)

async def main():
    print("WebSocket Server running on ws://localhost:8080")
    async with websockets.serve(handler, "localhost", 8080):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
