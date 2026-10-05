import asyncio
import websockets
import json
import random

async def sync_cursor():
    uri = "ws://localhost:8080/sync"
    try:
        async with websockets.connect(uri) as websocket:
            for _ in range(100):
                payload = json.dumps({
                    "userId": "usr_99",
                    "x": random.uniform(0, 1920),
                    "y": random.uniform(0, 1080)
                })
                
                await websocket.send(payload)
                await asyncio.sleep(0.016) # ~60fps
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ensure server is running on :8080 before executing client
    print("Run `go run usecase3_cursor_sync.go` in another terminal first.")
    # asyncio.run(sync_cursor())
