import asyncio
import websockets

async def resilient_client():
    uri = "ws://localhost:8080/health"
    
    try:
        # ping_interval handles heartbeats under the hood
        async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as ws:
            print("Connected with resilient health checks active.")
            while True:
                message = await ws.recv()
                print(f"Received: {message}")
    except websockets.exceptions.ConnectionClosedError:
        print("Connection dropped. Initiate exponential backoff reconnection...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Run `go run usecase4_health_check.go` in another terminal first.")
    # asyncio.run(resilient_client())
